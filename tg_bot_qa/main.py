import asyncio
import json
import logging
import os
import time
from pathlib import Path

import aiohttp
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import BaseFilter, Command
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).with_name(".env"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("tg_bot_qa")

API_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_OWNER = os.getenv("REPO_OWNER")
REPO_NAME = os.getenv("REPO_NAME")
WORKFLOW_ID = os.getenv("WORKFLOW_ID", "tests.yml")
WORKFLOW_REF = os.getenv("WORKFLOW_REF", "main")
DISPATCH_COOLDOWN_SEC = int(os.getenv("DISPATCH_COOLDOWN_SEC", "30"))

_raw_allowed = os.getenv("ALLOWED_USER_IDS", "").strip()
ALLOWED_USER_IDS: set[int] = {
    int(uid.strip()) for uid in _raw_allowed.split(",") if uid.strip().isdigit()
}

required_vars = {
    "TELEGRAM_BOT_TOKEN": API_TOKEN,
    "GITHUB_TOKEN": GITHUB_TOKEN,
    "REPO_OWNER": REPO_OWNER,
    "REPO_NAME": REPO_NAME,
}
missing_vars = [name for name, value in required_vars.items() if not value]
if missing_vars:
    raise RuntimeError(f"Missing required environment variables: {', '.join(missing_vars)}")

if not ALLOWED_USER_IDS:
    logger.warning(
        "ALLOWED_USER_IDS is empty — anyone who finds the bot can trigger workflows. "
        "Set ALLOWED_USER_IDS to a comma-separated list of Telegram user IDs."
    )

GITHUB_API = "https://api.github.com"
GITHUB_HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}
HTTP_TIMEOUT = aiohttp.ClientTimeout(total=30)

BTN_SMOKE = "🚀 Smoke-тесты"
BTN_DSZN = "📋 DSZN 136200"
BTN_STATUS = "📊 Статус"
BTN_HELP = "❓ Помощь"

# Per-chat cooldown to avoid spam-dispatching workflows
_last_dispatch_at: dict[int, float] = {}

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=BTN_SMOKE)],
        [KeyboardButton(text=BTN_DSZN)],
        [KeyboardButton(text=BTN_STATUS), KeyboardButton(text=BTN_HELP)],
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите действие",
)

HELP_TEXT = (
    "Я запускаю автотесты через GitHub Actions.\n\n"
    f"<b>{BTN_SMOKE}</b> / <code>/run_smoke_tests</code> — полный smoke-прогон\n"
    f"<b>{BTN_DSZN}</b> / <code>/run_dszn_136200_test</code> — тест Forms/dszn136200.py\n"
    f"<b>{BTN_STATUS}</b> / <code>/check_status</code> — последние запуски workflow\n"
    f"<b>{BTN_HELP}</b> / <code>/help</code> — эта справка\n\n"
    f"Репозиторий: <code>{REPO_OWNER}/{REPO_NAME}</code>\n"
    f"Workflow: <code>{WORKFLOW_ID}</code> · ветка: <code>{WORKFLOW_REF}</code>\n"
    f"Пауза между запусками: {DISPATCH_COOLDOWN_SEC} сек."
)

STATUS_EMOJI = {
    "queued": "⏳",
    "in_progress": "🔄",
    "completed": "✅",
    "waiting": "⏸",
    "requested": "📩",
    "pending": "⏳",
}
CONCLUSION_EMOJI = {
    "success": "✅",
    "failure": "❌",
    "cancelled": "🚫",
    "skipped": "⏭",
    "timed_out": "⏰",
    "action_required": "⚠",
    "neutral": "⚪",
    "stale": "🕸",
}


class AllowedUsers(BaseFilter):
    async def __call__(self, message: types.Message) -> bool:
        if not ALLOWED_USER_IDS:
            return True
        user_id = message.from_user.id if message.from_user else None
        if user_id in ALLOWED_USER_IDS:
            return True
        logger.warning("Denied access for user_id=%s chat_id=%s", user_id, message.chat.id)
        await message.answer("⛔ Нет доступа. Обратитесь к администратору бота.")
        return False


dp.message.filter(AllowedUsers())


def _truncate(text: str, limit: int = 400) -> str:
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


async def github_request(
    method: str,
    path: str,
    *,
    json_body: dict | None = None,
) -> tuple[int, str | dict | list | None]:
    url = f"{GITHUB_API}{path}"
    async with aiohttp.ClientSession(timeout=HTTP_TIMEOUT) as session:
        async with session.request(
            method,
            url,
            headers=GITHUB_HEADERS,
            json=json_body,
        ) as response:
            body_text = await response.text()
            if not body_text:
                return response.status, None
            try:
                return response.status, json.loads(body_text)
            except json.JSONDecodeError:
                return response.status, body_text


async def dispatch_workflow(inputs: dict | None = None) -> tuple[bool, str]:
    path = f"/repos/{REPO_OWNER}/{REPO_NAME}/actions/workflows/{WORKFLOW_ID}/dispatches"
    data: dict = {"ref": WORKFLOW_REF}
    if inputs:
        data["inputs"] = inputs

    try:
        status, body = await github_request("POST", path, json_body=data)
    except asyncio.TimeoutError:
        return False, "Таймаут запроса к GitHub API."
    except aiohttp.ClientError as exc:
        logger.exception("GitHub dispatch failed")
        return False, f"Сеть: {exc.__class__.__name__}"

    if status == 204:
        return True, "Пайплайн принят GitHub Actions."

    detail = body if isinstance(body, str) else str(body)
    logger.error("Dispatch failed status=%s body=%s", status, detail)
    return False, f"HTTP {status}: {_truncate(detail)}"


async def fetch_recent_runs(limit: int = 5) -> tuple[bool, str]:
    path = (
        f"/repos/{REPO_OWNER}/{REPO_NAME}/actions/workflows/{WORKFLOW_ID}/runs"
        f"?per_page={limit}"
    )
    try:
        status, body = await github_request("GET", path)
    except asyncio.TimeoutError:
        return False, "Таймаут запроса к GitHub API."
    except aiohttp.ClientError as exc:
        logger.exception("GitHub status fetch failed")
        return False, f"Сеть: {exc.__class__.__name__}"

    if status != 200 or not isinstance(body, dict):
        detail = body if isinstance(body, str) else str(body)
        return False, f"HTTP {status}: {_truncate(detail)}"

    runs = body.get("workflow_runs") or []
    if not runs:
        return True, "Пока нет запусков этого workflow."

    lines = [f"<b>Последние запуски</b> (<code>{WORKFLOW_ID}</code>):\n"]
    for run in runs:
        status_name = run.get("status") or "?"
        conclusion = run.get("conclusion")
        if status_name == "completed" and conclusion:
            icon = CONCLUSION_EMOJI.get(conclusion, "•")
            state = conclusion
        else:
            icon = STATUS_EMOJI.get(status_name, "•")
            state = status_name

        title = run.get("display_title") or run.get("name") or f"#{run.get('run_number')}"
        html_url = run.get("html_url") or ""
        created = (run.get("created_at") or "")[:19].replace("T", " ")
        actor = (run.get("actor") or {}).get("login") or "?"
        line = f'{icon} <a href="{html_url}">{title}</a>\n   {state} · {created} UTC · {actor}'
        lines.append(line)

    return True, "\n".join(lines)


def cooldown_remaining(chat_id: int) -> int:
    last = _last_dispatch_at.get(chat_id, 0)
    left = DISPATCH_COOLDOWN_SEC - (time.monotonic() - last)
    return max(0, int(left))


def mark_dispatched(chat_id: int) -> None:
    _last_dispatch_at[chat_id] = time.monotonic()


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Я бот для управления автотестами.\nВыбери действие на клавиатуре или /help.",
        reply_markup=keyboard,
    )


@dp.message(Command("help"))
@dp.message(F.text == BTN_HELP)
async def cmd_help(message: types.Message):
    await message.answer(HELP_TEXT, reply_markup=keyboard, parse_mode="HTML")


@dp.message(Command("run_smoke_tests"))
@dp.message(F.text == BTN_SMOKE)
async def run_smoke_tests(message: types.Message):
    remaining = cooldown_remaining(message.chat.id)
    if remaining:
        await message.answer(f"⏳ Подождите ещё {remaining} сек. перед новым запуском.")
        return

    await message.answer("🚀 Запускаю smoke-тесты…")
    ok, detail = await dispatch_workflow()
    if ok:
        mark_dispatched(message.chat.id)
        logger.info(
            "Smoke dispatched by user_id=%s",
            message.from_user.id if message.from_user else None,
        )
        await message.answer(
            f"✅ {detail}\nЧерез минуту можно проверить /check_status.",
            reply_markup=keyboard,
        )
    else:
        await message.answer(f"❌ Не удалось запустить:\n{detail}", reply_markup=keyboard)


@dp.message(Command("run_dszn_136200_test", "run_dszn"))
@dp.message(F.text == BTN_DSZN)
async def run_dszn_test(message: types.Message):
    remaining = cooldown_remaining(message.chat.id)
    if remaining:
        await message.answer(f"⏳ Подождите ещё {remaining} сек. перед новым запуском.")
        return

    await message.answer("🚀 Запускаю тест: Forms/dszn136200.py …")
    ok, detail = await dispatch_workflow(inputs={"test_file": "Forms/dszn136200.py"})
    if ok:
        mark_dispatched(message.chat.id)
        logger.info(
            "DSZN dispatched by user_id=%s",
            message.from_user.id if message.from_user else None,
        )
        await message.answer(
            f"✅ {detail}\nЧерез минуту можно проверить /check_status.",
            reply_markup=keyboard,
        )
    else:
        await message.answer(f"❌ Не удалось запустить:\n{detail}", reply_markup=keyboard)


@dp.message(Command("check_status"))
@dp.message(F.text == BTN_STATUS)
async def check_status(message: types.Message):
    await message.answer("📡 Смотрю последние запуски…")
    ok, text = await fetch_recent_runs()
    if ok:
        await message.answer(
            text,
            reply_markup=keyboard,
            parse_mode="HTML",
            disable_web_page_preview=True,
        )
    else:
        await message.answer(f"❌ Не удалось получить статус:\n{text}", reply_markup=keyboard)


@dp.message()
async def fallback(message: types.Message):
    await message.answer(
        "Не понял команду. Нажмите кнопку на клавиатуре или /help.",
        reply_markup=keyboard,
    )


async def main():
    logger.info(
        "Starting bot for %s/%s workflow=%s ref=%s",
        REPO_OWNER,
        REPO_NAME,
        WORKFLOW_ID,
        WORKFLOW_REF,
    )
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())

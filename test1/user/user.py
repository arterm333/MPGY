import os

# `python-dotenv` предоставляет модуль `dotenv`, но в некоторых конфигурациях
# анализатор Cursor/basedpyright может не успевать подтянуть пакет из venv.
from dotenv import load_dotenv, find_dotenv  # pyright: ignore[reportMissingImports]

load_dotenv(find_dotenv())


def user_fl(route, request):
    """Данные для авторизации под ФЛ"""
    headers = {
        **request.headers,
        'iv-user': os.getenv('USER_FL_ID'),
        'iv-persontype': '1',
        'iv-sudir': os.getenv('USER_SUDIR_ID')
    }
    route.continue_(headers=headers)


def ip(route, request):
    """Данные для авторизации под ИП"""
    headers = {
        **request.headers,
        'iv-user': os.getenv('USER_IP_ID'),
        'iv-ogrn': os.getenv('USER_IP_OGRN'),
        'iv-corpid': os.getenv('USER_IP_CORPID'),
        'iv-persontype': '3'
    }
    route.continue_(headers=headers)


def ul(route, request):
    """Данные для авторизации под ЮЛ"""
    headers = {
        **request.headers,
        'iv-user': os.getenv('USER_UL_ID'),
        'iv-ogrn': os.getenv('USER_UL_OGRN'),
        'iv-corpid': os.getenv('USER_UL_CORPID'),
        'token2form': os.getenv('USER_UL_TOKEN2FORM'),
        'iv-persontype': '2'
    }
    route.continue_(headers=headers)

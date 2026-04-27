import{s as f,n as u}from"../isObjectLike-7962ce13.js";import{S as d,i as _,c as x,s as b,e as h,m as w,a,t as y,b as k,d as c,f as g,g as l}from"../IconBtn-94c9cb85.js";import{A as $}from"../App-65d1a1d0.js";import{I as A,i as C}from"../profile-hook-7bf735b0.js";import"../_commonjsHelpers-187a63f9.js";function F(i){let t;return{c(){t=l("style"),t.textContent=`body {
      height: 510px;
      /** Fix FF popup disappearance on long window. */
      width: 620px !important;
    }

    :root {
      --drawer-width: 36px;
      --app-content-width: calc(100% - 36px);
      --top-bar-width: calc(100% - 35px);
      --top-bar-height: 48px;
    }`},m(e,o){a(e,t,o)},d(e){e&&c(t)}}}function I(i){let t;return{c(){t=l("style"),t.textContent=`body {
      height: 100vh;
      width: 100% !important;
    }
    :root {
      --drawer-width: 36px;
      --app-content-width: calc(100% - 36px);
      --top-bar-width: calc(100% - 35px);
      --top-bar-height: 48px;
    }`},m(e,o){a(e,t,o)},d(e){e&&c(t)}}}function S(i){let t,e,o,p;t=new $({});function m(n,r){return A?I:F}let s=m()(i);return{c(){x(t.$$.fragment),e=b(),s.c(),o=h()},m(n,r){w(t,n,r),a(n,e,r),s.m(n,r),a(n,o,r),p=!0},p:u,i(n){p||(y(t.$$.fragment,n),p=!0)},o(n){k(t.$$.fragment,n),p=!1},d(n){n&&(c(e),c(o)),g(t,n),s.d(n)}}}class v extends d{constructor(t){super(),_(this,t,null,S,f,{})}}C();new v({target:document.body});

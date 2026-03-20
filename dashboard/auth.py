"""앱 접근 제어 — 비밀번호 인증 게이트"""
import hashlib
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from src.config import _get_secret


def _auth_token(pw: str) -> str:
    """비밀번호 기반 세션 토큰 생성 (URL 파라미터용)."""
    return hashlib.sha256(pw.encode()).hexdigest()[:16]


def require_auth():
    """비밀번호 인증이 안 된 상태면 로그인 화면을 표시하고 st.stop()."""
    if st.session_state.get("authenticated"):
        # 페이지 이동으로 ?t= 유실 시 복원 (rerun 1회 추가)
        app_pw = _get_secret("APP_PASSWORD")
        if app_pw:
            token = _auth_token(app_pw)
            if st.query_params.get("t") != token:
                st.query_params["t"] = token
        return

    app_pw = _get_secret("APP_PASSWORD")
    if not app_pw:
        return

    # 새로고침 시 URL 토큰으로 세션 복원
    token = _auth_token(app_pw)
    if st.query_params.get("t") == token:
        st.session_state["authenticated"] = True
        return

    st.markdown(
        '<div style="max-width:400px;margin:80px auto;text-align:center;">'
        '<h2 style="margin-bottom:8px;">YT 토픽 파인더</h2>'
        '<p style="color:#8B949E;margin-bottom:24px;">접근하려면 비밀번호를 입력하세요</p>'
        "</div>",
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            pwd = st.text_input(
                "비밀번호", type="password", key="_login_pw",
                label_visibility="collapsed", placeholder="비밀번호 입력",
            )
            submitted = st.form_submit_button("로그인", type="primary", use_container_width=True)

        if submitted and pwd:
            if pwd == app_pw:
                st.session_state["authenticated"] = True
                st.query_params["t"] = token
                st.rerun()
            else:
                st.error("비밀번호가 틀렸어요")
    st.stop()

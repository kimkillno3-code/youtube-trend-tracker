"""설정 페이지 — API 키 관리, 할당량 모니터링"""
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from src.config import YOUTUBE_API_KEY, YOUTUBE_DAILY_QUOTA, DB_PATH
from src.database.repository import TrendRepository
from dashboard.theme import (
    inject_custom_css, sidebar_with_badges,
    render_page_header, render_metric_card,
)

st.set_page_config(page_title="설정 - YT", layout="wide")

repo = TrendRepository(str(DB_PATH))
inject_custom_css()
sidebar_with_badges(repo)
render_page_header("설정", "API 키 관리 및 시스템 상태")


# ── API 키 상태 ──
st.markdown("#### YouTube API 키")

if YOUTUBE_API_KEY:
    # 마스킹 처리 (앞 4 + ... + 뒤 4)
    key_len = len(YOUTUBE_API_KEY)
    if key_len > 8:
        masked = YOUTUBE_API_KEY[:4] + "*" * (key_len - 8) + YOUTUBE_API_KEY[-4:]
    else:
        masked = "*" * key_len
    st.success(f"API 키가 등록되어 있어요: `{masked}`")
else:
    st.error(
        "YouTube API 키가 설정되지 않았어요.\n\n"
        "**설정 방법:**\n"
        "1. 프로젝트 루트에 `.env` 파일을 만들어주세요\n"
        "2. 아래 형식으로 API 키를 입력해주세요:\n"
        "```\nYOUTUBE_API_KEY=여기에_발급받은_키\n```\n"
        "3. [Google Cloud Console](https://console.cloud.google.com/apis/credentials)에서 "
        "API 키를 발급받을 수 있어요\n"
        "4. YouTube Data API v3이 활성화되어 있는지 확인해주세요\n\n"
        "설정 후 페이지를 새로고침하면 바로 사용할 수 있어요."
    )

st.markdown("---")


# ── API 할당량 사용률 ──
st.markdown("#### API 할당량 (일일)")

today_used = repo.get_today_quota_used()
daily_limit = YOUTUBE_DAILY_QUOTA
usage_pct = min(today_used / daily_limit * 100, 100) if daily_limit > 0 else 0
remaining = max(daily_limit - today_used, 0)

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(
        render_metric_card(
            f"{today_used:,}", "오늘 사용량", color="blue",
            hint=f"일일 한도: {daily_limit:,}",
        ),
        unsafe_allow_html=True,
    )
with col2:
    st.markdown(
        render_metric_card(
            f"{remaining:,}", "잔여 할당량", color="green" if remaining > 2000 else "red",
            hint="자정(태평양 시간) 초기화",
        ),
        unsafe_allow_html=True,
    )
with col3:
    st.markdown(
        render_metric_card(
            f"{usage_pct:.1f}%", "사용률",
            color="green" if usage_pct < 70 else ("amber" if usage_pct < 90 else "red"),
        ),
        unsafe_allow_html=True,
    )

# 프로그레스 바
st.progress(min(usage_pct / 100, 1.0))

if usage_pct >= 90:
    st.warning("할당량이 거의 소진되었어요. 내일 자정(태평양 시간) 이후에 초기화됩니다.")
elif usage_pct >= 70:
    st.info("할당량의 70%를 사용했어요. 남은 할당량을 확인하며 사용해주세요.")

st.caption(
    "**할당량 참고:** 실시간 트렌드 수집 ≈ 100유닛 | 주간 인기 수집 ≈ 200유닛 | "
    "키워드 검색 1회 ≈ 200유닛"
)

st.markdown("---")


# ── 최근 수집 기록 ──
st.markdown("#### 최근 수집 기록")

logs = repo.get_recent_logs(limit=10)
if logs:
    for log in logs:
        status = log.get("status", "unknown")
        icon = {"success": "✅", "failed": "❌", "running": "🔄"}.get(status, "⬜")
        run_type = log.get("run_type", "-")
        started = (log.get("run_started_at") or "")[:16].replace("T", " ")
        videos = log.get("videos_collected", 0)
        quota = log.get("quota_used", 0)
        error = log.get("error_message")

        with st.expander(f"{icon} {run_type} — {started}", expanded=False):
            c1, c2, c3 = st.columns(3)
            c1.metric("수집 영상", f"{videos}개")
            c2.metric("할당량 사용", f"{quota} 유닛")
            c3.metric("상태", status)
            if error:
                st.error(f"에러: {error}")
else:
    st.info("아직 수집 기록이 없어요.")

st.markdown("---")


# ── 성과 별점 기준 안내 ──
st.markdown("#### 성과 별점 기준")
st.markdown(
    "영상 카드의 별점은 **구독자 대비 조회수 비율**로 산출됩니다.\n\n"
    "| 별점 | 기준 (조회수 / 구독자) |\n"
    "|------|----------------------|\n"
    "| ⭐⭐⭐⭐⭐ | 50배 이상 |\n"
    "| ⭐⭐⭐⭐ | 10배 이상 |\n"
    "| ⭐⭐⭐ | 2배 이상 |\n"
    "| ⭐⭐ | 0.5배 이상 |\n"
    "| ⭐ | 그 외 |\n\n"
    "소규모 채널(구독자 5만 이하)이 높은 별점을 받으면 해당 키워드가 블루오션일 수 있어요."
)

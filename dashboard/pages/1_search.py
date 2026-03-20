"""키워드 검색 & 벤치마킹 페이지"""
import html as html_lib
import sys
import zipfile
from datetime import datetime
from io import BytesIO
from pathlib import Path

import pandas as pd
import requests
import streamlit as st

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from src.config import YOUTUBE_API_KEY, DB_PATH, DATA_DIR
from src.collector.youtube_api import YouTubeAPIClient
from src.collector.search import search_and_collect
from src.database.repository import TrendRepository
from src.analysis.tag_analyzer import analyze_tags
from src.analysis.insights import generate_insights
from src.utils import validate_thumbnail_url
from dashboard.theme import (
    inject_custom_css, sidebar_with_badges,
    render_page_header, render_metric_card,
    render_video_grid, render_empty_state,
    render_insight_box, render_filter_info,
    build_category_pills, filter_videos_by_category,
    inject_pills_highlight,
)

st.set_page_config(page_title="키워드 검색 - YT", layout="wide")

DATA_DIR.mkdir(parents=True, exist_ok=True)
repo = TrendRepository(str(DB_PATH))

inject_custom_css()
sidebar_with_badges(repo)

render_page_header("키워드 검색", "경쟁 영상을 검색하고 한눈에 분석해보세요")

# ── 검색 폼 (API 호출에 필요한 조건만) ──
with st.form("search_form"):
    keyword = st.text_input("검색어", placeholder="예: AI, 먹방, 브이로그")

    col_days, col_dur = st.columns(2)
    days = col_days.selectbox("기간", ["최근 1주일", "최근 1개월", "최근 3개월", "전체"], index=0)
    duration = col_dur.selectbox("영상 길이", ["전체", "4분 미만", "4~20분", "20분 이상"], index=0)

    submitted = st.form_submit_button("검색하기", type="primary", use_container_width=True)

DAYS_MAP = {"최근 1주일": 7, "최근 1개월": 30, "최근 3개월": 90, "전체": 0}
DURATION_MAP = {"전체": None, "4분 미만": "short", "4~20분": "medium", "20분 이상": "long"}

if submitted:
    if not keyword.strip():
        st.warning("검색어를 입력해주세요.")
    elif not YOUTUBE_API_KEY:
        st.error(
            "YouTube API 키가 설정되지 않았어요.\n\n"
            "1. [Google Cloud Console](https://console.cloud.google.com/)에서 API 키 발급\n"
            "2. 프로젝트 루트에 `.env` 파일 생성\n"
            "3. `YOUTUBE_API_KEY=발급받은키` 입력 후 저장"
        )
        st.stop()
    else:
        api = YouTubeAPIClient(YOUTUBE_API_KEY)
        collected_at = datetime.now().isoformat()
        log_id = repo.log_start("search")

        try:
            with st.spinner(f'"{keyword}" 관련 영상을 찾고 있어요...'):
                videos = search_and_collect(
                    api, keyword,
                    max_results=50,
                    order="viewCount",
                    days_ago=DAYS_MAP[days],
                    video_duration=DURATION_MAP[duration],
                )
                saved = repo.save_search_results(keyword, videos, collected_at)
                repo.log_end(log_id, "success", saved, api.quota_used)

            st.session_state["search_videos"] = videos
            st.session_state["search_keyword"] = keyword
            st.toast(f'"{keyword}" {len(videos)}개 영상을 찾았어요')
        except requests.exceptions.ConnectionError:
            repo.log_end(log_id, "failed", 0, 0, "network")
            st.error("네트워크 연결을 확인해주세요.")
        except Exception as e:
            err_msg = str(e).lower()
            if "quota" in err_msg or "rateLimitExceeded" in str(e):
                repo.log_end(log_id, "failed", 0, 0, "quota")
                st.error("YouTube API 일일 할당량을 초과했어요. 내일 다시 시도해주세요.")
            elif "forbidden" in err_msg or "403" in err_msg:
                repo.log_end(log_id, "failed", 0, 0, "forbidden")
                st.error("API 키 권한이 부족해요. YouTube Data API v3이 활성화됐는지 확인해주세요.")
            else:
                repo.log_end(log_id, "failed", 0, 0, str(e))
                st.error("검색 중 문제가 발생했어요. 잠시 후 다시 시도해주세요.")

# ── 결과 로드 ──
all_videos = st.session_state.get("search_videos", [])
keyword = st.session_state.get("search_keyword", "")

if not all_videos:
    if keyword:
        all_videos = repo.get_search_results(keyword)
        if all_videos:
            st.info(f'이전에 검색한 "{keyword}" 결과를 보여드릴게요')

if not all_videos:
    render_empty_state(
        "검색 결과가 없어요",
        "키워드를 입력하면 경쟁 영상을 한눈에 분석할 수 있어요",
    )
    st.stop()

st.caption(f"상위 {len(all_videos)}개 결과를 분석했어요")

# ── 핵심 지표 — 바로 노출 ──
insights = generate_insights(all_videos)

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.markdown(render_metric_card(
        insights["avg_views"], "평균 조회수", "blue",
        hint="검색된 영상 기준",
    ), unsafe_allow_html=True)
with m2:
    st.markdown(render_metric_card(
        insights["max_views"], "최고 조회수", "red",
    ), unsafe_allow_html=True)
with m3:
    st.markdown(render_metric_card(
        f'{insights["avg_duration_min"]}분', "평균 영상 길이", "green",
    ), unsafe_allow_html=True)
with m4:
    st.markdown(render_metric_card(
        f'{insights["small_channel_hits"]}개', "소채널 성과", "amber",
        hint="구독자 5만 이하 채널",
    ), unsafe_allow_html=True)

# ── 인사이트 박스 ──
tag_freq = analyze_tags(all_videos)

if insights.get("category_distribution"):
    cats = insights["category_distribution"]
    top_tags = [t[0] for t in tag_freq[:5]] if tag_freq else []
    cat_name = html_lib.escape(cats[0][0])
    tags_text = html_lib.escape(", ".join(top_tags))
    render_insight_box(
        f"<strong>인기 카테고리:</strong> {cat_name} ({cats[0][1]}개) &nbsp;&middot;&nbsp; "
        f"<strong>많이 쓰인 태그:</strong> {tags_text} &nbsp;&middot;&nbsp; "
        f"<strong>소채널 성과:</strong> 구독자 5만 이하 채널에서 {insights['small_channel_hits']}개 영상이 높은 조회수를 기록했어요"
    )

# ── 정렬 + 카테고리 필터 + 다운로드 ──
SORT_OPTIONS = ["조회수순", "최신순", "관련도순"]
sort_order = st.selectbox("정렬", SORT_OPTIONS, index=0, key="search_sort")
if sort_order == "조회수순":
    all_videos = sorted(all_videos, key=lambda v: v.get("view_count", 0), reverse=True)
elif sort_order == "최신순":
    all_videos = sorted(all_videos, key=lambda v: v.get("published_at", ""), reverse=True)

videos = all_videos
labels, cat_map = build_category_pills(all_videos)

col_filter, col_dl = st.columns([8, 2])
with col_filter:
    if labels:
        btn_cols = st.columns([2, 2, 6])
        with btn_cols[0]:
            if st.button("전체선택", key="search_cat_all", use_container_width=True):
                st.session_state["search_cat_filter"] = labels
        with btn_cols[1]:
            if st.button("선택해제", key="search_cat_clear", use_container_width=True):
                st.session_state["search_cat_filter"] = []

        selected_cats = st.pills(
            "카테고리 필터", labels,
            selection_mode="multi", key="search_cat_filter",
        )
        inject_pills_highlight(selected_cats, group_index=0)
        if selected_cats:
            videos = filter_videos_by_category(all_videos, selected_cats, cat_map)
            render_filter_info(len(videos), len(all_videos))
with col_dl:
    df = pd.DataFrame(videos)
    if not df.empty:
        excel_buffer = BytesIO()
        export_cols = ["search_rank", "title", "channel_title", "view_count",
                       "like_count", "subscriber_count", "performance_stars",
                       "category_name", "tags", "video_id", "published_at"]
        available_cols = [c for c in export_cols if c in df.columns]
        df[available_cols].to_excel(excel_buffer, index=False, engine="openpyxl")
        st.download_button(
            "엑셀 다운로드",
            data=excel_buffer.getvalue(),
            file_name=f"youtube_search_{keyword}_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
        if st.button("썸네일 모아받기", use_container_width=True):
            with st.spinner("썸네일을 모아서 준비하고 있어요..."):
                zip_buffer = BytesIO()
                downloaded = 0
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                    for v in videos:
                        thumb_url = validate_thumbnail_url(v.get("thumbnail_url", ""))
                        if not thumb_url:
                            continue
                        try:
                            resp = requests.get(thumb_url, timeout=5)
                            if resp.status_code == 200:
                                rank = v.get("search_rank", downloaded + 1)
                                vid = v.get("video_id", "unknown")
                                zf.writestr(f"{rank:02d}_{vid}.jpg", resp.content)
                                downloaded += 1
                        except requests.RequestException:
                            continue

                if downloaded > 0:
                    st.session_state["thumb_zip"] = zip_buffer.getvalue()
                    st.session_state["thumb_count"] = downloaded
                    st.toast(f"{downloaded}개 썸네일을 모아받았어요")
                else:
                    st.warning("다운로드할 썸네일이 없어요")

    if st.session_state.get("thumb_zip"):
        st.download_button(
            f"썸네일 저장 ({st.session_state.get('thumb_count', 0)}개)",
            data=st.session_state["thumb_zip"],
            file_name=f"thumbnails_{keyword}_{datetime.now().strftime('%Y%m%d')}.zip",
            mime="application/zip",
            use_container_width=True,
        )

# ── 영상 그리드 ──
render_video_grid(videos, rank_field="search_rank", cols=3)

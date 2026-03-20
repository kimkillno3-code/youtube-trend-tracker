"""YouTube 토픽 파인더 — 트렌드 대시보드"""
import sys
from datetime import datetime, timezone, timedelta
from io import BytesIO
from pathlib import Path

KST = timezone(timedelta(hours=9))

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from src.config import YOUTUBE_API_KEY, DB_PATH, DATA_DIR
from src.collector.youtube_api import YouTubeAPIClient
from src.collector.trending import collect_trending, save_snapshots
from src.database.repository import TrendRepository
from src.analysis.insights import generate_insights
from dashboard.theme import (
    inject_custom_css, sidebar_with_badges, get_plotly_layout,
    render_page_header, render_metric_card,
    render_section_title, render_video_grid,
    render_empty_state, render_insight_box,
    render_filter_info, build_category_pills, filter_videos_by_category,
    inject_pills_highlight,
)

st.set_page_config(page_title="YT 토픽 파인더", layout="wide")

DATA_DIR.mkdir(parents=True, exist_ok=True)
repo = TrendRepository(str(DB_PATH))

inject_custom_css()
sidebar_with_badges(repo, current_page="dashboard")

try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=300000, limit=None, key="cmd_center_refresh")
except ImportError:
    pass


# ── 수집 함수 ──
def _handle_api_error(e: Exception, log_id: int, quota: int):
    """API 에러 유형별 분기 처리"""
    err_msg = str(e).lower()
    if "quota" in err_msg or "ratelimitexceeded" in err_msg:
        repo.log_end(log_id, "failed", 0, quota, "quota")
        st.error("YouTube API 일일 할당량을 초과했어요. 내일 다시 시도해주세요.")
    elif "forbidden" in err_msg or "403" in err_msg:
        repo.log_end(log_id, "failed", 0, quota, "forbidden")
        st.error("API 키 권한이 부족해요. YouTube Data API v3이 활성화됐는지 확인해주세요.")
    elif "connectionerror" in err_msg or "timeout" in err_msg:
        repo.log_end(log_id, "failed", 0, quota, "network")
        st.error("네트워크 연결을 확인해주세요.")
    else:
        repo.log_end(log_id, "failed", 0, quota, str(e))
        st.error("수집 중 문제가 발생했어요. 잠시 후 다시 시도해주세요.")


def do_realtime_collect():
    if not YOUTUBE_API_KEY:
        st.error(
            "YouTube API 키가 설정되지 않았어요.\n\n"
            "1. [Google Cloud Console](https://console.cloud.google.com/)에서 API 키 발급\n"
            "2. 프로젝트 루트에 `.env` 파일 생성\n"
            "3. `YOUTUBE_API_KEY=발급받은키` 입력 후 저장"
        )
        return
    api = YouTubeAPIClient(YOUTUBE_API_KEY)
    collected_at = datetime.now(KST).isoformat()
    log_id = repo.log_start("realtime")
    try:
        with st.spinner("실시간 인기 영상을 가져오고 있어요..."):
            videos = collect_trending(api, max_results=30)
            saved = repo.save_trending_videos(videos, collected_at, source_type="realtime")
            save_snapshots(repo, videos)
            repo.log_end(log_id, "success", saved, api.quota_used)
        if saved > 0:
            st.toast(f"실시간 인기 영상 {saved}개를 가져왔어요")
        else:
            st.toast("이미 수집된 영상이에요. 새로운 영상이 없어요")
    except Exception as e:
        _handle_api_error(e, log_id, api.quota_used)


def do_weekly_trend():
    if not YOUTUBE_API_KEY:
        st.error(
            "YouTube API 키가 설정되지 않았어요.\n\n"
            "1. [Google Cloud Console](https://console.cloud.google.com/)에서 API 키 발급\n"
            "2. 프로젝트 루트에 `.env` 파일 생성\n"
            "3. `YOUTUBE_API_KEY=발급받은키` 입력 후 저장"
        )
        return
    api = YouTubeAPIClient(YOUTUBE_API_KEY)
    collected_at = datetime.now(KST).isoformat()
    log_id = repo.log_start("weekly_trend")
    try:
        with st.spinner("주간 인기 영상을 분석하고 있어요..."):
            videos = collect_trending(api, max_results=50)
            # 조회수 기준 내림차순 정렬 후 순위 재부여
            videos.sort(key=lambda v: v.get("view_count", 0), reverse=True)
            for rank, v in enumerate(videos[:30], 1):
                v["trending_rank"] = rank
            videos = videos[:30]
            saved = repo.save_trending_videos(videos, collected_at, source_type="weekly")
            save_snapshots(repo, videos)
            repo.log_end(log_id, "success", saved, api.quota_used)
        if saved > 0:
            st.toast(f"주간 인기 영상 {saved}개를 분석했어요")
        else:
            st.toast("이미 수집된 영상이에요. 새로운 영상이 없어요")
    except Exception as e:
        _handle_api_error(e, log_id, api.quota_used)


# ── 탭별 영상 목록 렌더링 (공통) ──
def render_tab_content(videos, source_label, cat_key, rank_field="trending_rank", pills_group=0):
    """탭 내부: 지표 → 카테고리 필터 → 영상 그리드"""
    if not videos:
        render_empty_state(
            f"{source_label} 데이터가 없어요",
            "수집 버튼을 눌러 영상을 가져와보세요",
        )
        return

    insights = generate_insights(videos)

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(render_metric_card(
            f"{insights['total_videos']}개", "수집된 영상", "blue",
        ), unsafe_allow_html=True)
    with m2:
        st.markdown(render_metric_card(
            insights["avg_views"], "평균 조회수", "green",
        ), unsafe_allow_html=True)
    with m3:
        st.markdown(render_metric_card(
            insights["max_views"], "최고 조회수", "red",
        ), unsafe_allow_html=True)
    with m4:
        top_cat = insights["top_category"][0] if insights.get("top_category") else "없음"
        st.markdown(render_metric_card(
            top_cat, "인기 카테고리", "purple",
        ), unsafe_allow_html=True)

    filtered = videos
    labels, cat_map = build_category_pills(videos)

    col_filter, col_dl = st.columns([8, 2])
    with col_filter:
        if labels:
            btn_cols = st.columns([2, 2, 6])
            with btn_cols[0]:
                if st.button("전체선택", key=f"{cat_key}_all", use_container_width=True):
                    st.session_state[cat_key] = labels
            with btn_cols[1]:
                if st.button("선택해제", key=f"{cat_key}_clear", use_container_width=True):
                    st.session_state[cat_key] = []

            selected = st.pills(
                "카테고리 필터", labels,
                selection_mode="multi", key=cat_key,
            )
            inject_pills_highlight(selected, group_index=pills_group)
            if selected:
                filtered = filter_videos_by_category(videos, selected, cat_map)
                render_filter_info(len(filtered), len(videos))
    with col_dl:
        df = pd.DataFrame(filtered)
        if not df.empty:
            excel_buffer = BytesIO()
            export_cols = ["trending_rank", "title", "channel_title", "view_count",
                           "like_count", "subscriber_count", "performance_stars",
                           "category_name", "published_at", "tags", "video_id"]
            available_cols = [c for c in export_cols if c in df.columns]
            df[available_cols].to_excel(excel_buffer, index=False, engine="openpyxl")
            st.download_button(
                "엑셀 다운로드",
                data=excel_buffer.getvalue(),
                file_name=f"youtube_{source_label}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

    render_video_grid(filtered, rank_field=rank_field, cols=3)


# ══════════════════════════════════════
# 트렌드 대시보드
# ══════════════════════════════════════

last_time = repo.get_last_collection_time()
if last_time:
    try:
        _utc = datetime.fromisoformat(last_time.replace("Z", "+00:00"))
        _kst = _utc.astimezone(KST)
        subtitle = f"마지막 수집: {_kst.strftime('%Y-%m-%d %H:%M')}"
    except Exception:
        subtitle = f"마지막 수집: {last_time[:16].replace('T', ' ')}"
else:
    subtitle = "첫 트렌드 분석을 시작해보세요"
render_page_header("트렌드 대시보드", subtitle)

# ── 탭 ──
tab_realtime, tab_weekly, tab_analysis = st.tabs(["실시간 트렌드", "주간 인기", "분석 리포트"])

with tab_realtime:
    if st.button("실시간 인기 영상 가져오기", type="primary", use_container_width=False):
        do_realtime_collect()
    realtime_videos = repo.get_latest_by_source("realtime", limit=30)
    render_tab_content(realtime_videos, "실시간", "realtime_cat_filter", pills_group=0)

with tab_weekly:
    col_btn, col_toggle = st.columns([3, 7])
    with col_btn:
        if st.button("주간 인기 영상 분석", type="primary", use_container_width=False):
            do_weekly_trend()
    st.caption("현재 인기 급상승 영상 50개를 조회수 기준으로 정렬하여 TOP 30을 보여줍니다.")
    weekly_videos = repo.get_latest_by_source("weekly", limit=30)
    if weekly_videos and realtime_videos:
        realtime_ids = {v["video_id"] for v in realtime_videos}
        overlap_count = sum(1 for v in weekly_videos if v["video_id"] in realtime_ids)
        if overlap_count > 0:
            with col_toggle:
                hide_dup = st.toggle(
                    f"실시간 중복 제외 ({overlap_count}개)",
                    key="hide_weekly_dup",
                )
                if hide_dup:
                    weekly_videos = [v for v in weekly_videos if v["video_id"] not in realtime_ids]
    render_tab_content(weekly_videos, "주간", "weekly_cat_filter", pills_group=1)

with tab_analysis:
    all_videos = repo.get_all_trending_deduplicated()
    if not all_videos:
        render_empty_state("분석할 데이터가 없어요", "먼저 영상을 수집해주세요")
    else:
        insights = generate_insights(all_videos)
        df_all = pd.DataFrame(all_videos)

        st.caption(f"누적 수집된 고유 영상 {len(all_videos)}개 기준 분석")

        # ── 핵심 지표 ──
        render_section_title("핵심 지표 요약")
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown(render_metric_card(
                str(insights.get("total_videos", 0)), "수집 영상 수", "blue",
            ), unsafe_allow_html=True)
        with m2:
            st.markdown(render_metric_card(
                insights.get("avg_views", "0"), "평균 조회수", "green",
            ), unsafe_allow_html=True)
        with m3:
            st.markdown(render_metric_card(
                insights.get("max_views", "0"), "최고 조회수", "red",
            ), unsafe_allow_html=True)
        with m4:
            top_cat = insights.get("top_category", ("기타", 0))
            st.markdown(render_metric_card(
                top_cat[0], "인기 카테고리", "purple",
                hint=f"{top_cat[1]}개 영상",
            ), unsafe_allow_html=True)

        st.markdown("")

        # ── 1행: 카테고리 분포 + 태그 빈도 ──
        col_chart, col_tags = st.columns(2)

        with col_chart:
            if insights.get("category_distribution"):
                render_section_title("카테고리별 분포")
                cat_data = insights["category_distribution"]
                fig = px.pie(
                    names=[c[0] for c in cat_data],
                    values=[c[1] for c in cat_data],
                    hole=0.45,
                    color_discrete_sequence=["#FF4757", "#4C9AFF", "#36D399", "#FBBD23", "#A78BFA", "#FF6B81"],
                )
                fig.update_traces(
                    textposition="inside", textinfo="label+percent", textfont_size=12,
                )
                fig.update_layout(height=360, showlegend=False, **get_plotly_layout())
                st.plotly_chart(fig, use_container_width=True)

        with col_tags:
            render_section_title("트렌드 영상 업로드 시간대")
            if "published_at" in df_all.columns:
                df_time = df_all[df_all["published_at"].notna()].copy()
                df_time["hour"] = pd.to_datetime(df_time["published_at"]).dt.hour
                hour_counts = df_time["hour"].value_counts().reindex(range(24), fill_value=0)
                fig_hour = px.bar(
                    x=hour_counts.index, y=hour_counts.values,
                    labels={"x": "업로드 시간 (UTC)", "y": "영상 수"},
                    color_discrete_sequence=["#4C9AFF"],
                )
                peak_hour = hour_counts.idxmax()
                fig_hour.update_traces(
                    marker_color=["#FF4757" if h == peak_hour else "#4C9AFF" for h in range(24)],
                )
                fig_hour.update_layout(
                    height=360, showlegend=False,
                    xaxis=dict(dtick=2, tickmode="linear"),
                    **get_plotly_layout(),
                )
                st.plotly_chart(fig_hour, use_container_width=True)
                st.caption(f"트렌드 영상이 가장 많이 업로드된 시간: **UTC {peak_hour}시** (한국 시간 {(peak_hour + 9) % 24}시)")

        # ── 2행: 조회수 분포 + 참여율 분석 ──
        col_views, col_engage = st.columns(2)

        with col_views:
            render_section_title("조회수 분포")
            view_counts = df_all["view_count"].dropna()
            if not view_counts.empty:
                fig_hist = px.histogram(
                    view_counts, nbins=15,
                    labels={"value": "조회수", "count": "영상 수"},
                    color_discrete_sequence=["#4C9AFF"],
                )
                fig_hist.update_layout(
                    height=300, showlegend=False,
                    xaxis_title="조회수", yaxis_title="영상 수",
                    **get_plotly_layout(),
                )
                st.plotly_chart(fig_hist, use_container_width=True)

        with col_engage:
            render_section_title("참여율 TOP 10 (좋아요/조회수)")
            if "like_count" in df_all.columns:
                df_engage = df_all[df_all["view_count"] > 0].copy()
                df_engage["참여율(%)"] = (
                    df_engage["like_count"] / df_engage["view_count"] * 100
                ).round(2)
                top_engage = df_engage.nlargest(10, "참여율(%)")
                if not top_engage.empty:
                    fig_engage = px.bar(
                        top_engage, x="참여율(%)", y="title", orientation="h",
                        color_discrete_sequence=["#36D399"],
                        labels={"title": ""},
                    )
                    fig_engage.update_layout(
                        height=300, yaxis=dict(autorange="reversed"),
                        showlegend=False, **get_plotly_layout(),
                    )
                    # 제목 길이 제한
                    fig_engage.update_yaxes(
                        ticktext=[t[:20] + "…" if len(t) > 20 else t for t in top_engage["title"]],
                        tickvals=top_engage["title"],
                    )
                    st.plotly_chart(fig_engage, use_container_width=True)

        # ── 3행: 채널별 등장 횟수 + 영상 길이 분포 ──
        col_ch, col_dur = st.columns(2)

        with col_ch:
            render_section_title("채널별 등장 횟수 TOP 10")
            if "channel_title" in df_all.columns:
                ch_counts = df_all["channel_title"].value_counts().head(10)
                if not ch_counts.empty:
                    fig_ch = px.bar(
                        x=ch_counts.values, y=ch_counts.index, orientation="h",
                        labels={"x": "영상 수", "y": ""},
                        color_discrete_sequence=["#A78BFA"],
                    )
                    fig_ch.update_layout(
                        height=300, yaxis=dict(autorange="reversed"),
                        showlegend=False, **get_plotly_layout(),
                    )
                    fig_ch.update_yaxes(
                        ticktext=[t[:18] + "…" if len(t) > 18 else t for t in ch_counts.index],
                        tickvals=list(ch_counts.index),
                    )
                    st.plotly_chart(fig_ch, use_container_width=True)

        with col_dur:
            render_section_title("영상 길이 분포")
            if "duration" in df_all.columns:
                from src.analysis.insights import parse_duration_seconds
                df_all["duration_min"] = df_all["duration"].apply(
                    lambda d: parse_duration_seconds(d) / 60 if d else 0
                )
                dur_valid = df_all[df_all["duration_min"] > 0]["duration_min"]
                if not dur_valid.empty:
                    # 구간 분류
                    bins = [0, 4, 10, 20, 60, float("inf")]
                    bin_labels = ["~4분", "4~10분", "10~20분", "20~60분", "60분+"]
                    dur_cats = pd.cut(dur_valid, bins=bins, labels=bin_labels, right=False)
                    dur_dist = dur_cats.value_counts().reindex(bin_labels).fillna(0)

                    fig_dur = px.bar(
                        x=dur_dist.index, y=dur_dist.values,
                        labels={"x": "영상 길이", "y": "영상 수"},
                        color_discrete_sequence=["#FBBD23"],
                    )
                    fig_dur.update_layout(
                        height=300, showlegend=False, **get_plotly_layout(),
                    )
                    st.plotly_chart(fig_dur, use_container_width=True)

        # ── 4행: 인사이트 박스 ──
        render_section_title("AI 인사이트")
        i1, i2 = st.columns(2)
        with i1:
            avg_dur = insights.get("avg_duration_min", 0)
            small_hits = insights.get("small_channel_hits", 0)
            render_insight_box(
                f"트렌드 영상의 평균 길이는 <strong>{avg_dur}분</strong>이에요. "
                f"{'10분 이상의 긴 영상이 트렌드에 유리해요.' if avg_dur >= 10 else '짧은 영상도 트렌드에 오를 수 있어요.'}"
            )
        with i2:
            if small_hits > 0:
                render_insight_box(
                    f"구독자 5만 미만 채널 중 <strong>{small_hits}개</strong> 영상이 "
                    f"10만 조회를 돌파했어요. 소규모 채널도 기회가 있어요!"
                )
            else:
                import html as _html
                top_cat = insights.get("top_category", ("기타", 0))
                render_insight_box(
                    f"현재 트렌드의 <strong>{top_cat[1]}/{insights.get('total_videos', 0)}</strong> 영상이 "
                    f"<strong>{_html.escape(str(top_cat[0]))}</strong> 카테고리예요. 이 분야에 주목하세요."
                )


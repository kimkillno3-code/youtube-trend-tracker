"""콘텐츠 아이디어 파인더 — 급상승 키워드 · 키워드 갭 · 시즌 캘린더"""
import html as html_lib
import sys
from datetime import datetime
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from src.config import YOUTUBE_API_KEY, YOUTUBE_DAILY_QUOTA, DB_PATH, DATA_DIR, KST
from src.database.repository import TrendRepository
from dashboard.theme import (
    inject_custom_css, sidebar_with_badges, get_plotly_layout,
    render_page_header, render_metric_card,
    render_section_title, render_empty_state,
    render_freshness_bar, inject_pills_highlight,
)

st.set_page_config(page_title="콘텐츠 아이디어 - YT", layout="wide")
st.markdown('<style>[data-testid="stSidebarNav"]{display:none!important}</style>', unsafe_allow_html=True)

DATA_DIR.mkdir(parents=True, exist_ok=True)
repo = TrendRepository(str(DB_PATH))

inject_custom_css()
sidebar_with_badges(repo, current_page="ideas")

from dashboard.auth import require_auth
require_auth()

render_page_header("콘텐츠 아이디어", "급상승 키워드와 블루오션 주제를 찾아보세요")


# ── 탭 ──
tab_trending, tab_gap, tab_season = st.tabs(["급상승 키워드", "키워드 갭 분석", "시즌 캘린더"])


# ══════════════════════════════════════
# 탭 1: 급상승 키워드
# ══════════════════════════════════════
with tab_trending:
    if st.button("급상승 키워드 가져오기", type="primary", use_container_width=False):
        with st.spinner("Google Trends에서 급상승 키워드를 가져오고 있어요..."):
            try:
                from src.collector.google_trends import get_trending_searches
                trending = get_trending_searches(geo="KR")
                if trending:
                    # DB 저장
                    breakouts = []
                    for item in trending:
                        from src.collector.google_trends import _parse_traffic
                        traffic = _parse_traffic(item.get("traffic", "0"))
                        breakouts.append({
                            "keyword": item["keyword"],
                            "surge_pct": 1000.0,
                            "interest": min(traffic // 10, 100) if traffic else 50,
                            "traffic": traffic,
                        })
                    repo.save_breakout_keywords(breakouts)
                    st.session_state["trending_keywords"] = trending
                    st.session_state["trending_fetched_at"] = datetime.now(KST).isoformat()
                    st.toast(f"급상승 키워드 {len(trending)}개를 가져왔어요")
                else:
                    st.warning("현재 급상승 키워드가 없어요. 잠시 후 다시 시도해주세요.")
            except Exception as e:
                st.error(f"키워드 수집 중 오류가 발생했어요: {e}")

    # 이전 데이터 로드
    trending = st.session_state.get("trending_keywords")
    fetched_at = st.session_state.get("trending_fetched_at")

    if not trending:
        # DB에서 가장 최근 배치만 로드 (최신 detected_at 기준)
        recent = repo.get_recent_breakout_keywords(hours=24)
        if recent:
            latest_at = max(r.get("detected_at", "") for r in recent)
            batch = [r for r in recent if r.get("detected_at") == latest_at]
            trending = [
                {"keyword": r["keyword"], "traffic": str(r.get("trend_interest", 0)),
                 "news": []}
                for r in batch
            ]
            fetched_at = latest_at

    if not trending:
        render_empty_state(
            "급상승 키워드가 없어요",
            "버튼을 눌러 지금 뜨고 있는 검색어를 가져와보세요",
        )
    else:
        if fetched_at:
            render_freshness_bar(fetched_at)

        st.caption(f"총 {len(trending)}개 급상승 키워드")

        # 지표 카드
        m1, m2 = st.columns(2)
        with m1:
            st.markdown(render_metric_card(
                f"{len(trending)}개", "급상승 키워드", "red",
            ), unsafe_allow_html=True)
        with m2:
            top_kw = trending[0]["keyword"] if trending else "-"
            st.markdown(render_metric_card(
                top_kw, "1위 키워드", "blue",
            ), unsafe_allow_html=True)

        # 키워드 카드 그리드
        for i in range(0, len(trending), 2):
            cols = st.columns(2)
            for j in range(2):
                if i + j < len(trending):
                    item = trending[i + j]
                    rank = i + j + 1
                    kw = html_lib.escape(item.get("keyword", ""))
                    traffic = html_lib.escape(str(item.get("traffic", "")))
                    news = item.get("news", [])

                    news_html = ""
                    for n in news[:2]:
                        headline = html_lib.escape(n.get("headline", ""))
                        source = html_lib.escape(n.get("source", ""))
                        if headline:
                            news_html += f'<div class="kw-news"><span>{headline}</span> — {source}</div>'

                    with cols[j]:
                        st.markdown(f'''
                        <div class="keyword-card">
                            <div class="kw-header">
                                <span class="kw-rank">{rank}</span>
                                <span class="kw-name">{kw}</span>
                                <span class="kw-traffic">{traffic}</span>
                            </div>
                            {news_html}
                        </div>
                        ''', unsafe_allow_html=True)


# ══════════════════════════════════════
# 탭 2: 키워드 갭 분석
# ══════════════════════════════════════
with tab_gap:
    st.caption("수요(검색량)는 높은데 공급(영상)이 적은 블루오션 키워드를 찾아보세요")

    # 키워드 입력
    gap_keywords_input = st.text_input(
        "분석할 키워드 (쉼표로 구분, 최대 5개)",
        placeholder="예: 스파이더맨, BTS, 먹방",
        key="gap_input",
    )

    # 급상승 키워드에서 빠른 선택
    trending_kws = st.session_state.get("trending_keywords", [])
    if trending_kws:
        quick_labels = [item["keyword"] for item in trending_kws[:10]]
        btn_cols = st.columns([2, 2, 6])
        with btn_cols[0]:
            if st.button("전체선택", key="gap_pills_all", use_container_width=True):
                st.session_state["gap_quick_select"] = quick_labels
        with btn_cols[1]:
            if st.button("선택해제", key="gap_pills_clear", use_container_width=True):
                st.session_state["gap_quick_select"] = []
        selected_quick = st.pills(
            "급상승 키워드에서 선택", quick_labels,
            selection_mode="multi", key="gap_quick_select",
        )
        inject_pills_highlight(selected_quick, group_index=0)
    else:
        selected_quick = []

    if st.button("갭 분석 시작", type="primary", use_container_width=False):
        # 키워드 수집
        keywords = []
        if gap_keywords_input:
            keywords.extend([k.strip() for k in gap_keywords_input.split(",") if k.strip()])
        if selected_quick:
            keywords.extend([k for k in selected_quick if k not in keywords])
        keywords = keywords[:5]

        if not keywords:
            st.warning("분석할 키워드를 입력하거나 급상승 키워드에서 선택해주세요.")
        elif not YOUTUBE_API_KEY:
            st.error(
                "YouTube API 키가 설정되지 않았어요.\n\n"
                "1. [Google Cloud Console](https://console.cloud.google.com/)에서 API 키 발급\n"
                "2. 프로젝트 루트에 `.env` 파일 생성\n"
                "3. `YOUTUBE_API_KEY=발급받은키` 입력 후 저장"
            )
        else:
            # 할당량 체크
            today_used = repo.get_today_quota_used()
            estimated_cost = len(keywords) * 101  # search 100 + video details 1
            if today_used + estimated_cost >= YOUTUBE_DAILY_QUOTA * 0.9:
                st.error(
                    f"오늘 API 할당량의 {today_used / YOUTUBE_DAILY_QUOTA * 100:.0f}%를 사용했어요. "
                    "갭 분석에는 키워드당 약 100유닛이 필요합니다."
                )
            else:
                from src.collector.youtube_api import YouTubeAPIClient
                from src.analysis.keyword_gap import batch_analyze_gaps
                api = YouTubeAPIClient(YOUTUBE_API_KEY)
                log_id = repo.log_start("keyword_gap")
                try:
                    with st.spinner(f"{len(keywords)}개 키워드를 분석하고 있어요..."):
                        results = batch_analyze_gaps(api, keywords)
                        repo.save_keyword_gaps(results)
                        repo.log_end(log_id, "success", len(results), api.quota_used)
                    st.session_state["gap_results"] = results
                    st.toast(f"{len(results)}개 키워드 갭 분석 완료")
                except Exception as e:
                    repo.log_end(log_id, "failed", 0, 0, str(e))
                    st.error(f"분석 중 오류가 발생했어요: {e}")

    # 결과 표시
    gap_results = st.session_state.get("gap_results")
    if not gap_results:
        # DB에서 로드 시도
        saved_gaps = repo.get_keyword_gaps()
        if saved_gaps:
            gap_results = saved_gaps

    if gap_results:
        render_section_title("분석 결과")

        for gap in gap_results:
            kw = html_lib.escape(gap["keyword"])
            opp = gap["opportunity_score"]
            demand = gap["demand_score"]
            supply = gap["supply_score"]
            comp = gap.get("competition_level", "보통")
            vcount = gap.get("video_count_7d", 0)
            avg_v = gap.get("avg_views_7d", 0)

            # 점수별 색상
            score_cls = "high" if opp >= 60 else ("mid" if opp >= 40 else "low")

            # 경쟁강도별 배지
            comp_map = {"매우 낮음": "very-low", "낮음": "low", "보통": "mid", "높음": "high"}
            comp_cls = comp_map.get(comp, "mid")

            # 평균 조회수 포맷
            if avg_v >= 1_000_000:
                avg_v_str = f"{avg_v / 1_000_000:.1f}M"
            elif avg_v >= 1_000:
                avg_v_str = f"{avg_v / 1_000:.1f}K"
            else:
                avg_v_str = str(avg_v)

            st.markdown(f'''
            <div class="gap-card">
                <div class="gap-keyword">{kw}</div>
                <div style="display:flex;align-items:center;gap:16px;">
                    <div>
                        <div style="font-size:0.7rem;color:#9BA3B0;text-transform:uppercase;letter-spacing:0.05em;">기회점수</div>
                        <div class="gap-score {score_cls}">{opp}</div>
                    </div>
                    <div style="flex:1;">
                        <div style="font-size:0.72rem;color:#9BA3B0;margin-bottom:2px;">수요 (검색 관심도)</div>
                        <div class="gap-bar-wrap"><div class="gap-bar-fill demand" style="width:{demand}%"></div></div>
                        <div style="font-size:0.72rem;color:#9BA3B0;margin-bottom:2px;margin-top:6px;">공급 (영상 포화도)</div>
                        <div class="gap-bar-wrap"><div class="gap-bar-fill supply" style="width:{supply}%"></div></div>
                    </div>
                </div>
                <div class="gap-meta">
                    <span>경쟁: <span class="gap-badge {comp_cls}">{html_lib.escape(comp)}</span></span>
                    <span>7일 영상: <strong>{vcount}개</strong></span>
                    <span>평균 조회수: <strong>{avg_v_str}</strong></span>
                </div>
            </div>
            ''', unsafe_allow_html=True)
    else:
        render_empty_state(
            "갭 분석 결과가 없어요",
            "키워드를 입력하고 분석을 시작해보세요",
        )


# ══════════════════════════════════════
# 탭 3: 시즌 캘린더
# ══════════════════════════════════════
with tab_season:
    st.caption("현재월부터 12개월간 예상 시즌 키워드 + Google Trends 실시간 연관 검색어")

    from src.analysis.seasonal import get_full_year_keywords

    year_keywords = get_full_year_keywords()

    # 지표 요약
    total_kw = sum(len(v) for v in year_keywords.values())
    all_cats = {kw["category"] for kws in year_keywords.values() for kw in kws}
    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(render_metric_card(
            f"{total_kw}개", "12개월 시즌 키워드", "purple",
        ), unsafe_allow_html=True)
    with m2:
        st.markdown(render_metric_card(
            "12개월", "예측 범위", "red",
        ), unsafe_allow_html=True)
    with m3:
        st.markdown(render_metric_card(
            f"{len(all_cats)}개", "카테고리", "blue",
        ), unsafe_allow_html=True)

    # 월 선택 필터
    month_labels = list(year_keywords.keys())
    selected_month = st.pills(
        "월 선택", month_labels,
        default=month_labels[0],
        key="season_month_select",
    )
    inject_pills_highlight(
        [selected_month] if selected_month else [],
        group_index=0,
    )

    sel_month = selected_month if selected_month else month_labels[0]
    kws = sorted(year_keywords.get(sel_month, []), key=lambda k: -k["confidence"])

    CAT_COLORS = {
        "시즌": "#3B82F6", "여행": "#10B981", "교육": "#F59E0B",
        "이벤트": "#FF4757", "전통": "#A78BFA", "엔터": "#EC4899",
        "패션": "#F472B6", "라이프": "#6EE7B7", "레저": "#22D3EE",
        "날씨": "#64748B", "건강": "#34D399", "가전": "#94A3B8",
        "음식": "#FB923C", "쇼핑": "#E879F9", "경제": "#FBBF24",
        "스포츠": "#38BDF8",
    }

    if kws:
        # 신뢰도 차트
        layout = get_plotly_layout()
        fig = go.Figure()
        y_labels = [f"{kw['keyword']}  ({kw['category']})" for kw in kws]
        x_vals = [kw["confidence"] for kw in kws]
        colors = [CAT_COLORS.get(kw["category"], "#6B7280") for kw in kws]
        text_labels = [f"  {kw['confidence']}%" for kw in kws]

        fig.add_trace(go.Bar(
            y=y_labels, x=x_vals, orientation="h",
            marker=dict(color=colors, line=dict(width=0), opacity=0.85),
            text=text_labels, textposition="outside", textfont=dict(size=11),
            hoverinfo="text",
            hovertext=[
                f"<b>{kw['keyword']}</b><br>카테고리: {kw['category']}<br>신뢰도: {kw['confidence']}%"
                for kw in kws
            ],
        ))
        fig.update_layout(
            **layout,
            height=max(280, len(y_labels) * 42 + 60),
            xaxis=dict(title="신뢰도 (%)", range=[0, 115], showgrid=True,
                        gridcolor="rgba(255,255,255,0.06)", dtick=20),
            yaxis=dict(tickfont=dict(size=12)),
            showlegend=False, bargap=0.3,
        )
        st.plotly_chart(fig, use_container_width=True)

        # Google Trends 연관 검색어
        st.divider()
        render_section_title(f"{sel_month} 키워드 — Google Trends 연관 검색어")
        sel_kw = st.selectbox(
            "키워드 선택", [kw["keyword"] for kw in kws],
            key="season_gtrends_kw",
        )
        if sel_kw:
            try:
                from src.collector.google_trends import get_related_queries
                with st.spinner(f"'{sel_kw}' 연관 검색어 조회 중..."):
                    related = get_related_queries(sel_kw)
                col_rise, col_top = st.columns(2)
                with col_rise:
                    render_section_title("급상승 연관 검색어")
                    if related.get("rising"):
                        for q in related["rising"][:10]:
                            st.markdown(
                                f"**{q['query']}** · "
                                f"<span style='color:#36D399'>{q.get('value', '')}</span>",
                                unsafe_allow_html=True,
                            )
                    else:
                        st.caption("데이터 없음")
                with col_top:
                    render_section_title("인기 연관 검색어")
                    if related.get("top"):
                        for q in related["top"][:10]:
                            st.markdown(
                                f"**{q['query']}** · {q.get('value', '')}",
                                unsafe_allow_html=True,
                            )
                    else:
                        st.caption("데이터 없음")
            except Exception as e:
                st.warning(f"Google Trends 조회 실패: {e}")
    else:
        render_empty_state(
            "시즌 키워드가 없어요",
            "시스템 오류가 발생했을 수 있어요",
        )

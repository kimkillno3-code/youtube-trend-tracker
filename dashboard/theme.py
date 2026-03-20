"""공유 CSS 테마 및 UI 컴포넌트 — v8
다크 모드 강제 적용. WCAG AA 명도 대비 교정. 간격 체계 재설계. 탭 대비 강화.
"""
import html as html_lib
import streamlit as st

# ── 디자인 토큰 ──
PLOTLY_COLORWAY = ["#FF4757", "#4C9AFF", "#36D399", "#FBBD23", "#A78BFA", "#FF6B81"]

PLOTLY_LAYOUT = {
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor": "rgba(0,0,0,0)",
    "font": {"color": "#F0F2F5", "family": "'Inter', -apple-system, sans-serif"},
    "colorway": PLOTLY_COLORWAY,
    "margin": dict(l=20, r=20, t=40, b=20),
}


def get_plotly_layout():
    """테마에 따라 Plotly 레이아웃 반환"""
    is_light = st.session_state.get("_theme_pref", False) or st.session_state.get("theme_light", False)
    return {
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {
            "color": "#24292F" if is_light else "#F0F2F5",
            "family": "'Inter', -apple-system, sans-serif",
        },
        "colorway": PLOTLY_COLORWAY,
        "margin": dict(l=20, r=20, t=40, b=20),
    }

_CARD_COLORS = ("red", "blue", "green", "amber", "purple")


def inject_custom_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    /* ═══════════════════════════════════
       GLOBAL RESET
       ═══════════════════════════════════ */
    .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        -webkit-font-smoothing: antialiased;
    }
    [data-testid="stSidebarNav"] { display: none !important; }
    /* Streamlit 장식/배포 버튼 숨김 — 헤더 자체는 유지 (모바일 사이드바 토글) */
    .stApp [data-testid="stStatusWidget"],
    .stDeployButton,
    [data-testid="stDecoration"],
    .stDecoration { display: none !important; }
    header[data-testid="stHeader"] {
        background: transparent !important;
        border-bottom: none !important;
        height: 50px !important;
        min-height: 50px !important;
        max-height: 50px !important;
        pointer-events: none !important;
    }
    .stApp [data-testid="stAppViewContainer"] > .stMainBlockContainer,
    .stApp .block-container {
        padding-top: 0 !important;
    }
    /* autorefresh 컴포넌트 빈 공간 제거 */
    div[class*="st-key-cmd_center_refresh"],
    .st-key-cmd_center_refresh,
    [data-stale] iframe[title*="autorefresh"],
    .stElementContainer:first-child:has(iframe) {
        height: 0 !important;
        min-height: 0 !important;
        overflow: hidden !important;
        margin: 0 !important;
        padding: 0 !important;
        line-height: 0 !important;
    }
    /* 사이드바 내부 상단 스페이서 제거 */
    .e1dbuyne10 {
        display: none !important;
    }
    /* 사이드바 토글 버튼: ">>" → 햄버거 아이콘 (크기는 Streamlit 기본값 유지) */
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="collapsedControl"] {
        z-index: 999 !important;
    }
    [data-testid="stSidebarCollapsedControl"] button,
    [data-testid="collapsedControl"] button,
    header[data-testid="stHeader"] button[kind="headerNoPadding"],
    header[data-testid="stHeader"] button[data-testid="baseButton-headerNoPadding"] {
        background: rgba(255,255,255,0.06) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 10px !important;
        width: 48px !important; height: 48px !important;
        padding: 0 !important;
        display: flex !important; align-items: center !important;
        justify-content: center !important;
        font-size: 0 !important;
        color: transparent !important;
        overflow: hidden !important;
        cursor: pointer !important;
    }
    [data-testid="stSidebarCollapsedControl"] button > *,
    [data-testid="collapsedControl"] button > *,
    header[data-testid="stHeader"] button[kind="headerNoPadding"] > *,
    header[data-testid="stHeader"] button[data-testid="baseButton-headerNoPadding"] > * {
        display: none !important;
    }
    [data-testid="stSidebarCollapsedControl"] button::after,
    [data-testid="collapsedControl"] button::after,
    header[data-testid="stHeader"] button[kind="headerNoPadding"]::after,
    header[data-testid="stHeader"] button[data-testid="baseButton-headerNoPadding"]::after {
        content: '\\2630' !important;
        font-size: 1.4rem !important;
        color: #E6EDF3 !important;
        line-height: 1;
        pointer-events: none !important;
    }
    /* Streamlit 우측 상단 메뉴 + Fork/GitHub 버튼 숨김 */
    #MainMenu,
    [data-testid="stMainMenu"],
    [data-testid="stToolbar"] [data-testid="stToolbarActions"],
    [data-testid="stToolbar"] .stActionButton,
    header[data-testid="stHeader"] [data-testid="stMainMenu"] {
        display: none !important;
    }
    /* Streamlit Cloud 하단 배지/워터마크 숨김 */
    footer,
    .stApp footer,
    [data-testid="manage-app-button"],
    [data-testid="stAppDeployButton"],
    [data-testid="stBottom"],
    [data-testid="stBottomBlockContainer"],
    a[href*="streamlit.io"],
    div[class*="viewerBadge"],
    div[class*="HostButton"],
    div[class*="hostToolbar"],
    div[class*="StatusWidget"],
    ._container_gzau3_1,
    ._link_gzau3_18,
    ._profileContainer_gzau3_53 {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        overflow: hidden !important;
        opacity: 0 !important;
        pointer-events: none !important;
    }
    /* Streamlit 상단 컬러바 / 런닝 인디케이터 */
    .stApp > div:first-child > div:first-child,
    .stApp::before,
    .stApp > div:first-child::before {
        background: transparent !important;
        display: none !important;
    }
    /* Inline-style 데코레이션 바 (fallback) */
    div[style*="position: fixed"][style*="height: 0.125rem"],
    div[style*="position: fixed"][style*="top: 0px"][style*="z-index: 99999"],
    div[style*="position: fixed"][style*="top: 0px"][style*="background: linear-gradient"] {
        display: none !important;
        background: transparent !important;
        height: 0 !important;
        visibility: hidden !important;
    }
    /* 전체 body/root 배경 강제 */
    html, body, [data-testid="stAppViewContainer"],
    .stApp, .main, .block-container {
        background-color: #0B0E14 !important;
        color: #E6EDF3 !important;
    }

    /* 간격 체계 — 요소별 제어 */
    .stApp [data-testid="stVerticalBlock"] > div {
        margin-bottom: 4px !important;
    }
    .stApp [data-testid="stVerticalBlock"] > div:has(> .stButton),
    .stApp [data-testid="stVerticalBlock"] > div:has(> .stDownloadButton) {
        margin-bottom: 2px !important;
    }
    .stApp [data-testid="stVerticalBlock"] > div:has(> .stMarkdown > .page-header) {
        margin-bottom: 12px !important;
    }
    .stApp [data-testid="stVerticalBlock"] > div:has(> .stMarkdown > .metric-card) {
        margin-bottom: 8px !important;
    }
    .stApp [data-testid="stVerticalBlock"] > div:has(> .stTabs) {
        margin-bottom: 0 !important;
    }

    /* ═══════════════════════════════════
       SIDEBAR
       ═══════════════════════════════════ */
    section[data-testid="stSidebar"] {
        background: #0B0E14 !important;
        border-right: 1px solid rgba(255,255,255,0.06);
    }
    /* 사이드바 상단 빈 공간 제거 */
    section[data-testid="stSidebar"] > div:first-child {
        padding-top: 0.5rem !important;
    }
    section[data-testid="stSidebar"] hr {
        border-color: rgba(255,255,255,0.08) !important;
        margin: 12px 0 !important;
    }
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] div,
    section[data-testid="stSidebar"] .stMarkdown,
    section[data-testid="stSidebar"] .stMarkdown p {
        color: #C9D1D9 !important;
    }
    section[data-testid="stSidebar"] [data-testid="stToggle"] label span,
    section[data-testid="stSidebar"] .stToggle label span {
        color: #C9D1D9 !important;
    }
    section[data-testid="stSidebar"] [data-testid="stCaption"],
    section[data-testid="stSidebar"] .stCaption {
        color: #9BA3B0 !important;
    }
    section[data-testid="stSidebar"] .stPageLink a {
        color: #C9D1D9 !important;
        font-size: 0.85rem !important;
        font-weight: 500 !important;
        padding: 8px 12px !important;
        border-radius: 8px !important;
    }
    section[data-testid="stSidebar"] .stPageLink a:hover,
    section[data-testid="stSidebar"] .stPageLink a[aria-current="page"] {
        background: #1A1F2B !important;
        color: #FFFFFF !important;
    }

    /* ═══════════════════════════════════
       PAGE HEADER
       ═══════════════════════════════════ */
    .page-header {
        background: linear-gradient(135deg, #141820 0%, #1A1F2B 50%, #1E1A2E 100%);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 16px;
        padding: 28px 32px;
        margin-bottom: 16px;
        position: relative; overflow: hidden;
    }
    .page-header::before {
        content: '';
        position: absolute; top: 0; right: 0;
        width: 300px; height: 100%;
        background: radial-gradient(ellipse at top right, rgba(255,71,87,0.06) 0%, transparent 70%);
        pointer-events: none;
    }
    .page-header h1 {
        font-size: 1.5rem; font-weight: 800; margin: 0;
        color: #F0F2F5; letter-spacing: -0.03em; position: relative;
    }
    .page-header .subtitle {
        color: #C9D1D9; font-size: 0.82rem; margin-top: 4px;
        font-weight: 400; position: relative;
    }

    /* ═══════════════════════════════════
       METRIC CARD
       ═══════════════════════════════════ */
    .metric-card {
        background: #141820;
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 12px;
        padding: 18px 20px;
        position: relative; overflow: hidden;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .metric-card::before {
        content: ''; position: absolute;
        top: 0; left: 0; right: 0; height: 3px;
    }
    .metric-card:hover {
        border-color: rgba(255,255,255,0.12);
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0,0,0,0.3);
    }
    .metric-card.red::before    { background: linear-gradient(90deg, #FF4757, #FF6B81); }
    .metric-card.blue::before   { background: linear-gradient(90deg, #4C9AFF, #68B6FF); }
    .metric-card.green::before  { background: linear-gradient(90deg, #36D399, #6EE7B7); }
    .metric-card.amber::before  { background: linear-gradient(90deg, #FBBD23, #FCD34D); }
    .metric-card.purple::before { background: linear-gradient(90deg, #A78BFA, #C4B5FD); }
    .metric-card .metric-label {
        font-size: 0.7rem; color: #C9D1D9;
        text-transform: uppercase; letter-spacing: 0.08em;
        font-weight: 600; margin-bottom: 10px;
    }
    .metric-card .metric-value {
        font-size: 1.6rem; font-weight: 800;
        color: #F0F2F5; letter-spacing: -0.03em; line-height: 1;
    }
    .metric-card .metric-hint {
        font-size: 0.72rem; color: #C9D1D9;
        margin-top: 8px; line-height: 1.3;
    }

    /* ═══════════════════════════════════
       SECTION TITLE
       ═══════════════════════════════════ */
    .section-title {
        font-size: 0.88rem; font-weight: 700; color: #E6EDF3;
        margin: 16px 0 8px;
        padding: 0 0 0 12px;
        border-left: 3px solid #FF4757;
    }

    /* ═══════════════════════════════════
       VIDEO GRID CARD
       ═══════════════════════════════════ */
    .vgrid {
        background: #141820;
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 14px; overflow: hidden;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        margin-bottom: 12px;
    }
    .vgrid:hover {
        border-color: rgba(255,255,255,0.15);
        transform: translateY(-3px);
        box-shadow: 0 12px 32px rgba(0,0,0,0.35);
    }
    .vgrid .vg-thumb {
        position: relative; width: 100%;
        aspect-ratio: 16/9; overflow: hidden;
        background: #0B0E14;
    }
    .vgrid .vg-thumb img {
        width: 100%; height: 100%; object-fit: cover;
        transition: transform 0.3s ease;
    }
    .vgrid:hover .vg-thumb img { transform: scale(1.03); }
    .vgrid .vg-rank {
        position: absolute; top: 10px; left: 10px;
        background: rgba(0,0,0,0.7);
        backdrop-filter: blur(4px);
        color: #fff; font-weight: 800; font-size: 0.72rem;
        padding: 4px 10px; border-radius: 6px;
    }
    .vgrid .vg-rank.top3 {
        background: linear-gradient(135deg, #FF4757, #FF6B81);
    }
    .vgrid .vg-body { padding: 14px 16px; }
    .vgrid .vg-title {
        font-size: 0.88rem; font-weight: 600;
        color: #F0F2F5; text-decoration: none; line-height: 1.35;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical; overflow: hidden;
    }
    .vgrid .vg-title:hover { color: #FF4757; }
    .vgrid .vg-channel { font-size: 0.73rem; color: #C9D1D9; margin-top: 6px; }
    .vgrid .vg-stats {
        display: flex; align-items: center; gap: 12px;
        margin-top: 10px; padding-top: 10px;
        border-top: 1px solid rgba(255,255,255,0.06);
    }
    .vgrid .vg-stat { font-size: 0.75rem; color: #C9D1D9; }
    .vgrid .vg-stat strong { color: #F0F2F5; font-weight: 700; }
    .vgrid .vg-stars { margin-left: auto; font-size: 0.78rem; letter-spacing: 1px; }

    /* ═══════════════════════════════════
       EMPTY STATE
       ═══════════════════════════════════ */
    .empty-state {
        text-align: center; padding: 56px 24px;
        background: #141820;
        border: 1px dashed rgba(255,255,255,0.08);
        border-radius: 16px; margin: 12px 0;
    }
    .empty-state .title {
        font-size: 1.05rem; font-weight: 700;
        color: #F0F2F5; margin-bottom: 6px;
    }
    .empty-state .desc { color: #C9D1D9; font-size: 0.82rem; line-height: 1.5; }

    /* ═══════════════════════════════════
       INSIGHT BOX
       ═══════════════════════════════════ */
    .insight-box {
        background: #141820;
        border: 1px solid rgba(255,255,255,0.06);
        border-left: 3px solid #4C9AFF;
        border-radius: 0 12px 12px 0;
        padding: 14px 18px; margin: 8px 0 16px;
        font-size: 0.82rem; line-height: 1.7; color: #C9D1D9;
    }
    .insight-box strong { color: #F0F2F5; }

    /* ═══════════════════════════════════
       FRESHNESS BAR
       ═══════════════════════════════════ */
    .freshness-bar {
        background: #141820;
        border: 1px solid rgba(255,255,255,0.06);
        border-left: 3px solid #36D399;
        border-radius: 0 10px 10px 0;
        padding: 10px 16px;
        font-size: 0.78rem; color: #C9D1D9;
        font-weight: 500; margin: 0 0 12px;
        display: flex; align-items: center; gap: 8px;
    }
    .freshness-bar .freshness-icon { font-size: 0.85rem; }
    .freshness-bar .freshness-time { color: #F0F2F5; font-weight: 700; }
    .freshness-bar .freshness-hint { color: #9BA3B0; margin-left: auto; font-weight: 400; }
    .freshness-bar.fresh { border-left-color: #36D399; }
    .freshness-bar.stale { border-left-color: #FBBD23; }
    .freshness-bar.old   { border-left-color: #FF4757; }

    /* ═══════════════════════════════════
       KEYWORD CARD (급상승 키워드)
       ═══════════════════════════════════ */
    .keyword-card {
        background: #141820;
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 12px;
        padding: 16px 18px;
        margin-bottom: 10px;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .keyword-card:hover {
        border-color: rgba(255,255,255,0.15);
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0,0,0,0.3);
    }
    .keyword-card .kw-header {
        display: flex; align-items: center; gap: 10px;
        margin-bottom: 8px;
    }
    .keyword-card .kw-rank {
        background: rgba(255,71,87,0.15);
        color: #FF6B81; font-weight: 800; font-size: 0.72rem;
        padding: 3px 8px; border-radius: 6px; min-width: 28px;
        text-align: center;
    }
    .keyword-card .kw-name {
        font-size: 0.95rem; font-weight: 700; color: #F0F2F5;
    }
    .keyword-card .kw-traffic {
        margin-left: auto;
        background: rgba(76,154,255,0.12);
        color: #4C9AFF; font-weight: 700; font-size: 0.72rem;
        padding: 3px 10px; border-radius: 20px;
    }
    .keyword-card .kw-news {
        font-size: 0.75rem; color: #9BA3B0; line-height: 1.5;
        margin-top: 4px;
    }
    .keyword-card .kw-news span { color: #C9D1D9; }

    /* ═══════════════════════════════════
       GAP BAR (키워드 갭 분석)
       ═══════════════════════════════════ */
    .gap-card {
        background: #141820;
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 12px;
        padding: 16px 18px; margin-bottom: 10px;
    }
    .gap-card .gap-keyword {
        font-size: 0.95rem; font-weight: 700; color: #F0F2F5;
        margin-bottom: 10px;
    }
    .gap-card .gap-score {
        font-size: 1.4rem; font-weight: 800; margin-bottom: 8px;
    }
    .gap-card .gap-score.high { color: #36D399; }
    .gap-card .gap-score.mid  { color: #FBBD23; }
    .gap-card .gap-score.low  { color: #FF4757; }
    .gap-bar-wrap {
        background: rgba(255,255,255,0.06);
        border-radius: 6px; height: 8px; overflow: hidden;
        margin: 6px 0;
    }
    .gap-bar-fill {
        height: 100%; border-radius: 6px;
        transition: width 0.4s ease;
    }
    .gap-bar-fill.demand { background: #4C9AFF; }
    .gap-bar-fill.supply { background: #FF4757; }
    .gap-card .gap-meta {
        display: flex; gap: 12px; margin-top: 8px;
        font-size: 0.75rem; color: #9BA3B0;
    }
    .gap-card .gap-meta strong { color: #F0F2F5; }
    .gap-badge {
        display: inline-block;
        padding: 2px 10px; border-radius: 20px;
        font-size: 0.7rem; font-weight: 700;
    }
    .gap-badge.very-low { background: rgba(54,211,153,0.15); color: #36D399; }
    .gap-badge.low      { background: rgba(76,154,255,0.15); color: #4C9AFF; }
    .gap-badge.mid      { background: rgba(251,189,35,0.15); color: #FBBD23; }
    .gap-badge.high     { background: rgba(255,71,87,0.15); color: #FF6B81; }

    /* ═══════════════════════════════════
       SEASON TAG (시즌 캘린더)
       ═══════════════════════════════════ */
    .season-week {
        margin-bottom: 16px;
    }
    .season-week-label {
        font-size: 0.82rem; font-weight: 700; color: #F0F2F5;
        margin-bottom: 8px;
        padding-left: 12px; border-left: 3px solid #A78BFA;
    }
    .season-tags { display: flex; flex-wrap: wrap; gap: 8px; }
    .season-tag {
        display: inline-flex; align-items: center; gap: 6px;
        background: #1A1F2B;
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 20px; padding: 6px 14px;
        font-size: 0.8rem; font-weight: 500; color: #C9D1D9;
    }
    .season-tag .st-conf {
        font-size: 0.65rem; font-weight: 700;
        padding: 1px 6px; border-radius: 10px;
    }
    .season-tag .st-conf.high   { background: rgba(54,211,153,0.15); color: #36D399; }
    .season-tag .st-conf.medium { background: rgba(251,189,35,0.15); color: #FBBD23; }
    .season-tag .st-cat {
        font-size: 0.68rem; color: #9BA3B0;
    }

    /* ═══════════════════════════════════
       FILTER INFO
       ═══════════════════════════════════ */
    .filter-info {
        background: rgba(76,154,255,0.08);
        border: 1px solid rgba(76,154,255,0.15);
        border-radius: 10px; padding: 10px 16px;
        font-size: 0.8rem; color: #4C9AFF;
        font-weight: 500; margin: 8px 0;
    }

    /* ═══════════════════════════════════
       ACTION BAR
       ═══════════════════════════════════ */
    .action-bar {
        display: flex; align-items: center; justify-content: space-between;
        padding: 4px 0; margin: 8px 0;
    }
    .action-bar .count { font-size: 0.82rem; color: #C9D1D9; font-weight: 500; }
    .action-bar .count strong { color: #F0F2F5; font-weight: 700; }

    /* ═══════════════════════════════════
       FORM ELEMENTS — 강제 다크
       ═══════════════════════════════════ */

    /* 텍스트 인풋 — 모든 가능한 셀렉터 */
    .stApp input[type="text"],
    .stApp input[type="number"],
    .stApp input[type="search"],
    .stApp input[type="email"],
    .stApp input[type="password"],
    .stApp input:not([type]),
    .stTextInput input,
    .stNumberInput input,
    [data-testid="stTextInput"] input,
    [data-testid="stNumberInput"] input,
    [data-baseweb="input"] input {
        background-color: #0B0E14 !important;
        color: #F0F2F5 !important;
        -webkit-text-fill-color: #F0F2F5 !important;
        border-color: rgba(255,255,255,0.1) !important;
        caret-color: #FF4757 !important;
    }

    /* 인풋 래퍼 (baseui) */
    [data-baseweb="input"],
    [data-baseweb="input"] > div,
    .stTextInput > div > div,
    [data-testid="stTextInput"] > div > div {
        background-color: #0B0E14 !important;
        border-color: rgba(255,255,255,0.1) !important;
    }

    /* 포커스 상태 — 배경색 유지 필수 */
    .stApp input:focus,
    .stApp input:active {
        background-color: #0B0E14 !important;
        color: #F0F2F5 !important;
        -webkit-text-fill-color: #F0F2F5 !important;
        border-color: rgba(255,71,87,0.5) !important;
        box-shadow: 0 0 0 1px rgba(255,71,87,0.25) !important;
    }
    [data-baseweb="input"]:focus-within,
    [data-baseweb="input"]:focus-within > div,
    .stTextInput > div > div:focus-within,
    [data-testid="stTextInput"] > div > div:focus-within,
    [data-testid="stForm"] [data-baseweb="input"]:focus-within,
    [data-testid="stForm"] [data-baseweb="input"]:focus-within > div {
        background-color: #0B0E14 !important;
        border-color: rgba(255,71,87,0.5) !important;
        box-shadow: 0 0 0 1px rgba(255,71,87,0.25) !important;
    }

    /* 브라우저 자동완성(autofill) 배경색 강제 */
    .stApp input:-webkit-autofill,
    .stApp input:-webkit-autofill:hover,
    .stApp input:-webkit-autofill:focus,
    .stApp input:-webkit-autofill:active {
        -webkit-box-shadow: 0 0 0 30px #0B0E14 inset !important;
        -webkit-text-fill-color: #F0F2F5 !important;
        box-shadow: 0 0 0 30px #0B0E14 inset !important;
        transition: background-color 5000s ease-in-out 0s !important;
        caret-color: #FF4757 !important;
    }

    /* 플레이스홀더 */
    .stApp input::placeholder,
    .stApp textarea::placeholder {
        color: #6E7681 !important;
        -webkit-text-fill-color: #6E7681 !important;
        opacity: 1 !important;
    }

    /* 텍스트에어리어 */
    .stApp textarea,
    .stTextArea textarea,
    [data-baseweb="textarea"],
    [data-baseweb="textarea"] textarea {
        background-color: #0B0E14 !important;
        color: #F0F2F5 !important;
        -webkit-text-fill-color: #F0F2F5 !important;
        border-color: rgba(255,255,255,0.1) !important;
    }

    /* 셀렉트박스 — 모든 가능한 셀렉터 */
    .stSelectbox > div > div,
    .stSelectbox [data-baseweb="select"] > div,
    [data-testid="stSelectbox"] > div > div,
    [data-testid="stSelectbox"] [data-baseweb="select"] > div,
    [data-baseweb="select"] > div {
        background-color: #0B0E14 !important;
        border-color: rgba(255,255,255,0.1) !important;
        color: #F0F2F5 !important;
    }
    [data-baseweb="select"] > div > div,
    [data-baseweb="select"] span,
    .stSelectbox [data-baseweb="select"] span {
        color: #F0F2F5 !important;
    }
    [data-baseweb="select"] svg {
        fill: #8B949E !important;
    }

    /* 드롭다운 팝오버 */
    [data-baseweb="popover"],
    [data-baseweb="popover"] > div,
    [data-baseweb="popover"] > div > div {
        background-color: #141820 !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 10px !important;
        box-shadow: 0 12px 40px rgba(0,0,0,0.6) !important;
    }
    [data-baseweb="menu"],
    [data-baseweb="menu"] > div,
    [data-baseweb="menu"] ul,
    ul[role="listbox"] {
        background-color: #141820 !important;
    }
    [data-baseweb="menu"] [role="option"],
    ul[role="listbox"] [role="option"],
    [data-baseweb="menu"] li,
    ul[role="listbox"] li {
        color: #F0F2F5 !important;
        background-color: transparent !important;
    }
    [data-baseweb="menu"] [role="option"]:hover,
    ul[role="listbox"] [role="option"]:hover,
    [data-baseweb="menu"] li:hover,
    ul[role="listbox"] li:hover {
        background-color: #1A1F2B !important;
    }
    [data-baseweb="menu"] [role="option"][aria-selected="true"],
    ul[role="listbox"] [role="option"][aria-selected="true"],
    [data-baseweb="menu"] li[aria-selected="true"],
    ul[role="listbox"] li[aria-selected="true"] {
        background-color: rgba(255,71,87,0.08) !important;
    }

    /* ═══════════════════════════════════
       ALERTS — 좌측 액센트 바 스타일
       ═══════════════════════════════════ */
    .stAlert {
        background-color: transparent !important;
        border: none !important;
        border-left: 3px solid #4C9AFF !important;
        border-radius: 0 !important;
        padding: 8px 14px !important;
    }
    .stAlert > div,
    .stAlert [data-baseweb="notification"],
    .stAlert [data-baseweb="notification"] > div {
        background-color: transparent !important;
        border: none !important;
        border-left: none !important;
        padding: 0 !important;
    }
    /* success — 초록 */
    .stAlert:has([kind="positive"]),
    .stAlert:has(svg[data-testid="stIconSuccess"]) {
        border-left-color: #3FB950 !important;
    }
    /* warning — 주황 */
    .stAlert:has([kind="warning"]),
    .stAlert:has(svg[data-testid="stIconWarning"]) {
        border-left-color: #D29922 !important;
    }
    /* error — 빨강 */
    .stAlert:has([kind="negative"]),
    .stAlert:has(svg[data-testid="stIconError"]) {
        border-left-color: #F85149 !important;
    }
    /* 알림 텍스트 */
    .stAlert p, .stAlert span {
        color: #C9D1D9 !important;
        font-size: 0.85rem !important;
    }
    .stAlert svg { min-width: 20px; }

    /* Toast */
    [data-testid="stToast"],
    [data-testid="stToast"] > div {
        background-color: #141820 !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        color: #F0F2F5 !important;
        border-radius: 10px !important;
    }

    /* ═══════════════════════════════════
       BUTTONS
       ═══════════════════════════════════ */
    .stButton > button[kind="primary"],
    button[data-testid="stFormSubmitButton"],
    [data-testid="stForm"] button[type="submit"] {
        background: linear-gradient(135deg, #FF4757, #FF6B81) !important;
        border: none !important; border-radius: 10px !important;
        font-weight: 700 !important; font-size: 0.85rem !important;
        box-shadow: 0 4px 16px rgba(255,71,87,0.2) !important;
        color: #fff !important;
    }
    .stButton > button[kind="primary"]:hover,
    button[data-testid="stFormSubmitButton"]:hover {
        box-shadow: 0 6px 20px rgba(255,71,87,0.3) !important;
        transform: translateY(-1px) !important;
    }
    .stButton > button:not([kind="primary"]) {
        background: #141820 !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 10px !important;
        color: #F0F2F5 !important; font-weight: 600 !important;
    }
    .stButton > button:not([kind="primary"]):hover {
        background: #1A1F2B !important;
        border-color: rgba(255,255,255,0.2) !important;
    }
    .stDownloadButton > button {
        background: #141820 !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 10px !important;
        color: #F0F2F5 !important;
        font-weight: 600 !important; font-size: 0.8rem !important;
    }
    .stDownloadButton > button:hover {
        background: #1A1F2B !important;
        border-color: #FF4757 !important;
    }

    /* ═══════════════════════════════════
       FORM
       ═══════════════════════════════════ */
    [data-testid="stForm"] {
        background: #141820 !important;
        border: 1px solid rgba(255,255,255,0.06) !important;
        border-radius: 14px !important;
        padding: 20px 24px !important;
    }
    [data-testid="stSelectbox"] label,
    [data-testid="stTextInput"] label {
        font-weight: 500 !important; font-size: 0.78rem !important;
        color: #C9D1D9 !important;
        text-transform: uppercase !important; letter-spacing: 0.04em !important;
    }

    /* ═══════════════════════════════════
       TABS
       ═══════════════════════════════════ */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px; background: #141820;
        border-radius: 10px; padding: 4px;
        border: 1px solid rgba(255,255,255,0.06);
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px; padding: 10px 24px;
        font-weight: 600; font-size: 0.85rem; color: #C9D1D9;
    }
    .stTabs [aria-selected="true"] {
        background: #252B36 !important;
        color: #F0F2F5 !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    }
    .stTabs [data-baseweb="tab-panel"] { padding-top: 16px; }
    .stTabs [data-baseweb="tab-highlight"] {
        background-color: transparent !important;
    }

    /* ═══════════════════════════════════
       PILLS (stButtonGroup) — 다크 강제
       선택 상태는 JS(inject_pills_highlight)로 처리
       ═══════════════════════════════════ */
    .stApp [data-testid="stButtonGroup"] > label,
    .stApp [data-testid="stPills"] > label {
        font-size: 0.78rem !important;
        color: #9BA3B0 !important;
        margin-bottom: 4px !important;
    }
    .stApp [data-testid="stButtonGroup"] button,
    .stApp [data-testid="stPills"] button {
        background-color: #1A1F2B !important;
        color: #C9D1D9 !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 20px !important;
        font-size: 0.8rem !important;
        font-weight: 500 !important;
        padding: 6px 14px !important;
        transition: all 0.2s ease !important;
    }
    .stApp [data-testid="stButtonGroup"] button span,
    .stApp [data-testid="stButtonGroup"] button div,
    .stApp [data-testid="stButtonGroup"] button p,
    .stApp [data-testid="stPills"] button span,
    .stApp [data-testid="stPills"] button div {
        background-color: transparent !important;
        color: inherit !important;
    }
    .stApp [data-testid="stButtonGroup"] button:hover,
    .stApp [data-testid="stPills"] button:hover {
        background-color: #252B36 !important;
        border-color: rgba(255,255,255,0.15) !important;
        color: #F0F2F5 !important;
    }
    .stApp [data-testid="stButtonGroup"] button[aria-pressed="true"],
    .stApp [data-testid="stPills"] button[aria-pressed="true"] {
        background-color: rgba(255,71,87,0.22) !important;
        color: #FF6B81 !important;
        border-color: rgba(255,71,87,0.55) !important;
        font-weight: 700 !important;
        box-shadow: 0 0 0 1px rgba(255,71,87,0.55) !important;
    }
    .stApp [data-testid="stButtonGroup"] button[aria-pressed="true"] span,
    .stApp [data-testid="stButtonGroup"] button[aria-pressed="true"] div,
    .stApp [data-testid="stButtonGroup"] button[aria-pressed="true"] p,
    .stApp [data-testid="stPills"] button[aria-pressed="true"] span,
    .stApp [data-testid="stPills"] button[aria-pressed="true"] div {
        color: #FF6B81 !important;
    }

    /* ═══════════════════════════════════
       기타 STREAMLIT 위젯
       ═══════════════════════════════════ */
    hr { border-color: rgba(255,255,255,0.06) !important; }

    .stDataFrame { border-radius: 12px; overflow: hidden; }
    .stDataFrame [data-testid="stDataFrameResizable"] {
        background: #141820 !important;
    }

    .stMetric {
        background: #141820;
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 12px; padding: 16px;
    }

    /* Spinner */
    .stSpinner > div { color: #C9D1D9 !important; }

    /* Caption */
    .stCaption, [data-testid="stCaption"] { color: #9BA3B0 !important; }

    /* Expander */
    .stExpander {
        background: #141820 !important;
        border: 1px solid rgba(255,255,255,0.06) !important;
        border-radius: 12px !important;
    }
    .stExpander summary { color: #F0F2F5 !important; }

    /* 스크롤바 */
    .stApp ::-webkit-scrollbar { width: 6px; height: 6px; }
    .stApp ::-webkit-scrollbar-track { background: transparent; }
    .stApp ::-webkit-scrollbar-thumb {
        background: rgba(255,255,255,0.12);
        border-radius: 3px;
    }
    .stApp ::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.2); }

    /* 남은 밝은 배경 강제 처리 */
    .stApp [data-baseweb="base-input"],
    .stApp [data-baseweb="input-container"],
    .stApp [data-baseweb="input-enhancer"],
    .stApp [class*="InputContainer"],
    .stApp [class*="BaseInput"] {
        background-color: #0B0E14 !important;
    }
    /* 모든 Streamlit 내부 div 중 흰색 배경 강제 다크 */
    .stApp div[style*="background-color: white"],
    .stApp div[style*="background-color: rgb(255, 255, 255)"],
    .stApp div[style*="background: white"],
    .stApp div[style*="background: rgb(255"] {
        background-color: #0B0E14 !important;
    }
    /* 토스트 알림 */
    [data-testid="stToast"] div,
    [data-testid="stToast"] p,
    [data-testid="stToast"] span {
        color: #F0F2F5 !important;
    }

    /* ═══════════════════════════════════
       ANIMATIONS
       ═══════════════════════════════════ */
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .vgrid { animation: fadeInUp 0.3s ease forwards; }
    .metric-card { animation: fadeInUp 0.25s ease forwards; }

    /* ═══════════════════════════════════
       MOBILE
       ═══════════════════════════════════ */
    @media (max-width: 768px) {
        .page-header { padding: 20px; }
        .page-header h1 { font-size: 1.25rem; }
        .metric-card .metric-value { font-size: 1.25rem; }
        .vgrid .vg-body { padding: 12px 14px; }
    }
    </style>
    """, unsafe_allow_html=True)

    # 항상 동일한 수의 st.markdown 호출을 유지해야 탭 상태가 보존됨
    is_light = st.session_state.get("_theme_pref", False) or st.session_state.get("theme_light", False)
    if is_light:
        _inject_light_overrides()
    else:
        st.markdown("<style>/* dark-mode-active */</style>", unsafe_allow_html=True)

    # Streamlit Cloud 배지 제거 + 모바일 사이드바 자동 닫기
    import streamlit.components.v1 as _components
    _components.html("""
    <script>
    (function(){
        var doc = window.parent.document;
        var w = window.parent;

        // 0) localStorage 토큰 동기화 (보조 — 메인 복원은 서버사이드)
        try {
            var _urlTk = new URLSearchParams(w.location.search).get('t');
            if (_urlTk === '_out') {
                w.localStorage.removeItem('_yt_auth');
            } else if (_urlTk) {
                w.localStorage.setItem('_yt_auth', _urlTk);
            }
        } catch(e) {}

        // 1) parent document에 CSS 주입 (페이지 전환에도 유지됨)
        if (!doc.getElementById('_yt_injected_css')) {
            var style = doc.createElement('style');
            style.id = '_yt_injected_css';
            style.textContent = [
                '[data-testid="stSidebarNav"] { display:none!important; }',
                'a[href*="streamlit.io"] { display:none!important; }',
                'a[href*="streamlit.app"]:not(.stApp a) { display:none!important; }',
                '[data-testid="manage-app-button"] { display:none!important; }',
                'footer { display:none!important; }',
                'div[class*="viewerBadge"] { display:none!important; }',
                'div[class*="HostButton"] { display:none!important; }',
                '#MainMenu { display:none!important; }',
                '[data-testid="stMainMenu"] { display:none!important; }',
            ].join('\\n');
            doc.head.appendChild(style);
        }

        // 1-b) stSidebarNav 제거 + 사이드바 상단 빈 공간 제거
        function cleanSidebar() {
            var nav = doc.querySelector('[data-testid="stSidebarNav"]');
            if (nav) nav.remove();
            var sep = doc.querySelector('[data-testid="stSidebarNavSeparator"]');
            if (sep) sep.remove();
            // 사이드바 내부 첫 번째 빈 div 제거 (Streamlit 내부 스페이서)
            var sidebar = doc.querySelector('section[data-testid="stSidebar"] > div');
            if (sidebar) {
                var first = sidebar.firstElementChild;
                if (first && !first.textContent.trim() && !first.querySelector('input,button,a')) {
                    first.style.display = 'none';
                }
            }
        }
        cleanSidebar();
        if (!w._ytNavObserver) {
            w._ytNavObserver = new MutationObserver(cleanSidebar);
            w._ytNavObserver.observe(doc.body, {childList: true, subtree: true});
        }

        // 2) 하단 fixed 배지 제거 함수
        function removeBadges(){
            doc.querySelectorAll('body > div, body > a, body > section, body > aside').forEach(function(el){
                if(el.querySelector('.stApp')) return;
                var s = w.getComputedStyle(el);
                if(s.position==='fixed' || s.position==='absolute'){
                    var b = parseInt(s.bottom||'999');
                    var r = parseInt(s.right||'999');
                    if(b < 120 && r < 200){
                        el.remove();
                    }
                }
            });
            doc.querySelectorAll('img[src*="streamlit"], a[href*="streamlit.io"]').forEach(function(el){
                var p = el.closest('div,a,section');
                if(p && !p.closest('.stApp')) p.remove();
            });
        }

        // 3) MutationObserver — 동적 삽입 감시
        removeBadges();
        var observer = new MutationObserver(function(){ removeBadges(); });
        observer.observe(doc.body, { childList: true, subtree: true });
        setTimeout(function(){ observer.disconnect(); }, 10000);

        // 4) 모바일 사이드바 자동 닫기
        function _removeSidebarHide() {
            sessionStorage.removeItem('_yt_close_sidebar');
            var el = doc.getElementById('_yt_hide_sidebar');
            if (el) el.remove();
        }

        if (w.innerWidth <= 768) {
            var _flag = sessionStorage.getItem('_yt_close_sidebar');
            if (_flag) {
                var _elapsed = Date.now() - (parseInt(_flag) || 0);
                if (_elapsed < 3000) {
                    // (a) CSS로 사이드바 즉시 숨김 (깜빡임 방지)
                    if (!doc.getElementById('_yt_hide_sidebar')) {
                        var _s = doc.createElement('style');
                        _s.id = '_yt_hide_sidebar';
                        _s.textContent = 'section[data-testid="stSidebar"]{transform:translateX(-100%)!important;transition:none!important;}';
                        doc.head.appendChild(_s);
                    }
                    // (b) 닫기 버튼 클릭
                    function _clickClose() {
                        var btn = doc.querySelector('[data-testid="stSidebarCollapseButton"] button') ||
                                  doc.querySelector('[data-testid="stSidebarNavCollapseButton"] button');
                        if (btn) { btn.click(); _removeSidebarHide(); return true; }
                        return false;
                    }
                    setTimeout(_clickClose, 150);
                    setTimeout(function(){ if(!_clickClose()) setTimeout(_clickClose, 500); }, 600);
                    // 안전장치: 1.5초 후 CSS 강제 제거 (메뉴 재오픈 차단 방지)
                    setTimeout(_removeSidebarHide, 1500);
                } else {
                    _removeSidebarHide();
                }
            }

            // 사이드바 열기 버튼 클릭 시 hide CSS 제거 (잔존 차단 방지)
            function _guardOpenBtn() {
                var openBtn = doc.querySelector('[data-testid="stSidebarCollapsedControl"] button') ||
                              doc.querySelector('[data-testid="collapsedControl"] button');
                if (openBtn && !openBtn._ytGuard) {
                    openBtn._ytGuard = true;
                    openBtn.addEventListener('click', _removeSidebarHide);
                }
            }
            setTimeout(_guardOpenBtn, 300);
            setTimeout(_guardOpenBtn, 1000);

            // 사이드바 링크 클릭 시 → CSS 즉시 삽입 + 플래그 설정
            function setupAutoClose() {
                var sidebar = doc.querySelector('section[data-testid="stSidebar"]');
                if (!sidebar) return;
                sidebar.querySelectorAll('.stPageLink a').forEach(function(link) {
                    if (link._ytAutoClose) return;
                    link._ytAutoClose = true;
                    link.addEventListener('click', function() {
                        sessionStorage.setItem('_yt_close_sidebar', Date.now().toString());
                        if (!doc.getElementById('_yt_hide_sidebar')) {
                            var s = doc.createElement('style');
                            s.id = '_yt_hide_sidebar';
                            s.textContent = 'section[data-testid="stSidebar"]{transform:translateX(-100%)!important;transition:none!important;}';
                            doc.head.appendChild(s);
                        }
                    });
                });
            }
            setTimeout(setupAutoClose, 300);
            setTimeout(setupAutoClose, 800);
        }
    })();
    </script>
    """, height=0, scrolling=False)


def _inject_light_overrides():
    """라이트 모드: 다크 CSS 위에 색상만 오버라이드"""
    st.markdown("""
    <style>
    /* ═══ LIGHT MODE OVERRIDES ═══ */
    html, body, [data-testid="stAppViewContainer"],
    .stApp, .main, .block-container {
        background-color: #FAFBFC !important;
        color: #24292F !important;
    }
    /* 사이드바 토글 버튼 — 라이트 모드 */
    [data-testid="stSidebarCollapsedControl"] button,
    [data-testid="collapsedControl"] button,
    button[data-testid="baseButton-headerNoPadding"] {
        background: rgba(0,0,0,0.04) !important;
        border-color: rgba(0,0,0,0.12) !important;
    }
    [data-testid="stSidebarCollapsedControl"] button::after,
    [data-testid="collapsedControl"] button::after,
    button[data-testid="baseButton-headerNoPadding"]::after {
        color: #24292F !important;
    }

    /* 사이드바 라이트 모드 */
    section[data-testid="stSidebar"] {
        background: #F6F8FA !important;
        border-right-color: rgba(0,0,0,0.08) !important;
    }
    section[data-testid="stSidebar"] > div:first-child {
        padding-top: 0.5rem !important;
    }
    section[data-testid="stSidebar"] hr { border-color: rgba(0,0,0,0.08) !important; }
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] div,
    section[data-testid="stSidebar"] .stMarkdown,
    section[data-testid="stSidebar"] .stMarkdown p { color: #24292F !important; }
    section[data-testid="stSidebar"] [data-testid="stToggle"] label span,
    section[data-testid="stSidebar"] .stToggle label span { color: #24292F !important; }
    section[data-testid="stSidebar"] [data-testid="stCaption"],
    section[data-testid="stSidebar"] .stCaption { color: #656D76 !important; }
    section[data-testid="stSidebar"] .stPageLink a { color: #656D76 !important; }
    section[data-testid="stSidebar"] .stPageLink a:hover,
    section[data-testid="stSidebar"] .stPageLink a[aria-current="page"] {
        background: #ECEEF0 !important;
        color: #24292F !important;
    }

    .page-header {
        background: linear-gradient(135deg, #F6F8FA 0%, #ECEEF0 50%, #F0EEF5 100%) !important;
        border-color: rgba(0,0,0,0.08) !important;
    }
    .page-header::before {
        background: radial-gradient(ellipse at top right, rgba(255,71,87,0.04) 0%, transparent 70%) !important;
    }
    .page-header h1 { color: #24292F !important; }
    .page-header .subtitle { color: #656D76 !important; }

    .metric-card {
        background: #FFFFFF !important;
        border-color: rgba(0,0,0,0.08) !important;
    }
    .metric-card:hover {
        border-color: rgba(0,0,0,0.15) !important;
        box-shadow: 0 8px 24px rgba(0,0,0,0.06) !important;
    }
    .metric-card .metric-label { color: #656D76 !important; }
    .metric-card .metric-value { color: #24292F !important; }
    .metric-card .metric-hint { color: #57606A !important; }

    .section-title { color: #57606A !important; }

    .vgrid {
        background: #FFFFFF !important;
        border-color: rgba(0,0,0,0.08) !important;
    }
    .vgrid:hover {
        border-color: rgba(0,0,0,0.15) !important;
        box-shadow: 0 12px 32px rgba(0,0,0,0.08) !important;
    }
    .vgrid .vg-thumb { background: #F6F8FA !important; }
    .vgrid .vg-title { color: #24292F !important; }
    .vgrid .vg-channel { color: #656D76 !important; }
    .vgrid .vg-stats { border-top-color: rgba(0,0,0,0.06) !important; }
    .vgrid .vg-stat { color: #656D76 !important; }
    .vgrid .vg-stat strong { color: #24292F !important; }

    .empty-state {
        background: #FFFFFF !important;
        border-color: rgba(0,0,0,0.1) !important;
    }
    .empty-state .title { color: #24292F !important; }
    .empty-state .desc { color: #656D76 !important; }

    .insight-box {
        background: #FFFFFF !important;
        border-color: rgba(0,0,0,0.06) !important;
        color: #656D76 !important;
    }
    .insight-box strong { color: #24292F !important; }

    .freshness-bar {
        background: #FFFFFF !important;
        border-color: rgba(0,0,0,0.08) !important;
        color: #656D76 !important;
    }
    .freshness-bar .freshness-time { color: #24292F !important; }
    .freshness-bar .freshness-hint { color: #9CA3AF !important; }

    .keyword-card {
        background: #FFFFFF !important;
        border-color: rgba(0,0,0,0.08) !important;
    }
    .keyword-card:hover { border-color: rgba(0,0,0,0.15) !important; box-shadow: 0 8px 24px rgba(0,0,0,0.06) !important; }
    .keyword-card .kw-name { color: #24292F !important; }
    .keyword-card .kw-news { color: #9CA3AF !important; }
    .keyword-card .kw-news span { color: #656D76 !important; }

    .gap-card { background: #FFFFFF !important; border-color: rgba(0,0,0,0.08) !important; }
    .gap-card .gap-keyword { color: #24292F !important; }
    .gap-card .gap-meta { color: #9CA3AF !important; }
    .gap-card .gap-meta strong { color: #24292F !important; }
    .gap-bar-wrap { background: rgba(0,0,0,0.06) !important; }

    .season-week-label { color: #24292F !important; }
    .season-tag { background: #F6F8FA !important; border-color: rgba(0,0,0,0.08) !important; color: #656D76 !important; }

    .filter-info {
        background: rgba(76,154,255,0.06) !important;
        border-color: rgba(76,154,255,0.12) !important;
    }

    /* Forms */
    .stApp input[type="text"],
    .stApp input[type="number"],
    .stApp input[type="search"],
    .stApp input[type="email"],
    .stApp input[type="password"],
    .stApp input:not([type]),
    .stTextInput input, .stNumberInput input,
    [data-testid="stTextInput"] input,
    [data-testid="stNumberInput"] input,
    [data-baseweb="input"] input {
        background-color: #FFFFFF !important;
        color: #24292F !important;
        -webkit-text-fill-color: #24292F !important;
        border-color: rgba(0,0,0,0.12) !important;
    }
    [data-baseweb="input"], [data-baseweb="input"] > div,
    .stTextInput > div > div,
    [data-testid="stTextInput"] > div > div {
        background-color: #FFFFFF !important;
        border-color: rgba(0,0,0,0.12) !important;
    }
    /* 라이트 모드 autofill */
    .stApp input:-webkit-autofill,
    .stApp input:-webkit-autofill:hover,
    .stApp input:-webkit-autofill:focus,
    .stApp input:-webkit-autofill:active {
        -webkit-box-shadow: 0 0 0 30px #FFFFFF inset !important;
        -webkit-text-fill-color: #24292F !important;
        box-shadow: 0 0 0 30px #FFFFFF inset !important;
        transition: background-color 5000s ease-in-out 0s !important;
    }
    .stApp input::placeholder, .stApp textarea::placeholder {
        color: #9CA3AF !important;
        -webkit-text-fill-color: #9CA3AF !important;
    }
    .stApp textarea, .stTextArea textarea,
    [data-baseweb="textarea"], [data-baseweb="textarea"] textarea {
        background-color: #FFFFFF !important;
        color: #24292F !important;
        -webkit-text-fill-color: #24292F !important;
        border-color: rgba(0,0,0,0.12) !important;
    }
    .stSelectbox > div > div,
    .stSelectbox [data-baseweb="select"] > div,
    [data-testid="stSelectbox"] > div > div,
    [data-testid="stSelectbox"] [data-baseweb="select"] > div,
    [data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        border-color: rgba(0,0,0,0.12) !important;
        color: #24292F !important;
    }
    [data-baseweb="select"] > div > div,
    [data-baseweb="select"] span,
    .stSelectbox [data-baseweb="select"] span { color: #24292F !important; }
    [data-baseweb="select"] svg { fill: #656D76 !important; }

    /* Dropdowns */
    [data-baseweb="popover"], [data-baseweb="popover"] > div,
    [data-baseweb="popover"] > div > div {
        background-color: #FFFFFF !important;
        border-color: rgba(0,0,0,0.08) !important;
        box-shadow: 0 12px 40px rgba(0,0,0,0.1) !important;
    }
    [data-baseweb="menu"], [data-baseweb="menu"] > div,
    [data-baseweb="menu"] ul, ul[role="listbox"] {
        background-color: #FFFFFF !important;
    }
    [data-baseweb="menu"] [role="option"],
    ul[role="listbox"] [role="option"],
    [data-baseweb="menu"] li, ul[role="listbox"] li {
        color: #24292F !important;
        background-color: transparent !important;
    }
    [data-baseweb="menu"] [role="option"]:hover,
    ul[role="listbox"] [role="option"]:hover,
    [data-baseweb="menu"] li:hover, ul[role="listbox"] li:hover {
        background-color: #F6F8FA !important;
    }

    /* Alerts & Toast */
    .stAlert, .stAlert > div,
    [data-baseweb="notification"], [data-baseweb="notification"] > div {
        background-color: transparent !important;
        color: #57606A !important;
    }
    .stAlert p, .stAlert span,
    [data-baseweb="notification"] p, [data-baseweb="notification"] span { color: #57606A !important; }
    [data-testid="stToast"], [data-testid="stToast"] > div {
        background-color: #FFFFFF !important;
        border-color: rgba(0,0,0,0.08) !important;
        color: #24292F !important;
    }
    [data-testid="stToast"] div, [data-testid="stToast"] p,
    [data-testid="stToast"] span { color: #24292F !important; }

    /* Buttons - secondary */
    .stButton > button:not([kind="primary"]) {
        background: #FFFFFF !important;
        border-color: rgba(0,0,0,0.12) !important;
        color: #24292F !important;
    }
    .stButton > button:not([kind="primary"]):hover {
        background: #F6F8FA !important;
        border-color: rgba(0,0,0,0.2) !important;
    }
    .stDownloadButton > button {
        background: #FFFFFF !important;
        border-color: rgba(0,0,0,0.12) !important;
        color: #24292F !important;
    }
    .stDownloadButton > button:hover { background: #F6F8FA !important; }

    /* Form container */
    [data-testid="stForm"] {
        background: #FFFFFF !important;
        border-color: rgba(0,0,0,0.08) !important;
    }
    [data-testid="stSelectbox"] label,
    [data-testid="stTextInput"] label { color: #656D76 !important; }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: #F6F8FA !important;
        border-color: rgba(0,0,0,0.06) !important;
    }
    .stTabs [data-baseweb="tab"] { color: #656D76 !important; }
    .stTabs [aria-selected="true"] {
        background: #FFFFFF !important;
        color: #24292F !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06) !important;
    }

    /* Pills — 라이트 모드 강제, 선택 상태는 JS(inject_pills_highlight)로 처리 */
    .stApp [data-testid="stButtonGroup"] > label,
    .stApp [data-testid="stPills"] > label { color: #656D76 !important; }
    .stApp [data-testid="stButtonGroup"] button,
    .stApp [data-testid="stPills"] button {
        background-color: #F6F8FA !important;
        color: #656D76 !important;
        border-color: rgba(0,0,0,0.08) !important;
    }
    .stApp [data-testid="stButtonGroup"] button span,
    .stApp [data-testid="stButtonGroup"] button div,
    .stApp [data-testid="stPills"] button span,
    .stApp [data-testid="stPills"] button div {
        background-color: transparent !important;
        color: inherit !important;
    }
    .stApp [data-testid="stButtonGroup"] button:hover,
    .stApp [data-testid="stPills"] button:hover {
        background-color: #ECEEF0 !important;
        border-color: rgba(0,0,0,0.15) !important;
        color: #24292F !important;
    }
    .stApp [data-testid="stButtonGroup"] button[aria-pressed="true"],
    .stApp [data-testid="stPills"] button[aria-pressed="true"] {
        background-color: rgba(255,71,87,0.12) !important;
        color: #E8384F !important;
        border-color: rgba(255,71,87,0.35) !important;
        font-weight: 700 !important;
        box-shadow: 0 0 0 1px rgba(255,71,87,0.35) !important;
    }
    .stApp [data-testid="stButtonGroup"] button[aria-pressed="true"] span,
    .stApp [data-testid="stButtonGroup"] button[aria-pressed="true"] div,
    .stApp [data-testid="stPills"] button[aria-pressed="true"] span,
    .stApp [data-testid="stPills"] button[aria-pressed="true"] div {
        color: #E8384F !important;
    }

    /* DataFrame, Metric, Expander */
    .stDataFrame [data-testid="stDataFrameResizable"] { background: #FFFFFF !important; }
    .stMetric { background: #FFFFFF !important; border-color: rgba(0,0,0,0.06) !important; }
    .stCaption, [data-testid="stCaption"] { color: #656D76 !important; }
    .stExpander { background: #FFFFFF !important; border-color: rgba(0,0,0,0.06) !important; }
    .stExpander summary { color: #24292F !important; }

    /* Scrollbar */
    .stApp ::-webkit-scrollbar-thumb { background: rgba(0,0,0,0.12) !important; }
    .stApp ::-webkit-scrollbar-thumb:hover { background: rgba(0,0,0,0.2) !important; }

    /* BaseUI catch-all */
    .stApp [data-baseweb="base-input"],
    .stApp [data-baseweb="input-container"],
    .stApp [data-baseweb="input-enhancer"],
    .stApp [class*="InputContainer"],
    .stApp [class*="BaseInput"] { background-color: #FFFFFF !important; }

    /* Spinner */
    .stSpinner > div { color: #656D76 !important; }
    </style>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════
# 렌더링 함수
# ═══════════════════════════════════

def render_page_header(title: str, subtitle: str = "") -> None:
    sub_html = (
        f'<div class="subtitle">{html_lib.escape(subtitle)}</div>'
        if subtitle else ""
    )
    st.markdown(
        f'<div class="page-header"><h1>{html_lib.escape(title)}</h1>{sub_html}</div>',
        unsafe_allow_html=True,
    )


def render_metric_card(value: str, label: str, color: str = "blue",
                       hint: str = "") -> str:
    c = color if color in _CARD_COLORS else "blue"
    hint_html = f'<div class="metric-hint">{html_lib.escape(hint)}</div>' if hint else ""
    return (
        f'<div class="metric-card {c}">'
        f'<div class="metric-label">{html_lib.escape(label)}</div>'
        f'<div class="metric-value">{html_lib.escape(str(value))}</div>'
        f'{hint_html}'
        f'</div>'
    )


def render_section_title(title: str) -> None:
    st.markdown(
        f'<div class="section-title">{html_lib.escape(title)}</div>',
        unsafe_allow_html=True,
    )


def render_video_grid_card(video: dict, rank_field: str = "trending_rank") -> None:
    from src.analysis.performance import format_count, stars_display

    rank = video.get(rank_field, "")
    rank_cls = "vg-rank top3" if isinstance(rank, int) and rank <= 3 else "vg-rank"
    title = html_lib.escape(video.get("title", ""))
    channel = html_lib.escape(video.get("channel_title", ""))
    video_id = video.get("video_id", "")
    url = f"https://www.youtube.com/watch?v={html_lib.escape(video_id)}"
    from src.utils import validate_thumbnail_url
    thumb = validate_thumbnail_url(video.get("thumbnail_url", ""))
    views = format_count(video.get("view_count", 0))
    subs = format_count(video.get("subscriber_count", 0))
    stars = stars_display(video.get("performance_stars", 1))

    thumb_html = f'<img src="{thumb}" alt="" loading="lazy">' if thumb else ""

    st.markdown(f'''
    <div class="vgrid">
        <a class="vg-thumb" href="{url}" target="_blank" style="display:block;text-decoration:none;">
            {thumb_html}
            <span class="{rank_cls}">#{rank}</span>
        </a>
        <div class="vg-body">
            <a class="vg-title" href="{url}" target="_blank">{title}</a>
            <div class="vg-channel">{channel}</div>
            <div class="vg-stats">
                <span class="vg-stat"><strong>{views}</strong> 조회</span>
                <span class="vg-stat"><strong>{subs}</strong> 구독</span>
                <span class="vg-stars" title="구독자 대비 조회수 성과 (1~5점)">{stars}</span>
            </div>
        </div>
    </div>
    ''', unsafe_allow_html=True)


def render_video_grid(videos: list, rank_field: str = "trending_rank",
                      cols: int = 2) -> None:
    for i in range(0, len(videos), cols):
        columns = st.columns(cols)
        for j in range(cols):
            if i + j < len(videos):
                with columns[j]:
                    render_video_grid_card(videos[i + j], rank_field=rank_field)


def render_empty_state(title: str, description: str) -> None:
    st.markdown(f'''
    <div class="empty-state">
        <div class="title">{html_lib.escape(title)}</div>
        <div class="desc">{html_lib.escape(description)}</div>
    </div>
    ''', unsafe_allow_html=True)


def render_insight_box(text: str) -> None:
    st.markdown(f'<div class="insight-box">{text}</div>', unsafe_allow_html=True)


def render_freshness_bar(collected_at: str) -> None:
    """수집 시각 경과에 따른 신선도 바 렌더링."""
    from datetime import datetime
    from src.config import KST

    if not collected_at:
        return

    try:
        parsed = datetime.fromisoformat(collected_at.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            # naive datetime → 로컬 서버 시간으로 간주하여 KST 부여
            parsed = parsed.replace(tzinfo=KST)
        kst_time = parsed.astimezone(KST)
    except Exception:
        return

    now = datetime.now(KST)
    delta = now - kst_time
    minutes = int(delta.total_seconds() / 60)

    time_str = kst_time.strftime("%Y-%m-%d %H:%M")

    if minutes < 5:
        status, label, hint = "fresh", "방금 수집", ""
    elif minutes < 60:
        status, label, hint = "fresh", f"{minutes}분 전 수집", ""
    elif minutes < 240:
        hours = minutes // 60
        status = "stale"
        label = f"{hours}시간 전 수집"
        hint = "새로고침을 눌러 최신 데이터를 가져오세요"
    else:
        hours = minutes // 60
        status = "old"
        label = f"{hours}시간 전 수집"
        hint = "데이터가 오래되었어요. 새로고침을 권장합니다"

    icon = {"fresh": "●", "stale": "●", "old": "●"}[status]
    hint_html = f'<span class="freshness-hint">{html_lib.escape(hint)}</span>' if hint else ""

    st.markdown(
        f'<div class="freshness-bar {status}">'
        f'<span class="freshness-icon">{icon}</span>'
        f'<span class="freshness-time">{html_lib.escape(label)}</span>'
        f'<span>{html_lib.escape(time_str)}</span>'
        f'{hint_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_filter_info(count: int, total: int) -> None:
    st.markdown(
        f'<div class="filter-info">전체 {total}개 중 {count}개 영상이 선택됐어요</div>',
        unsafe_allow_html=True,
    )


def render_action_bar(count: int, keyword: str = "") -> None:
    label = f'"{html_lib.escape(keyword)}" 검색 결과' if keyword else "트렌드 영상"
    st.markdown(
        f'<div class="action-bar">'
        f'<span class="count">{label} <strong>{count}개</strong></span>'
        f'</div>',
        unsafe_allow_html=True,
    )


def build_category_pills(videos: list):
    """영상 목록에서 카테고리별 개수를 세어 pills 라벨 목록을 반환."""
    from collections import Counter
    cat_counter = Counter(v.get("category_name", "기타") for v in videos)
    items = cat_counter.most_common()
    labels = [f"{cat} ({cnt})" for cat, cnt in items]
    cat_map = {f"{cat} ({cnt})": cat for cat, cnt in items}
    return labels, cat_map


def filter_videos_by_category(videos: list, selected_labels: list,
                              cat_map: dict) -> list:
    if not selected_labels:
        return videos
    selected_cats = {cat_map.get(l, l) for l in selected_labels}
    return [v for v in videos if v.get("category_name", "기타") in selected_cats]


def inject_pills_highlight(selected_labels=None, group_index=0) -> None:
    """선택된 pill 버튼에 하이라이트 스타일 적용 (st.components.v1.html 사용).

    CSS만으로는 Streamlit BaseUI(Styletron)의 선택 상태를 오버라이드할 수 없으므로,
    iframe 내 JS에서 parent document에 접근하여 인라인 스타일을 적용한다.
    group_index: 페이지 내 N번째 stButtonGroup만 대상 (탭 간 간섭 방지)
    """
    import json as _json
    import streamlit.components.v1 as components

    is_light = (
        st.session_state.get("_theme_pref", False)
        or st.session_state.get("theme_light", False)
    )

    if is_light:
        bg, fg, bc = (
            "rgba(255,71,87,0.12)", "#E8384F", "rgba(255,71,87,0.35)",
        )
        reset_bg, reset_fg, reset_bc = (
            "#F6F8FA", "#656D76", "rgba(0,0,0,0.08)",
        )
    else:
        bg, fg, bc = (
            "rgba(255,71,87,0.22)", "#FF6B81", "rgba(255,71,87,0.55)",
        )
        reset_bg, reset_fg, reset_bc = (
            "#1A1F2B", "#C9D1D9", "rgba(255,255,255,0.08)",
        )

    sel_json = _json.dumps(list(selected_labels)) if selected_labels else "[]"

    js_code = f"""
    <script>
    (function() {{
        var S = new Set({sel_json});
        var BG = '{bg}', FG = '{fg}', BC = '{bc}';
        var RBG = '{reset_bg}', RFG = '{reset_fg}', RBC = '{reset_bc}';
        var GI = {group_index};

        function apply() {{
            var doc = window.parent.document;
            var groups = doc.querySelectorAll('[data-testid="stButtonGroup"], [data-testid="stPills"]');
            var g = groups[GI];
            if (!g) return;
            g.querySelectorAll('button').forEach(function(b) {{
                var t = b.textContent.trim();
                if (S.has(t)) {{
                    b.style.setProperty('background-color', BG, 'important');
                    b.style.setProperty('color', FG, 'important');
                    b.style.setProperty('border-color', BC, 'important');
                    b.style.setProperty('font-weight', '700', 'important');
                    b.style.setProperty('box-shadow', '0 0 0 1px ' + BC, 'important');
                    b.querySelectorAll('span,div,p').forEach(function(e) {{
                        e.style.setProperty('color', FG, 'important');
                        e.style.setProperty('background-color', 'transparent', 'important');
                    }});
                }} else {{
                    b.style.setProperty('background-color', RBG, 'important');
                    b.style.setProperty('color', RFG, 'important');
                    b.style.setProperty('border-color', RBC, 'important');
                    b.style.setProperty('font-weight', '500', 'important');
                    b.style.removeProperty('box-shadow');
                    b.querySelectorAll('span,div,p').forEach(function(e) {{
                        e.style.setProperty('color', 'inherit', 'important');
                        e.style.setProperty('background-color', 'transparent', 'important');
                    }});
                }}
            }});
        }}
        setTimeout(apply, 80);
        setTimeout(apply, 300);
        setTimeout(apply, 700);
    }})();
    </script>
    """
    components.html(js_code, height=0, scrolling=False)


def sidebar_with_badges(repo, current_page: str = "dashboard"):
    """사이드바 네비게이션 렌더링."""
    if "_theme_pref" not in st.session_state:
        st.session_state["_theme_pref"] = False

    with st.sidebar:
        st.markdown(
            '<div style="display:flex;align-items:center;gap:10px;padding:8px 0 12px;">'
            '<span style="font-weight:900;font-size:1.2rem;color:#FF4757;">YT</span>'
            '<span style="font-weight:700;font-size:0.95rem;">토픽 파인더</span>'
            '</div>',
            unsafe_allow_html=True,
        )

        st.page_link("app.py", label="트렌드 대시보드")
        st.page_link("pages/1_search.py", label="키워드 검색")
        st.page_link("pages/3_ideas.py", label="콘텐츠 아이디어")
        st.page_link("pages/2_settings.py", label="설정")

        st.divider()

        def _sync_theme():
            st.session_state["_theme_pref"] = st.session_state["theme_light"]

        st.toggle(
            "라이트 모드",
            value=st.session_state["_theme_pref"],
            key="theme_light",
            on_change=_sync_theme,
        )

        if st.session_state.get("authenticated"):
            if st.button("로그아웃", use_container_width=True):
                st.session_state["authenticated"] = False
                st.session_state.pop("_token_synced", None)
                st.query_params["t"] = "_out"
                st.rerun()

        st.divider()
        st.caption("YouTube 트렌드 분석 도구")

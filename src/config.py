"""환경 설정 중앙화"""
import os
from datetime import timezone, timedelta
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


def _get_secret(key: str, default: str = "") -> str:
    """환경변수 → st.secrets 순으로 조회."""
    val = os.environ.get(key, "")
    if val:
        return val
    try:
        import streamlit as st
        return st.secrets.get(key, default)
    except Exception:
        return default


# 경로
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "youtube_trends.db"

# YouTube API
YOUTUBE_API_KEY = _get_secret("YOUTUBE_API_KEY")
YOUTUBE_REGION_CODE = "KR"
YOUTUBE_LANGUAGE = "ko"
YOUTUBE_DAILY_QUOTA = 10000
KST = timezone(timedelta(hours=9))  # 한국 표준시

# 이메일 (SMTP)
SMTP_SERVER = _get_secret("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(_get_secret("SMTP_PORT", "587"))
SENDER_EMAIL = _get_secret("SENDER_EMAIL")
SENDER_PASSWORD = _get_secret("SENDER_PASSWORD")
RECIPIENT_EMAIL = _get_secret("RECIPIENT_EMAIL")

# 텔레그램
TELEGRAM_BOT_TOKEN = _get_secret("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = _get_secret("TELEGRAM_CHAT_ID")

# 알림 채널 (콤마 구분: email,telegram,kakao)
NOTIFICATION_CHANNELS = _get_secret("NOTIFICATION_CHANNELS", "email").split(",")

# 성과 별점 기준 (조회수/구독자 비율)
PERFORMANCE_THRESHOLDS = {
    5: 50,   # ⭐⭐⭐⭐⭐: 구독자의 50배 이상
    4: 10,   # ⭐⭐⭐⭐: 10배 이상
    3: 2,    # ⭐⭐⭐: 2배 이상
    2: 0.5,  # ⭐⭐: 절반 이상
    1: 0,    # ⭐: 그 외
}

# ── PRO 업그레이드 설정 ──

# Google Trends
GOOGLE_TRENDS_REGION = "KR"
BREAKOUT_THRESHOLD_PCT = 500.0  # 브레이크아웃 키워드 감지 기준 (%)

# 경쟁 채널 추적
MAX_TRACKED_CHANNELS = 20
COMPETITOR_CHECK_INTERVAL_HOURS = 6

# 트렌드 속도
VELOCITY_THRESHOLDS = {
    "급상승": {"acceleration_min": 30, "vph_min": 10000},
    "상승":   {"acceleration_min": 10, "vph_min": 5000},
    "안정":   {"acceleration_min": -10},
    "하락":   {"acceleration_max": -10},
}

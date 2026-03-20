"""텔레그램 봇 알림"""
import logging
import requests

from src.analysis.performance import format_count
from src.analysis.tag_analyzer import analyze_tags
from src.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from src.utils import sanitize_html

logger = logging.getLogger(__name__)


def send_telegram_report(videos: list[dict]) -> bool:
    """텔레그램으로 트렌드 요약 발송"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("텔레그램 설정 없음 - 건너뜁니다")
        return False

    # 태그 빈도
    tag_freq = analyze_tags(videos)
    tags_text = " ".join(f"#{sanitize_html(tag)}({count})" for tag, count in tag_freq[:10])

    # TOP 5 영상
    top5 = ""
    for i, v in enumerate(videos[:5], 1):
        views = format_count(v.get("view_count", 0))
        video_id = sanitize_html(v.get("video_id", ""))
        url = f'https://www.youtube.com/watch?v={video_id}'
        title = sanitize_html(v.get("title", "")[:40])
        top5 += f'{i}. <a href="{url}">{title}</a> - {views}\n'

    text = (
        f"📊 <b>YouTube 트렌드 알림</b>\n\n"
        f"🏷 <b>트렌드 키워드:</b>\n{tags_text}\n\n"
        f"🔥 <b>TOP 5:</b>\n{top5}"
    )

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        resp = requests.post(url, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
        }, timeout=10)
        if resp.status_code == 200:
            logger.info("텔레그램 발송 완료")
            return True
        logger.error(f"텔레그램 발송 실패: {resp.text}")
        return False
    except Exception as e:
        logger.error(f"텔레그램 발송 오류: {e}")
        return False

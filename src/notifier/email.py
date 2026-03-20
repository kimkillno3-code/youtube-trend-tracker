"""이메일 알림 - HTML 트렌드 리포트 발송"""
import logging
import smtplib
import uuid
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from src.analysis.performance import format_count, stars_display
from src.analysis.tag_analyzer import analyze_tags
from src.config import SMTP_SERVER, SMTP_PORT, SENDER_EMAIL, SENDER_PASSWORD, RECIPIENT_EMAIL
from src.utils import sanitize_html, validate_thumbnail_url

logger = logging.getLogger(__name__)


def _build_html_report(videos: list[dict], tag_freq: list[tuple[str, int]]) -> str:
    """HTML 트렌드 리포트 생성"""
    now = datetime.now().strftime("%Y.%m.%d %H:%M")
    hour = datetime.now().hour
    time_label = "아침" if hour < 12 else "오후" if hour < 18 else "저녁"

    # 태그 뱃지
    tag_badges = ""
    for tag, count in tag_freq[:15]:
        tag_badges += (
            f'<span style="display:inline-block;background:#ff6b6b;color:#fff;'
            f'padding:4px 10px;border-radius:12px;margin:3px;font-size:13px;">'
            f'{sanitize_html(tag)} ({count})</span>'
        )

    # 영상 테이블 행
    rows = ""
    for v in videos[:30]:
        stars = stars_display(v.get("performance_stars", 1))
        views = format_count(v.get("view_count", 0))
        subs = format_count(v.get("subscriber_count", 0))
        title = sanitize_html(v.get("title", "")[:60])
        channel = sanitize_html(v.get("channel_title", ""))
        video_id = sanitize_html(v.get("video_id", ""))
        url = f'https://www.youtube.com/watch?v={video_id}'
        thumb = validate_thumbnail_url(v.get("thumbnail_url", ""))
        thumb_html = f'<img src="{thumb}" width="120" style="border-radius:4px;">' if thumb else ""

        rows += f"""
        <tr style="border-bottom:1px solid #eee;">
            <td style="padding:8px;text-align:center;font-weight:bold;">{v.get('trending_rank', v.get('search_rank', ''))}</td>
            <td style="padding:8px;">{thumb_html}</td>
            <td style="padding:8px;"><a href="{url}" style="color:#1a73e8;text-decoration:none;">{title}</a></td>
            <td style="padding:8px;">{channel}</td>
            <td style="padding:8px;text-align:right;font-weight:bold;">{views}</td>
            <td style="padding:8px;text-align:right;">{subs}</td>
            <td style="padding:8px;text-align:center;">{stars}</td>
        </tr>"""

    return f"""
    <html>
    <body style="font-family:'Apple SD Gothic Neo',sans-serif;max-width:900px;margin:0 auto;padding:20px;">
        <div style="background:linear-gradient(135deg,#ff6b6b,#ee5a24);color:#fff;padding:20px;border-radius:10px;">
            <h1 style="margin:0;font-size:22px;">📊 YouTube 트렌드 리포트 [{time_label}]</h1>
            <p style="margin:5px 0 0;opacity:0.9;">{now} | 상위 {len(videos)}개 영상 분석</p>
        </div>

        <div style="background:#fff5f5;border:1px solid #ffcdd2;border-radius:8px;padding:15px;margin:15px 0;">
            <h3 style="margin:0 0 10px;color:#d32f2f;">🏷 트렌드 키워드 (태그 빈도)</h3>
            {tag_badges if tag_badges else '<p style="color:#999;">태그 데이터 없음</p>'}
        </div>

        <table style="width:100%;border-collapse:collapse;margin:15px 0;">
            <thead>
                <tr style="background:#4a4a4a;color:#fff;">
                    <th style="padding:10px;width:40px;">#</th>
                    <th style="padding:10px;width:130px;">썸네일</th>
                    <th style="padding:10px;">제목</th>
                    <th style="padding:10px;">채널</th>
                    <th style="padding:10px;width:70px;">조회수</th>
                    <th style="padding:10px;width:70px;">구독자</th>
                    <th style="padding:10px;width:80px;">성과</th>
                </tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>

        <p style="color:#999;font-size:12px;text-align:center;margin-top:20px;">
            YouTube 토픽 파인더 자동 분석 시스템 | 매일 오전 8시, 오후 6시 발송
        </p>
    </body>
    </html>
    """


def send_email_report(videos: list[dict]) -> bool:
    """트렌드 리포트 이메일 발송"""
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        logger.warning("이메일 설정 없음 - HTML 파일로 저장합니다")
        return _save_fallback(videos)

    tag_freq = analyze_tags(videos)
    html = _build_html_report(videos, tag_freq)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"📊 YouTube 트렌드 리포트 - {datetime.now().strftime('%Y.%m.%d %H:%M')}"
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECIPIENT_EMAIL or SENDER_EMAIL
    msg["Message-ID"] = f"<{uuid.uuid4()}@youtube-trend-tracker>"
    msg.attach(MIMEText(html, "html", "utf-8"))

    recipients = [
        addr.strip()
        for addr in (RECIPIENT_EMAIL or SENDER_EMAIL).split(",")
        if addr.strip()
    ]
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, recipients, msg.as_string())
        logger.info("이메일 발송 완료")
        return True
    except Exception as e:
        logger.error(f"이메일 발송 실패: {e}")
        return _save_fallback(videos)


def _save_fallback(videos: list[dict]) -> bool:
    """이메일 실패 시 HTML 파일로 저장"""
    tag_freq = analyze_tags(videos)
    html = _build_html_report(videos, tag_freq)
    fallback_path = Path("data") / f"report_{datetime.now().strftime('%Y%m%d_%H%M')}.html"
    fallback_path.parent.mkdir(parents=True, exist_ok=True)
    fallback_path.write_text(html, encoding="utf-8")
    logger.info(f"HTML 리포트 저장: {fallback_path}")
    return False

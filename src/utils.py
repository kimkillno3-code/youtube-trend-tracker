"""공통 유틸리티 — URL 검증, 텍스트 위생처리"""
import html
from urllib.parse import urlparse

# YouTube/Google 이미지 도메인 허용 목록
_ALLOWED_THUMBNAIL_HOSTS = frozenset({
    "i.ytimg.com",
    "i9.ytimg.com",
    "yt3.ggpht.com",
    "lh3.googleusercontent.com",
})


def validate_thumbnail_url(url: str) -> str:
    """썸네일 URL 검증 — YouTube/Google 도메인만 허용.

    Returns:
        검증된 URL 또는 빈 문자열
    """
    if not url:
        return ""
    try:
        parsed = urlparse(url)
        if parsed.scheme in ("http", "https") and parsed.hostname in _ALLOWED_THUMBNAIL_HOSTS:
            return url
    except Exception:
        pass
    return ""


def sanitize_html(text: str) -> str:
    """HTML 특수문자 이스케이프 — XSS 방지"""
    if not isinstance(text, str):
        return ""
    return html.escape(text, quote=True)

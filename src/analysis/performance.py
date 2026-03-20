"""성과 비율/별점 계산"""
from src.config import PERFORMANCE_THRESHOLDS


def calculate_stars(ratio: float) -> int:
    """조회수/구독자 비율 → 별점 (1~5)"""
    for stars in sorted(PERFORMANCE_THRESHOLDS.keys(), reverse=True):
        if ratio >= PERFORMANCE_THRESHOLDS[stars]:
            return stars
    return 1


def stars_display(stars: int) -> str:
    """별점을 이모지 문자열로 변환"""
    return "⭐" * stars


def format_count(n: int) -> str:
    """조회수를 읽기 쉬운 형태로 변환 (1.2M, 345K 등)"""
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)

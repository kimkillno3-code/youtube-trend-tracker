"""벤치마킹 인사이트 생성"""
import re
from collections import Counter
from src.analysis.performance import format_count


def parse_duration_seconds(duration: str) -> int:
    """ISO 8601 duration (PT4M33S) → 초"""
    if not duration:
        return 0
    match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duration)
    if not match:
        return 0
    h, m, s = match.groups(default="0")
    return int(h) * 3600 + int(m) * 60 + int(s)


def generate_insights(videos: list[dict]) -> dict:
    """영상 목록에서 벤치마킹 인사이트 생성"""
    if not videos:
        return {}

    view_counts = [v.get("view_count", 0) for v in videos]
    durations = [parse_duration_seconds(v.get("duration", "")) for v in videos]
    durations_nonzero = [d for d in durations if d > 0]

    # 카테고리 분포
    cat_counter = Counter(v.get("category_name", "기타") for v in videos)

    # 소규모 채널 대박 영상
    small_channel_hits = [
        v for v in videos
        if v.get("subscriber_count", 0) > 0
        and v.get("subscriber_count", 0) < 50000
        and v.get("view_count", 0) > 100000
    ]

    avg_views = sum(view_counts) / len(view_counts) if view_counts else 0
    avg_duration_min = (sum(durations_nonzero) / len(durations_nonzero) / 60) if durations_nonzero else 0

    return {
        "total_videos": len(videos),
        "avg_views": format_count(int(avg_views)),
        "avg_views_raw": int(avg_views),
        "max_views": format_count(max(view_counts)) if view_counts else "0",
        "avg_duration_min": round(avg_duration_min, 1),
        "top_category": cat_counter.most_common(1)[0] if cat_counter else ("기타", 0),
        "category_distribution": cat_counter.most_common(),
        "small_channel_hits": len(small_channel_hits),
    }

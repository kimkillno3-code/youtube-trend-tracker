"""키워드 검색 수집기 - 검색 + 상세 조회 + 채널 구독자 + 성과 계산"""
import logging
from datetime import datetime, timedelta
from typing import Optional

from src.collector.youtube_api import YouTubeAPIClient
from src.analysis.performance import calculate_stars
from src.collector.trending import CATEGORY_NAMES

logger = logging.getLogger(__name__)


def search_and_collect(
    api: YouTubeAPIClient,
    keyword: str,
    max_results: int = 25,
    order: str = "viewCount",
    days_ago: int = 7,
    video_duration: Optional[str] = None,
) -> list[dict]:
    """키워드 검색 후 상세 정보까지 수집"""
    logger.info(f'키워드 검색: "{keyword}" (정렬: {order}, 기간: {days_ago}일)')

    # 기간 필터
    published_after = None
    if days_ago > 0:
        dt = datetime.utcnow() - timedelta(days=days_ago)
        published_after = dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    # 1. 검색
    search_items = api.search_videos(
        query=keyword,
        max_results=max_results,
        order=order,
        published_after=published_after,
        video_duration=video_duration,
    )
    if not search_items:
        logger.warning(f'"{keyword}" 검색 결과 없음')
        return []

    # 2. 영상 ID 추출 → 상세 조회
    video_ids = [item["id"]["videoId"] for item in search_items if item["id"].get("videoId")]
    if not video_ids:
        return []

    details = api.get_video_details(video_ids)
    detail_map = {d["id"]: d for d in details}

    # 3. 채널 구독자 배치 조회
    channel_ids = list({d["snippet"]["channelId"] for d in details})
    channel_map = {}
    try:
        channels = api.get_channel_details(channel_ids)
        for ch in channels:
            channel_map[ch["id"]] = int(ch.get("statistics", {}).get("subscriberCount", 0))
    except Exception as e:
        logger.warning(f"채널 정보 조회 실패: {e}")

    # 4. 데이터 조합
    videos = []
    for rank, vid in enumerate(video_ids, 1):
        detail = detail_map.get(vid)
        if not detail:
            continue

        snippet = detail["snippet"]
        stats = detail.get("statistics", {})
        content = detail.get("contentDetails", {})

        channel_id = snippet["channelId"]
        subscriber_count = channel_map.get(channel_id, 0)
        view_count = int(stats.get("viewCount", 0))

        ratio = view_count / subscriber_count if subscriber_count > 0 else 0
        stars = calculate_stars(ratio)
        category_id = int(snippet.get("categoryId", 0))

        videos.append({
            "video_id": vid,
            "title": snippet.get("title", ""),
            "channel_id": channel_id,
            "channel_title": snippet.get("channelTitle", ""),
            "subscriber_count": subscriber_count,
            "view_count": view_count,
            "like_count": int(stats.get("likeCount", 0)),
            "comment_count": int(stats.get("commentCount", 0)),
            "thumbnail_url": snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
            "published_at": snippet.get("publishedAt"),
            "duration": content.get("duration", ""),
            "tags": snippet.get("tags", []),
            "category_id": category_id,
            "category_name": CATEGORY_NAMES.get(category_id, "기타"),
            "performance_ratio": round(ratio, 2),
            "performance_stars": stars,
            "search_rank": rank,
        })

    logger.info(f'"{keyword}" 검색 결과 {len(videos)}개 수집 (할당량: {api.quota_used})')
    return videos

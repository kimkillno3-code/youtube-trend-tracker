"""인기 영상 수집기 - mostPopular + 채널 구독자 조회 + 성과 계산"""
import logging
from datetime import datetime

from src.collector.youtube_api import YouTubeAPIClient
from src.analysis.performance import calculate_stars

logger = logging.getLogger(__name__)

# YouTube 카테고리 ID → 한글 이름
CATEGORY_NAMES = {
    1: "영화/애니메이션", 2: "자동차", 10: "음악", 15: "동물",
    17: "스포츠", 19: "여행/이벤트", 20: "게임", 22: "인물/블로그",
    23: "코미디", 24: "엔터테인먼트", 25: "뉴스/정치", 26: "노하우/스타일",
    27: "교육", 28: "과학기술", 29: "비영리/사회운동",
}


def collect_trending(api: YouTubeAPIClient, max_results: int = 30) -> list[dict]:
    """한국 YouTube 인기 영상 TOP N 수집 (태그 + 채널 구독자 포함)"""
    logger.info(f"인기 영상 수집 시작 (최대 {max_results}개)")

    # 1. 인기 영상 조회
    raw_items = api.get_trending_videos(region_code="KR", max_results=max_results)
    if not raw_items:
        logger.warning("인기 영상이 없습니다")
        return []

    # 2. 채널 ID 수집 → 배치 구독자 조회
    channel_ids = list({item["snippet"]["channelId"] for item in raw_items})
    channel_map = {}
    try:
        channels = api.get_channel_details(channel_ids)
        for ch in channels:
            sub_count = int(ch.get("statistics", {}).get("subscriberCount", 0))
            channel_map[ch["id"]] = sub_count
    except Exception as e:
        logger.warning(f"채널 정보 조회 실패: {e}")

    # 3. 영상 데이터 정리
    videos = []
    for rank, item in enumerate(raw_items, 1):
        snippet = item["snippet"]
        stats = item.get("statistics", {})
        content = item.get("contentDetails", {})

        channel_id = snippet["channelId"]
        subscriber_count = channel_map.get(channel_id, 0)
        view_count = int(stats.get("viewCount", 0))

        # 성과 비율 계산
        if subscriber_count > 0:
            ratio = view_count / subscriber_count
        else:
            ratio = 0
        stars = calculate_stars(ratio)

        category_id = int(snippet.get("categoryId", 0))

        videos.append({
            "video_id": item["id"],
            "title": snippet.get("title", ""),
            "description": snippet.get("description", "")[:500],
            "channel_id": channel_id,
            "channel_title": snippet.get("channelTitle", ""),
            "subscriber_count": subscriber_count,
            "published_at": snippet.get("publishedAt"),
            "category_id": category_id,
            "category_name": CATEGORY_NAMES.get(category_id, "기타"),
            "tags": snippet.get("tags", []),
            "thumbnail_url": snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
            "duration": content.get("duration", ""),
            "view_count": view_count,
            "like_count": int(stats.get("likeCount", 0)),
            "comment_count": int(stats.get("commentCount", 0)),
            "performance_ratio": round(ratio, 2),
            "performance_stars": stars,
            "trending_rank": rank,
        })

    logger.info(f"인기 영상 {len(videos)}개 수집 완료 (API 할당량: {api.quota_used})")
    return videos


def save_snapshots(repo, videos: list):
    """수집된 영상의 스냅샷 저장 (VPH 계산용)"""
    snapshots = []
    for v in videos:
        snapshots.append({
            "video_id": v["video_id"],
            "view_count": v.get("view_count", 0),
            "like_count": v.get("like_count", 0),
            "comment_count": v.get("comment_count", 0),
        })
    if snapshots:
        repo.save_video_snapshots_bulk(snapshots)
        logger.info(f"스냅샷 {len(snapshots)}개 저장")

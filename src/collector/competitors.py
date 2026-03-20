"""경쟁 채널 모니터링 - 채널 등록, 업로드 추적, 성과 비교"""
import logging
import re
from typing import Optional

from src.collector.youtube_api import YouTubeAPIClient

logger = logging.getLogger(__name__)


def parse_channel_input(channel_input: str) -> Optional[str]:
    """채널 URL/ID/핸들에서 채널 ID 추출

    지원 형식:
    - UC... (채널 ID 직접)
    - https://youtube.com/channel/UC...
    - https://youtube.com/@handle
    - @handle
    """
    channel_input = channel_input.strip()

    # 이미 채널 ID 형태
    if channel_input.startswith("UC") and len(channel_input) == 24:
        return channel_input

    # URL에서 채널 ID 추출
    match = re.search(r"channel/(UC[\w-]{22})", channel_input)
    if match:
        return match.group(1)

    # @핸들이나 URL의 @핸들은 API로 검색 필요
    return None


def register_channel(api: YouTubeAPIClient, channel_input: str) -> Optional[dict]:
    """채널 등록: URL/ID/핸들로 채널 정보 조회"""
    channel_id = parse_channel_input(channel_input)

    if channel_id:
        # 직접 ID로 조회
        channels = api.get_channel_details([channel_id])
    else:
        # 핸들이나 이름으로 검색
        handle = channel_input.strip().lstrip("@")
        try:
            response = api.youtube.search().list(
                part="snippet",
                q=handle,
                type="channel",
                maxResults=1,
            ).execute()
            api._track_quota("search.list")

            items = response.get("items", [])
            if not items:
                return None
            channel_id = items[0]["snippet"]["channelId"]
            channels = api.get_channel_details([channel_id])
        except Exception as e:
            logger.error(f"채널 검색 실패: {e}")
            return None

    if not channels:
        return None

    ch = channels[0]
    stats = ch.get("statistics", {})
    snippet = ch.get("snippet", {})

    return {
        "channel_id": ch["id"],
        "channel_title": snippet.get("title", ""),
        "subscriber_count": int(stats.get("subscriberCount", 0)),
        "thumbnail_url": snippet.get("thumbnails", {}).get("default", {}).get("url", ""),
        "avg_view_count": 0,  # 업로드 후 계산
    }


def fetch_channel_uploads(api: YouTubeAPIClient, channel_id: str,
                          max_results: int = 10) -> list:
    """채널의 최근 업로드 영상 조회 (playlistItems API)"""
    # 업로드 재생목록 ID: UC → UU
    uploads_playlist_id = "UU" + channel_id[2:]

    try:
        items = api.get_playlist_items(uploads_playlist_id, max_results=max_results)
    except Exception as e:
        logger.error(f"채널 업로드 조회 실패 ({channel_id}): {e}")
        return []

    if not items:
        return []

    # 영상 ID 추출 → 상세 조회
    video_ids = []
    for item in items:
        vid = item.get("contentDetails", {}).get("videoId")
        if vid:
            video_ids.append(vid)

    if not video_ids:
        return []

    details = api.get_video_details(video_ids)

    videos = []
    for d in details:
        snippet = d.get("snippet", {})
        stats = d.get("statistics", {})
        content = d.get("contentDetails", {})

        videos.append({
            "channel_id": channel_id,
            "video_id": d["id"],
            "title": snippet.get("title", ""),
            "thumbnail_url": snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
            "published_at": snippet.get("publishedAt", ""),
            "view_count": int(stats.get("viewCount", 0)),
            "like_count": int(stats.get("likeCount", 0)),
            "comment_count": int(stats.get("commentCount", 0)),
            "tags": snippet.get("tags", []),
            "category_name": "",
            "duration": content.get("duration", ""),
        })

    return videos


def calculate_channel_average(videos: list) -> int:
    """채널 평균 조회수 계산 (최근 영상 기준)"""
    if not videos:
        return 0
    total = sum(v.get("view_count", 0) for v in videos)
    return total // len(videos)


def enrich_with_performance(videos: list, avg_views: int) -> list:
    """영상 목록에 채널 평균 대비 성과 추가"""
    for v in videos:
        if avg_views > 0:
            v["performance_vs_avg"] = round(v.get("view_count", 0) / avg_views, 2)
        else:
            v["performance_vs_avg"] = 0
    return videos


def check_channel(api: YouTubeAPIClient, channel_id: str,
                  max_results: int = 10) -> dict:
    """단일 채널 체크: 업로드 조회 + 평균 계산 + 성과 비교"""
    videos = fetch_channel_uploads(api, channel_id, max_results=max_results)
    avg = calculate_channel_average(videos)
    videos = enrich_with_performance(videos, avg)

    return {
        "channel_id": channel_id,
        "videos": videos,
        "avg_view_count": avg,
        "total_videos": len(videos),
    }

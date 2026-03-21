"""YouTube Data API v3 클라이언트 (할당량 추적 포함)"""
import time
import logging
from typing import Optional

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)


class YouTubeAPIClient:
    """YouTube Data API v3 래퍼 - 배치 조회, 할당량 추적, 재시도"""

    QUOTA_COSTS = {
        "videos.list": 1,
        "search.list": 100,
        "channels.list": 1,
        "videoCategories.list": 1,
        "playlistItems.list": 1,
    }

    def __init__(self, api_key: str):
        self.youtube = build("youtube", "v3", developerKey=api_key)
        self.quota_used = 0
        self.quota_limit = 10000

    def _track_quota(self, method: str) -> None:
        cost = self.QUOTA_COSTS.get(method, 1)
        self.quota_used += cost
        if self.quota_used > self.quota_limit * 0.8:
            logger.warning(f"할당량 경고: {self.quota_used}/{self.quota_limit} 사용")

    def _retry(self, func, max_retries: int = 3):
        """지수 백오프 재시도"""
        for attempt in range(max_retries):
            try:
                return func()
            except HttpError as e:
                if e.resp.status == 403 and "quotaExceeded" in str(e):
                    logger.error("YouTube API 할당량 초과")
                    raise
                if e.resp.status in (429, 500, 503) and attempt < max_retries - 1:
                    wait = 2 ** (attempt + 1)
                    logger.warning(f"재시도 {attempt+1}/{max_retries} ({wait}초 대기)")
                    time.sleep(wait)
                    continue
                raise
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(2 ** (attempt + 1))
                    continue
                raise

    def get_trending_videos(
        self, region_code: str = "KR", max_results: int = 30,
        category_id: Optional[str] = None
    ) -> list[dict]:
        """인기 영상 조회 (videos.list chart=mostPopular)"""
        def _call():
            params = {
                "part": "snippet,statistics,contentDetails",
                "chart": "mostPopular",
                "regionCode": region_code,
                "maxResults": min(max_results, 50),
            }
            if category_id:
                params["videoCategoryId"] = category_id
            return self.youtube.videos().list(**params).execute()

        self._track_quota("videos.list")
        response = self._retry(_call)
        return response.get("items", [])

    def search_videos(
        self, query: str = "", max_results: int = 25, order: str = "viewCount",
        published_after: Optional[str] = None, region_code: str = "KR",
        video_duration: Optional[str] = None,
        relevance_language: Optional[str] = None,
        video_category_id: Optional[str] = None,
    ) -> list[dict]:
        """키워드 검색 (search.list) - 100 유닛/호출"""
        def _call():
            lang = relevance_language or {"KR": "ko", "US": "en", "JP": "ja"}.get(region_code, "ko")
            params = {
                "part": "snippet",
                "type": "video",
                "regionCode": region_code,
                "relevanceLanguage": lang,
                "maxResults": min(max_results, 50),
                "order": order,
            }
            if query:
                params["q"] = query
            if published_after:
                params["publishedAfter"] = published_after
            if video_duration:
                params["videoDuration"] = video_duration
            if video_category_id:
                params["videoCategoryId"] = video_category_id
            return self.youtube.search().list(**params).execute()

        self._track_quota("search.list")
        response = self._retry(_call)
        return response.get("items", [])

    def get_video_details(self, video_ids: list[str]) -> list[dict]:
        """영상 상세 조회 (배치, 최대 50개씩) - 1 유닛/호출"""
        all_items = []
        for i in range(0, len(video_ids), 50):
            batch = video_ids[i:i + 50]
            def _call(ids=",".join(batch)):
                return self.youtube.videos().list(
                    part="snippet,statistics,contentDetails,topicDetails",
                    id=ids,
                ).execute()

            self._track_quota("videos.list")
            response = self._retry(_call)
            all_items.extend(response.get("items", []))
        return all_items

    def get_playlist_items(self, playlist_id: str, max_results: int = 10) -> list:
        """재생목록 항목 조회 (playlistItems.list) - 1 유닛/호출"""
        def _call():
            return self.youtube.playlistItems().list(
                part="snippet,contentDetails",
                playlistId=playlist_id,
                maxResults=min(max_results, 50),
            ).execute()

        self._track_quota("playlistItems.list")
        response = self._retry(_call)
        return response.get("items", [])

    def get_channel_details(self, channel_ids: list[str]) -> list[dict]:
        """채널 상세 조회 (배치, 최대 50개씩) - 1 유닛/호출"""
        all_items = []
        for i in range(0, len(channel_ids), 50):
            batch = channel_ids[i:i + 50]
            def _call(ids=",".join(batch)):
                return self.youtube.channels().list(
                    part="snippet,statistics",
                    id=ids,
                ).execute()

            self._track_quota("channels.list")
            response = self._retry(_call)
            all_items.extend(response.get("items", []))
        return all_items

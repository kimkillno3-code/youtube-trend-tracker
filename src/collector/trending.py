"""인기 영상 수집기 - mostPopular + 채널 구독자 조회 + 성과 계산"""
import logging
from datetime import datetime, timedelta

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

# 대시보드에 표시할 주요 카테고리
MAIN_CATEGORIES = {
    10: "음악", 20: "게임", 24: "엔터테인먼트", 25: "뉴스/정치",
    1: "영화/애니메이션", 17: "스포츠", 22: "인물/블로그",
    26: "노하우/스타일", 27: "교육", 28: "과학기술",
}

# 국가 설정
COUNTRIES = {
    "KR": "한국",
    "JP": "일본",
    "US": "미국",
}

# 기간 탭 search.list용 — 국가별 카테고리 검색어
CATEGORY_SEARCH_QUERIES = {
    "KR": {
        10: "음악", 20: "게임", 24: "엔터테인먼트", 25: "뉴스",
        1: "영화", 17: "스포츠", 22: "브이로그",
        26: "뷰티|패션", 27: "교육", 28: "과학기술",
    },
    "US": {
        10: "music", 20: "gaming", 24: "entertainment", 25: "news",
        1: "movies", 17: "sports", 22: "vlog",
        26: "beauty|fashion", 27: "education", 28: "science|technology",
    },
    "JP": {
        10: "音楽", 20: "ゲーム", 24: "エンタメ", 25: "ニュース",
        1: "映画", 17: "スポーツ", 22: "Vlog",
        26: "美容|ファッション", 27: "教育", 28: "科学技術",
    },
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


def collect_trending_by_category(
    api: YouTubeAPIClient, category_id: int, max_results: int = 30,
    region_code: str = "KR",
) -> list[dict]:
    """카테고리별 실시간 인기 영상 수집 (videos.list chart=mostPopular + videoCategoryId)

    비용: 1 유닛 (videos.list) + 1 유닛 (channels.list)
    """
    cat_name = CATEGORY_NAMES.get(category_id, str(category_id))
    country = COUNTRIES.get(region_code, region_code)
    logger.info(f"[{country}/{cat_name}] 카테고리별 인기 영상 수집 시작 (최대 {max_results}개)")

    raw_items = api.get_trending_videos(
        region_code=region_code, max_results=max_results, category_id=str(category_id),
    )
    if not raw_items:
        logger.warning(f"[{cat_name}] 인기 영상이 없습니다")
        return []

    # 채널 구독자 조회
    channel_ids = list({item["snippet"]["channelId"] for item in raw_items})
    channel_map = {}
    try:
        channels = api.get_channel_details(channel_ids)
        for ch in channels:
            sub_count = int(ch.get("statistics", {}).get("subscriberCount", 0))
            channel_map[ch["id"]] = sub_count
    except Exception as e:
        logger.warning(f"채널 정보 조회 실패: {e}")

    videos = []
    for rank, item in enumerate(raw_items, 1):
        snippet = item["snippet"]
        stats = item.get("statistics", {})
        content = item.get("contentDetails", {})

        channel_id = snippet["channelId"]
        subscriber_count = channel_map.get(channel_id, 0)
        view_count = int(stats.get("viewCount", 0))

        ratio = view_count / subscriber_count if subscriber_count > 0 else 0
        stars = calculate_stars(ratio)
        cid = int(snippet.get("categoryId", 0))

        videos.append({
            "video_id": item["id"],
            "title": snippet.get("title", ""),
            "description": snippet.get("description", "")[:500],
            "channel_id": channel_id,
            "channel_title": snippet.get("channelTitle", ""),
            "subscriber_count": subscriber_count,
            "published_at": snippet.get("publishedAt"),
            "category_id": cid,
            "category_name": CATEGORY_NAMES.get(cid, "기타"),
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

    logger.info(f"[{cat_name}] 인기 영상 {len(videos)}개 수집 완료 (API 할당량: {api.quota_used})")
    return videos


def collect_popular_by_period(
    api: YouTubeAPIClient, days: int = 7, max_results: int = 30,
    category_name: str = "", region_code: str = "KR",
    category_id: int = 0,
) -> list[dict]:
    """기간별 인기 영상 수집 (search.list + 상세 조회 + 채널 구독자)

    category_id + region_code로 국가별 검색어 자동 결정.
    category_name은 폴백용.
    """
    # 국가별 검색어 결정
    region_queries = CATEGORY_SEARCH_QUERIES.get(region_code, CATEGORY_SEARCH_QUERIES["KR"])
    if category_id and category_id in region_queries:
        query = region_queries[category_id]
    elif category_name:
        query = category_name
    else:
        query = "|".join(region_queries.values())

    country = COUNTRIES.get(region_code, region_code)
    logger.info(f"[{country}] 기간별 인기 영상 수집 시작 (q={query}, 최근 {days}일, 최대 {max_results}개)")

    cutoff = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    search_results = api.search_videos(
        query=query, published_after=cutoff,
        order="viewCount", max_results=max_results,
        region_code=region_code,
        video_category_id=str(category_id) if category_id else None,
    )
    if not search_results:
        logger.warning("검색 결과가 없습니다")
        return []

    # 2. video ID 추출 → 상세 조회 (통계 + 태그 등)
    video_ids = [item["id"]["videoId"] for item in search_results
                 if item.get("id", {}).get("videoId")]
    if not video_ids:
        return []

    details = api.get_video_details(video_ids)

    # 2-b. 카테고리 불일치 영상 제거 (검색 결과에 다른 카테고리 영상이 섞이는 문제 방지)
    if category_id:
        details = [d for d in details
                   if int(d.get("snippet", {}).get("categoryId", 0)) == category_id]

    detail_map = {d["id"]: d for d in details}

    # 3. 채널 구독자 조회
    channel_ids = list({d["snippet"]["channelId"] for d in details})
    channel_map = {}
    try:
        channels = api.get_channel_details(channel_ids)
        for ch in channels:
            sub_count = int(ch.get("statistics", {}).get("subscriberCount", 0))
            channel_map[ch["id"]] = sub_count
    except Exception as e:
        logger.warning(f"채널 정보 조회 실패: {e}")

    # 4. collect_trending()과 동일한 포맷으로 정리
    videos = []
    for rank, vid in enumerate(video_ids, 1):
        item = detail_map.get(vid)
        if not item:
            continue
        snippet = item["snippet"]
        stats = item.get("statistics", {})
        content = item.get("contentDetails", {})

        channel_id = snippet["channelId"]
        subscriber_count = channel_map.get(channel_id, 0)
        view_count = int(stats.get("viewCount", 0))

        ratio = view_count / subscriber_count if subscriber_count > 0 else 0
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

    logger.info(f"기간별 인기 영상 {len(videos)}개 수집 완료 (API 할당량: {api.quota_used})")
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

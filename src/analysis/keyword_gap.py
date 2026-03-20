"""키워드 갭 분석 - 수요(검색량) vs 공급(영상 수) 비교"""
import logging
from typing import Optional

from src.collector.youtube_api import YouTubeAPIClient

logger = logging.getLogger(__name__)


def calculate_opportunity_score(demand: float, supply: float) -> float:
    """선점 기회 점수 계산 (0~100)

    높은 수요 + 낮은 공급 = 높은 기회
    """
    score = (demand * 0.6) + ((100 - supply) * 0.4)
    return round(min(max(score, 0), 100), 1)


def get_competition_level(video_count: int, avg_views: int) -> str:
    """경쟁 강도 판정"""
    if video_count <= 3:
        return "매우 낮음"
    elif video_count <= 10:
        return "낮음"
    elif video_count <= 25:
        return "보통"
    else:
        return "높음"


def analyze_keyword_gap(api: YouTubeAPIClient, keyword: str,
                        trends_interest: int = 50) -> dict:
    """단일 키워드 갭 분석

    1. YouTube 검색으로 최근 7일 영상 수 확인 (supply)
    2. Google Trends 관심도 활용 (demand)
    3. opportunity_score 계산

    Args:
        api: YouTube API 클라이언트
        keyword: 분석할 키워드
        trends_interest: Google Trends 관심도 (0-100)

    Returns:
        분석 결과 dict
    """
    from datetime import datetime, timedelta

    # 7일 전 날짜 계산
    published_after = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")

    # YouTube 검색으로 공급 측정
    try:
        results = api.search_videos(
            query=keyword,
            max_results=25,
            order="viewCount",
            published_after=published_after,
        )
        video_count = len(results)

        # 상위 영상들의 상세 정보
        avg_views = 0
        if results:
            video_ids = [r["id"]["videoId"] for r in results if r.get("id", {}).get("videoId")]
            if video_ids:
                details = api.get_video_details(video_ids[:10])
                total_views = sum(
                    int(d.get("statistics", {}).get("viewCount", 0))
                    for d in details
                )
                avg_views = total_views // len(details) if details else 0

    except Exception as e:
        logger.error(f"키워드 갭 분석 실패 ({keyword}): {e}")
        video_count = 0
        avg_views = 0

    # 수요 점수: Google Trends 관심도 (0-100)
    demand_score = min(trends_interest, 100)

    # 공급 점수: 영상 수 기반 (0-100으로 정규화, 25개 이상이면 100)
    supply_score = min((video_count / 25) * 100, 100)

    # 선점 기회 점수
    opportunity = calculate_opportunity_score(demand_score, supply_score)

    # 경쟁 강도
    competition = get_competition_level(video_count, avg_views)

    return {
        "keyword": keyword,
        "demand_score": round(demand_score, 1),
        "supply_score": round(supply_score, 1),
        "opportunity_score": opportunity,
        "video_count_7d": video_count,
        "avg_views_7d": avg_views,
        "competition_level": competition,
    }


def batch_analyze_gaps(api: YouTubeAPIClient, keywords: list,
                       trends_data: Optional[dict] = None) -> list:
    """여러 키워드 일괄 갭 분석

    Args:
        api: YouTube API 클라이언트
        keywords: 키워드 리스트
        trends_data: {keyword: interest_score} 딕셔너리 (Google Trends)
    """
    if trends_data is None:
        trends_data = {}

    results = []
    # 할당량 효율화: 최대 5개 키워드
    for kw in keywords[:5]:
        interest = trends_data.get(kw, 50)  # 기본 관심도 50
        gap = analyze_keyword_gap(api, kw, interest)
        results.append(gap)

    results.sort(key=lambda x: x["opportunity_score"], reverse=True)
    return results

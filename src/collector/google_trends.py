"""Google Trends 데이터 수집 - 브레이크아웃 키워드 탐지

trendspyg 기반 (pytrends 후속 라이브러리, 2025.04~)
"""
import logging
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)


def get_trending_searches(geo: str = "KR") -> list:
    """실시간 급상승 검색어 수집 (trendspyg RSS 방식)

    Returns: [{"keyword": str, "traffic": str, "news": list}, ...]
    """
    try:
        from trendspyg import download_google_trends_rss
        items = download_google_trends_rss(geo=geo)
        if not items:
            return []

        results = []
        for item in items:
            results.append({
                "keyword": item.get("trend", ""),
                "traffic": item.get("traffic", "0"),
                "news": [
                    {"headline": a.get("headline", ""), "source": a.get("source", "")}
                    for a in item.get("news_articles", [])[:3]
                ],
            })
        return results
    except ImportError:
        logger.error("trendspyg가 설치되지 않았습니다: pip install trendspyg")
        return []
    except Exception as e:
        logger.error(f"급상승 검색어 수집 실패: {e}")
        return []


def _parse_traffic(traffic_str: str) -> int:
    """트래픽 문자열을 숫자로 변환 ('500+' → 500, '2K+' → 2000)"""
    if not traffic_str:
        return 0
    s = traffic_str.replace("+", "").replace(",", "").strip()
    if s.endswith("K"):
        return int(float(s[:-1]) * 1000)
    elif s.endswith("M"):
        return int(float(s[:-1]) * 1000000)
    try:
        return int(s)
    except ValueError:
        return 0


def detect_breakout_keywords(threshold_pct: float = 500.0,
                             geo: str = "KR") -> list:
    """브레이크아웃 키워드 탐지

    trendspyg RSS로 급상승 검색어를 가져와서 트래픽 기반으로 분류.
    Google Trends 급상승 목록에 있다는 것 자체가 breakout 신호.

    Returns: [{"keyword": str, "surge_pct": float, "interest": int}, ...]
    """
    trending = get_trending_searches(geo=geo)
    if not trending:
        return []

    breakouts = []
    for item in trending:
        keyword = item.get("keyword", "")
        if not keyword:
            continue

        traffic = _parse_traffic(item.get("traffic", "0"))

        # 트래픽 기반 surge 추정
        # Google Trends 급상승 목록에 있으면 최소 1000%+
        if traffic >= 500:
            surge_pct = 5000.0
            interest = 100
        elif traffic >= 200:
            surge_pct = 3000.0
            interest = 85
        elif traffic >= 100:
            surge_pct = 1500.0
            interest = 70
        else:
            surge_pct = 1000.0
            interest = 50

        breakouts.append({
            "keyword": keyword,
            "surge_pct": surge_pct,
            "interest": interest,
            "traffic": traffic,
            "news": item.get("news", []),
        })

    # surge_pct 내림차순 정렬, 동일 시 traffic 내림차순
    breakouts.sort(key=lambda x: (x["surge_pct"], x.get("traffic", 0)), reverse=True)
    return breakouts


def get_interest_over_time(keywords: list, timeframe: str = "now 7-d",
                           geo: str = "KR") -> Optional[pd.DataFrame]:
    """키워드별 시간대별 검색 관심도 조회 (pytrends fallback)"""
    if not keywords:
        return None
    try:
        from pytrends.request import TrendReq
        pt = TrendReq(hl="ko", tz=540, timeout=(10, 25))
        pt.build_payload(keywords[:5], cat=0, timeframe=timeframe, geo=geo)
        df = pt.interest_over_time()
        return df if not df.empty else None
    except Exception as e:
        logger.warning(f"관심도 조회 실패 (pytrends): {e}")
        return None


def get_related_queries(keyword: str, geo: str = "KR") -> dict:
    """연관 검색어 조회 (pytrends fallback)"""
    try:
        from pytrends.request import TrendReq
        pt = TrendReq(hl="ko", tz=540, timeout=(10, 25))
        pt.build_payload([keyword], cat=0, timeframe="now 7-d", geo=geo)
        related = pt.related_queries()
        result = {"rising": [], "top": []}

        kw_data = related.get(keyword, {})
        if kw_data.get("rising") is not None and not kw_data["rising"].empty:
            for _, row in kw_data["rising"].iterrows():
                result["rising"].append({
                    "query": row.get("query", ""),
                    "value": int(row.get("value", 0)),
                })

        if kw_data.get("top") is not None and not kw_data["top"].empty:
            for _, row in kw_data["top"].iterrows():
                result["top"].append({
                    "query": row.get("query", ""),
                    "value": int(row.get("value", 0)),
                })

        return result
    except Exception as e:
        logger.warning(f"연관 검색어 조회 실패: {e}")
        return {"rising": [], "top": []}

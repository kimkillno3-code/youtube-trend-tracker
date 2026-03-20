"""시즌 트렌드 예측 - 한국 시즌별 키워드"""
from datetime import datetime, timedelta

# 한국 월별 시즌 키워드 (신뢰도 포함)
KOREAN_SEASONAL_EVENTS = {
    1: [
        {"keyword": "새해", "confidence": 95, "category": "이벤트"},
        {"keyword": "신년 다짐", "confidence": 90, "category": "라이프"},
        {"keyword": "설날", "confidence": 85, "category": "전통"},
        {"keyword": "겨울방학", "confidence": 80, "category": "교육"},
        {"keyword": "스키", "confidence": 75, "category": "스포츠"},
        {"keyword": "새해 운세", "confidence": 85, "category": "엔터"},
    ],
    2: [
        {"keyword": "발렌타인데이", "confidence": 95, "category": "이벤트"},
        {"keyword": "졸업", "confidence": 90, "category": "교육"},
        {"keyword": "설날", "confidence": 88, "category": "전통"},
        {"keyword": "겨울 끝", "confidence": 70, "category": "라이프"},
        {"keyword": "취업 준비", "confidence": 80, "category": "교육"},
    ],
    3: [
        {"keyword": "봄", "confidence": 90, "category": "시즌"},
        {"keyword": "벚꽃", "confidence": 95, "category": "여행"},
        {"keyword": "입학", "confidence": 92, "category": "교육"},
        {"keyword": "새학기", "confidence": 90, "category": "교육"},
        {"keyword": "화이트데이", "confidence": 85, "category": "이벤트"},
        {"keyword": "봄 패션", "confidence": 80, "category": "패션"},
        {"keyword": "삼일절", "confidence": 70, "category": "전통"},
    ],
    4: [
        {"keyword": "벚꽃", "confidence": 95, "category": "여행"},
        {"keyword": "봄나들이", "confidence": 90, "category": "여행"},
        {"keyword": "만우절", "confidence": 88, "category": "엔터"},
        {"keyword": "봄 맞이 대청소", "confidence": 75, "category": "라이프"},
        {"keyword": "꽃가루 알레르기", "confidence": 80, "category": "건강"},
    ],
    5: [
        {"keyword": "어린이날", "confidence": 95, "category": "이벤트"},
        {"keyword": "어버이날", "confidence": 95, "category": "이벤트"},
        {"keyword": "가정의달", "confidence": 90, "category": "라이프"},
        {"keyword": "석가탄신일", "confidence": 75, "category": "전통"},
        {"keyword": "스승의날", "confidence": 85, "category": "이벤트"},
    ],
    6: [
        {"keyword": "여름 준비", "confidence": 85, "category": "시즌"},
        {"keyword": "현충일", "confidence": 80, "category": "전통"},
        {"keyword": "장마", "confidence": 90, "category": "날씨"},
        {"keyword": "수능 D-day", "confidence": 75, "category": "교육"},
        {"keyword": "다이어트", "confidence": 85, "category": "건강"},
    ],
    7: [
        {"keyword": "여름 휴가", "confidence": 95, "category": "여행"},
        {"keyword": "바다", "confidence": 90, "category": "여행"},
        {"keyword": "여름방학", "confidence": 90, "category": "교육"},
        {"keyword": "에어컨", "confidence": 80, "category": "가전"},
        {"keyword": "물놀이", "confidence": 88, "category": "레저"},
        {"keyword": "수박", "confidence": 75, "category": "음식"},
    ],
    8: [
        {"keyword": "휴가", "confidence": 90, "category": "여행"},
        {"keyword": "광복절", "confidence": 80, "category": "전통"},
        {"keyword": "여름 끝", "confidence": 75, "category": "시즌"},
        {"keyword": "개학", "confidence": 85, "category": "교육"},
        {"keyword": "캠핑", "confidence": 82, "category": "레저"},
    ],
    9: [
        {"keyword": "추석", "confidence": 95, "category": "전통"},
        {"keyword": "가을", "confidence": 90, "category": "시즌"},
        {"keyword": "단풍", "confidence": 85, "category": "여행"},
        {"keyword": "추석 선물", "confidence": 88, "category": "쇼핑"},
        {"keyword": "가을 패션", "confidence": 80, "category": "패션"},
    ],
    10: [
        {"keyword": "단풍", "confidence": 95, "category": "여행"},
        {"keyword": "할로윈", "confidence": 90, "category": "이벤트"},
        {"keyword": "한글날", "confidence": 75, "category": "전통"},
        {"keyword": "가을 여행", "confidence": 88, "category": "여행"},
        {"keyword": "수능", "confidence": 82, "category": "교육"},
    ],
    11: [
        {"keyword": "수능", "confidence": 95, "category": "교육"},
        {"keyword": "블랙프라이데이", "confidence": 92, "category": "쇼핑"},
        {"keyword": "빼빼로데이", "confidence": 90, "category": "이벤트"},
        {"keyword": "김장", "confidence": 85, "category": "전통"},
        {"keyword": "겨울 준비", "confidence": 80, "category": "시즌"},
    ],
    12: [
        {"keyword": "크리스마스", "confidence": 95, "category": "이벤트"},
        {"keyword": "연말", "confidence": 90, "category": "라이프"},
        {"keyword": "송년회", "confidence": 85, "category": "라이프"},
        {"keyword": "연말정산", "confidence": 88, "category": "경제"},
        {"keyword": "겨울", "confidence": 80, "category": "시즌"},
        {"keyword": "올해의 영상", "confidence": 82, "category": "엔터"},
    ],
}


def get_upcoming_seasonal_keywords(weeks_ahead: int = 6) -> list:
    """향후 N주 내 예상 시즌 키워드 반환

    Returns:
        [{"keyword", "expected_date", "confidence", "category", "weeks_until"}, ...]
    """
    now = datetime.now()
    results = []

    for week in range(1, weeks_ahead + 1):
        target_date = now + timedelta(weeks=week)
        month = target_date.month

        events = KOREAN_SEASONAL_EVENTS.get(month, [])
        for event in events:
            results.append({
                "keyword": event["keyword"],
                "expected_date": target_date.strftime("%Y-%m-%d"),
                "confidence": event["confidence"],
                "category": event["category"],
                "peak_month": month,
                "weeks_until": week,
            })

    # 중복 키워드 제거 (가장 가까운 날짜 유지)
    seen = {}
    for r in results:
        kw = r["keyword"]
        if kw not in seen or r["weeks_until"] < seen[kw]["weeks_until"]:
            seen[kw] = r

    return sorted(seen.values(), key=lambda x: (-x["confidence"], x["weeks_until"]))


def get_seasonal_by_week(weeks_ahead: int = 6) -> dict:
    """주차별로 그룹핑된 시즌 키워드

    Returns:
        {"4월 1주": [keywords...], "4월 2주": [...], ...}
    """
    now = datetime.now()
    result = {}

    for week in range(1, weeks_ahead + 1):
        target_date = now + timedelta(weeks=week)
        month = target_date.month
        week_of_month = (target_date.day - 1) // 7 + 1
        label = f"{month}월 {week_of_month}주"

        events = KOREAN_SEASONAL_EVENTS.get(month, [])
        if events:
            result[label] = [
                {"keyword": e["keyword"], "confidence": e["confidence"],
                 "category": e["category"]}
                for e in events[:5]
            ]

    return result

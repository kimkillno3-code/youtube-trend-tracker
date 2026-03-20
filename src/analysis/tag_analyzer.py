"""태그 빈도 분석 - 영상 목록에서 태그를 추출하고 빈도수 계산"""
import json
from collections import Counter


def analyze_tags(videos: list[dict]) -> list[tuple[str, int]]:
    """
    영상 목록에서 태그를 추출하고 빈도수(해당 태그를 사용한 영상 수)를 계산.

    Returns: [(태그명, 영상수), ...] 빈도순 정렬
    """
    tag_counter = Counter()

    for video in videos:
        tags = video.get("tags", [])
        if isinstance(tags, str):
            try:
                tags = json.loads(tags)
            except (json.JSONDecodeError, TypeError):
                tags = []

        # 중복 태그 제거 (한 영상에서 같은 태그 2번 카운트 방지)
        unique_tags = set()
        for tag in tags:
            normalized = tag.strip().lower()
            if normalized and len(normalized) >= 2:
                unique_tags.add(normalized)

        tag_counter.update(unique_tags)

    return tag_counter.most_common()


def get_title_keywords(videos: list[dict], min_length: int = 2) -> list[tuple[str, int]]:
    """
    태그가 없는 경우 제목에서 키워드를 추출 (보조 분석).
    간단한 공백 토큰화 + 불용어 제거.
    """
    stopwords = {
        "의", "가", "이", "은", "는", "을", "를", "에", "에서", "로", "으로",
        "와", "과", "도", "만", "한", "하는", "그", "저", "것", "수", "등",
        "및", "더", "매우", "the", "a", "an", "in", "on", "at", "to", "for",
        "is", "are", "was", "were", "be", "and", "or", "of", "with", "this",
        "that", "how", "what", "why", "when", "who", "which",
    }

    word_counter = Counter()
    for video in videos:
        title = video.get("title", "")
        # 특수문자 제거하고 공백 분리
        words = title.replace("|", " ").replace("-", " ").replace("(", " ").replace(")", " ").split()
        for word in words:
            word = word.strip().lower()
            if len(word) >= min_length and word not in stopwords:
                word_counter[word] = word_counter.get(word, 0) + 1

    return word_counter.most_common()

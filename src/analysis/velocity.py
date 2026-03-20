"""트렌드 속도 분석 - VPH(Views Per Hour) 계산 및 분류"""
import logging
from datetime import datetime, timezone
from typing import Optional

from src.analysis.performance import format_count
from src.config import VELOCITY_THRESHOLDS

logger = logging.getLogger(__name__)


def calculate_vph(view_count: int, published_at: str) -> float:
    """VPH (시간당 조회수) 계산 — timezone-aware UTC 기반.

    Args:
        view_count: 조회수
        published_at: ISO 8601 발행일 (UTC 기준)

    Returns:
        시간당 조회수 (float). 계산 불가 시 0.0
    """
    if not published_at or view_count < 0:
        return 0.0
    try:
        if "T" in published_at:
            pub_time = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
        else:
            # DB bare timestamp → UTC로 간주
            pub_time = datetime.strptime(
                published_at[:19], "%Y-%m-%d %H:%M:%S"
            ).replace(tzinfo=timezone.utc)
        now_utc = datetime.now(timezone.utc)
        hours = max((now_utc - pub_time).total_seconds() / 3600, 0.1)
        return view_count / hours
    except (ValueError, TypeError) as e:
        logger.debug("VPH 계산 실패 (published_at=%s): %s", published_at, e)
        return 0.0


def calculate_acceleration(current_vph: float, previous_vph: float) -> float:
    """VPH 가속도 계산 (%).

    Returns:
        가속도 백분율. previous_vph가 0 이하면 current_vph 존재 여부에 따라 100 또는 0.
    """
    if previous_vph <= 0:
        return 100.0 if current_vph > 0 else 0.0
    return ((current_vph - previous_vph) / previous_vph) * 100


def classify_velocity(vph: float, acceleration: float, has_snapshot: bool = True) -> tuple:
    """속도 분류 → (label, arrow, css_class)

    스냅샷이 있으면 가속도 기반, 없으면 VPH 절대값 기반으로 분류.
    임계값은 config.py의 VELOCITY_THRESHOLDS 사용.
    """
    surge = VELOCITY_THRESHOLDS["급상승"]
    rising = VELOCITY_THRESHOLDS["상승"]
    stable_min = VELOCITY_THRESHOLDS["안정"].get("acceleration_min", -10)

    if has_snapshot and acceleration != 0:
        if acceleration > surge["acceleration_min"] and vph > surge["vph_min"]:
            return ("급상승", "↑↑", "velocity-surge")
        elif acceleration > rising["acceleration_min"] or vph > rising["vph_min"]:
            return ("상승", "↑", "velocity-rising")
        elif acceleration > stable_min:
            return ("안정", "→", "velocity-stable")
        else:
            return ("하락", "↓", "velocity-falling")
    else:
        # VPH 절대값 기반 분류 (스냅샷 없을 때)
        if vph >= surge["vph_min"] * 5:
            return ("급상승", "↑↑", "velocity-surge")
        elif vph >= surge["vph_min"]:
            return ("상승", "↑", "velocity-rising")
        elif vph >= 1000:
            return ("안정", "→", "velocity-stable")
        else:
            return ("하락", "↓", "velocity-falling")


def enrich_videos_with_velocity(videos: list, snapshots_map: Optional[dict] = None) -> list:
    """영상 목록에 VPH, 가속도, 분류를 추가"""
    for v in videos:
        published_at = v.get("published_at", "")
        view_count = v.get("view_count", 0)

        vph = calculate_vph(view_count, published_at) if published_at else 0

        # 이전 스냅샷이 있으면 가속도 계산
        acceleration = 0.0
        has_snapshot = False
        if snapshots_map and v.get("video_id") in snapshots_map:
            prev = snapshots_map[v["video_id"]]
            prev_vph = calculate_vph(prev.get("view_count", 0), published_at)
            acceleration = calculate_acceleration(vph, prev_vph)
            has_snapshot = True

        label, arrow, css_class = classify_velocity(vph, acceleration, has_snapshot)

        v["vph"] = round(vph, 1)
        v["vph_formatted"] = format_count(int(vph)) + "/h"
        v["acceleration"] = round(acceleration, 1)
        v["velocity_label"] = label
        v["velocity_arrow"] = arrow
        v["velocity_css"] = css_class

    return videos


def get_velocity_summary(videos: list) -> dict:
    """속도 분류별 영상 수 요약"""
    summary = {"급상승": 0, "상승": 0, "안정": 0, "하락": 0}
    for v in videos:
        label = v.get("velocity_label", "안정")
        if label in summary:
            summary[label] += 1
    return summary

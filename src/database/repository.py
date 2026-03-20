"""데이터 접근 레이어 - CRUD 및 분석 쿼리"""
import json
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Optional

from src.database.models import init_db

logger = logging.getLogger(__name__)

# SQL Injection 방지 — 허용 컬럼 화이트리스트
_CALENDAR_COLUMNS = frozenset({
    "title", "planned_date", "keyword", "source_type",
    "status", "priority", "notes",
})


class TrendRepository:
    def __init__(self, db_path: str):
        self.db_path = str(db_path)
        init_db(self.db_path)

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # ── 인기 영상 ──

    def save_trending_videos(self, videos: list[dict], collected_at: str,
                             source_type: str = "realtime") -> int:
        conn = self._conn()
        saved = 0
        try:
            for v in videos:
                try:
                    conn.execute(
                        """INSERT OR REPLACE INTO trending_videos
                        (video_id, collected_at, title, description, channel_id, channel_title,
                         subscriber_count, published_at, category_id, category_name, tags,
                         thumbnail_url, duration, view_count, like_count, comment_count,
                         performance_ratio, performance_stars, trending_rank, source_type)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (
                            v["video_id"], collected_at, v["title"], v.get("description", ""),
                            v["channel_id"], v["channel_title"], v.get("subscriber_count", 0),
                            v.get("published_at"), v.get("category_id"), v.get("category_name"),
                            json.dumps(v.get("tags", []), ensure_ascii=False),
                            v.get("thumbnail_url"), v.get("duration"),
                            v.get("view_count", 0), v.get("like_count", 0), v.get("comment_count", 0),
                            v.get("performance_ratio", 0), v.get("performance_stars", 1),
                            v.get("trending_rank"), source_type,
                        ),
                    )
                    saved += 1
                except sqlite3.Error as e:
                    logger.warning("DB 저장 실패: %s", e)
                    continue
            conn.commit()
        finally:
            conn.close()
        return saved

    def get_latest_trending(self, limit: int = 30) -> list[dict]:
        conn = self._conn()
        try:
            rows = conn.execute(
                """SELECT * FROM trending_videos
                WHERE collected_at = (SELECT MAX(collected_at) FROM trending_videos)
                ORDER BY trending_rank ASC LIMIT ?""",
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_latest_by_source(self, source_type: str, limit: int = 30) -> list[dict]:
        conn = self._conn()
        try:
            rows = conn.execute(
                """SELECT * FROM trending_videos
                WHERE source_type = ? AND collected_at = (
                    SELECT MAX(collected_at) FROM trending_videos WHERE source_type = ?
                )
                ORDER BY trending_rank ASC LIMIT ?""",
                (source_type, source_type, limit),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_trending_by_date_range(self, start: str, end: str) -> list:
        conn = self._conn()
        try:
            rows = conn.execute(
                """SELECT * FROM trending_videos
                WHERE collected_at BETWEEN ? AND ?
                ORDER BY view_count DESC""",
                (start, end),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_trending_within_hours(self, hours: int = 24, limit: int = 50) -> list:
        """최근 N시간 이내 수집된 트렌딩 영상 (중복 제거, 최신 데이터 우선)"""
        conn = self._conn()
        try:
            cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()
            rows = conn.execute(
                """SELECT * FROM trending_videos
                WHERE collected_at >= ?
                GROUP BY video_id
                HAVING collected_at = MAX(collected_at)
                ORDER BY view_count DESC LIMIT ?""",
                (cutoff, limit),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_all_trending_deduplicated(self) -> list[dict]:
        """누적 수집된 전체 트렌딩 영상 (video_id 중복 제거, 최신 수집분 우선)."""
        conn = self._conn()
        try:
            rows = conn.execute(
                """SELECT * FROM trending_videos
                WHERE collected_at = (
                    SELECT MAX(t2.collected_at) FROM trending_videos t2
                    WHERE t2.video_id = trending_videos.video_id
                )
                ORDER BY view_count DESC""",
            ).fetchall()
            seen = set()
            result = []
            for r in rows:
                d = dict(r)
                if d["video_id"] not in seen:
                    seen.add(d["video_id"])
                    result.append(d)
            return result
        finally:
            conn.close()

    # ── 검색 결과 ──

    def save_search_results(self, keyword: str, videos: list[dict], collected_at: str) -> int:
        conn = self._conn()
        saved = 0
        try:
            for v in videos:
                try:
                    conn.execute(
                        """INSERT OR REPLACE INTO search_results
                        (keyword, video_id, collected_at, title, channel_id, channel_title,
                         subscriber_count, view_count, like_count, comment_count,
                         thumbnail_url, published_at, duration, tags,
                         performance_ratio, performance_stars, search_rank)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (
                            keyword, v["video_id"], collected_at, v["title"],
                            v["channel_id"], v["channel_title"], v.get("subscriber_count", 0),
                            v.get("view_count", 0), v.get("like_count", 0), v.get("comment_count", 0),
                            v.get("thumbnail_url"), v.get("published_at"), v.get("duration"),
                            json.dumps(v.get("tags", []), ensure_ascii=False),
                            v.get("performance_ratio", 0), v.get("performance_stars", 1),
                            v.get("search_rank"),
                        ),
                    )
                    saved += 1
                except sqlite3.Error as e:
                    logger.warning("DB 저장 실패: %s", e)
                    continue
            conn.commit()
        finally:
            conn.close()
        return saved

    def get_search_results(self, keyword: str, limit: int = 50) -> list[dict]:
        conn = self._conn()
        try:
            rows = conn.execute(
                """SELECT * FROM search_results
                WHERE keyword = ? AND collected_at = (
                    SELECT MAX(collected_at) FROM search_results WHERE keyword = ?
                )
                ORDER BY view_count DESC LIMIT ?""",
                (keyword, keyword, limit),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    # ── 수집 로그 ──

    def log_start(self, run_type: str) -> int:
        conn = self._conn()
        try:
            cursor = conn.execute(
                "INSERT INTO collection_logs (run_started_at, run_type) VALUES (?, ?)",
                (datetime.now().isoformat(), run_type),
            )
            log_id = cursor.lastrowid
            conn.commit()
            return log_id
        finally:
            conn.close()

    def log_end(self, log_id: int, status: str, videos: int, quota: int, error: Optional[str] = None):
        conn = self._conn()
        try:
            conn.execute(
                """UPDATE collection_logs
                SET run_finished_at=?, status=?, videos_collected=?, quota_used=?, error_message=?
                WHERE id=?""",
                (datetime.now().isoformat(), status, videos, quota, error, log_id),
            )
            conn.commit()
        finally:
            conn.close()

    def get_recent_logs(self, limit: int = 20) -> list[dict]:
        conn = self._conn()
        try:
            rows = conn.execute(
                "SELECT * FROM collection_logs ORDER BY run_started_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_today_quota_used(self) -> int:
        """오늘(UTC) 사용한 API 할당량 합계를 반환한다."""
        conn = self._conn()
        try:
            row = conn.execute(
                "SELECT COALESCE(SUM(quota_used), 0) AS total "
                "FROM collection_logs WHERE date(run_started_at) = date('now')"
            ).fetchone()
            return row["total"] if row else 0
        finally:
            conn.close()

    def get_last_collection_time(self) -> Optional[str]:
        conn = self._conn()
        try:
            row = conn.execute(
                "SELECT MAX(collected_at) as last_time FROM trending_videos"
            ).fetchone()
            return row["last_time"] if row and row["last_time"] else None
        finally:
            conn.close()

    # ═══ PRO 업그레이드 메서드 ═══

    # ── 영상 스냅샷 (VPH 계산용) ──

    def save_video_snapshot(self, video_id: str, view_count: int,
                            like_count: int = 0, comment_count: int = 0) -> None:
        conn = self._conn()
        try:
            conn.execute(
                """INSERT OR IGNORE INTO video_snapshots
                (video_id, snapshot_at, view_count, like_count, comment_count)
                VALUES (?, ?, ?, ?, ?)""",
                (video_id, datetime.now().isoformat(), view_count, like_count, comment_count),
            )
            conn.commit()
        except sqlite3.Error as e:
            logger.warning("DB 저장 실패: %s", e)
        finally:
            conn.close()

    def save_video_snapshots_bulk(self, videos: list) -> int:
        conn = self._conn()
        now = datetime.now().isoformat()
        saved = 0
        try:
            for v in videos:
                try:
                    conn.execute(
                        """INSERT OR IGNORE INTO video_snapshots
                        (video_id, snapshot_at, view_count, like_count, comment_count)
                        VALUES (?, ?, ?, ?, ?)""",
                        (v["video_id"], now, v.get("view_count", 0),
                         v.get("like_count", 0), v.get("comment_count", 0)),
                    )
                    saved += 1
                except sqlite3.Error as e:
                    logger.warning("DB 저장 실패: %s", e)
                    continue
            conn.commit()
        finally:
            conn.close()
        return saved

    def get_video_snapshots(self, video_id: str, hours: int = 24) -> list:
        conn = self._conn()
        try:
            cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()
            rows = conn.execute(
                """SELECT * FROM video_snapshots
                WHERE video_id = ? AND snapshot_at >= ?
                ORDER BY snapshot_at ASC""",
                (video_id, cutoff),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_latest_snapshots_for_videos(self, video_ids: list) -> list:
        if not video_ids:
            return []
        conn = self._conn()
        try:
            placeholders = ",".join("?" * len(video_ids))
            rows = conn.execute(
                f"""SELECT vs.* FROM video_snapshots vs
                INNER JOIN (
                    SELECT video_id, MAX(snapshot_at) as max_at
                    FROM video_snapshots WHERE video_id IN ({placeholders})
                    GROUP BY video_id
                ) latest ON vs.video_id = latest.video_id AND vs.snapshot_at = latest.max_at""",
                video_ids,
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    # ── 추적 채널 ──

    def add_tracked_channel(self, channel: dict) -> int:
        conn = self._conn()
        try:
            cursor = conn.execute(
                """INSERT OR REPLACE INTO tracked_channels
                (channel_id, channel_title, subscriber_count, avg_view_count,
                 thumbnail_url, added_at, is_active)
                VALUES (?, ?, ?, ?, ?, ?, 1)""",
                (channel["channel_id"], channel.get("channel_title", ""),
                 channel.get("subscriber_count", 0), channel.get("avg_view_count", 0),
                 channel.get("thumbnail_url", ""), datetime.now().isoformat()),
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def get_tracked_channels(self) -> list:
        conn = self._conn()
        try:
            rows = conn.execute(
                "SELECT * FROM tracked_channels WHERE is_active = 1 ORDER BY added_at DESC"
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def remove_tracked_channel(self, channel_id: str) -> None:
        conn = self._conn()
        try:
            conn.execute(
                "UPDATE tracked_channels SET is_active = 0 WHERE channel_id = ?",
                (channel_id,),
            )
            conn.commit()
        finally:
            conn.close()

    def update_channel_stats(self, channel_id: str, stats: dict) -> None:
        conn = self._conn()
        try:
            conn.execute(
                """UPDATE tracked_channels
                SET subscriber_count=?, avg_view_count=?, last_checked_at=?
                WHERE channel_id=?""",
                (stats.get("subscriber_count", 0), stats.get("avg_view_count", 0),
                 datetime.now().isoformat(), channel_id),
            )
            conn.commit()
        finally:
            conn.close()

    # ── 채널 영상 ──

    def save_channel_video(self, video: dict) -> None:
        conn = self._conn()
        try:
            conn.execute(
                """INSERT OR REPLACE INTO channel_videos
                (channel_id, video_id, title, thumbnail_url, published_at,
                 view_count, like_count, comment_count, tags, category_name,
                 duration, performance_vs_avg)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (video["channel_id"], video["video_id"], video.get("title", ""),
                 video.get("thumbnail_url", ""), video.get("published_at"),
                 video.get("view_count", 0), video.get("like_count", 0),
                 video.get("comment_count", 0),
                 json.dumps(video.get("tags", []), ensure_ascii=False),
                 video.get("category_name", ""), video.get("duration", ""),
                 video.get("performance_vs_avg", 0)),
            )
            conn.commit()
        except sqlite3.Error as e:
            logger.warning("DB 저장 실패: %s", e)
        finally:
            conn.close()

    def save_channel_videos_bulk(self, videos: list) -> int:
        conn = self._conn()
        saved = 0
        try:
            for v in videos:
                try:
                    conn.execute(
                        """INSERT OR REPLACE INTO channel_videos
                        (channel_id, video_id, title, thumbnail_url, published_at,
                         view_count, like_count, comment_count, tags, category_name,
                         duration, performance_vs_avg)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (v["channel_id"], v["video_id"], v.get("title", ""),
                         v.get("thumbnail_url", ""), v.get("published_at"),
                         v.get("view_count", 0), v.get("like_count", 0),
                         v.get("comment_count", 0),
                         json.dumps(v.get("tags", []), ensure_ascii=False),
                         v.get("category_name", ""), v.get("duration", ""),
                         v.get("performance_vs_avg", 0)),
                    )
                    saved += 1
                except sqlite3.Error as e:
                    logger.warning("DB 저장 실패: %s", e)
                    continue
            conn.commit()
        finally:
            conn.close()
        return saved

    def get_channel_videos(self, channel_id: str, days: int = 7) -> list:
        conn = self._conn()
        try:
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            rows = conn.execute(
                """SELECT * FROM channel_videos
                WHERE channel_id = ? AND published_at >= ?
                ORDER BY published_at DESC""",
                (channel_id, cutoff),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_all_channel_videos(self, days: int = 7) -> list:
        conn = self._conn()
        try:
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            rows = conn.execute(
                """SELECT cv.*, tc.channel_title, tc.avg_view_count as channel_avg
                FROM channel_videos cv
                JOIN tracked_channels tc ON cv.channel_id = tc.channel_id
                WHERE tc.is_active = 1 AND cv.published_at >= ?
                ORDER BY cv.published_at DESC""",
                (cutoff,),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_overperforming_videos(self, threshold: float = 1.5) -> list:
        conn = self._conn()
        try:
            rows = conn.execute(
                """SELECT cv.*, tc.channel_title, tc.avg_view_count as channel_avg
                FROM channel_videos cv
                JOIN tracked_channels tc ON cv.channel_id = tc.channel_id
                WHERE tc.is_active = 1 AND cv.performance_vs_avg >= ?
                ORDER BY cv.performance_vs_avg DESC""",
                (threshold,),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    # ── 브레이크아웃 키워드 ──

    def save_breakout_keywords(self, keywords: list) -> int:
        conn = self._conn()
        now = datetime.now().isoformat()
        saved = 0
        try:
            for kw in keywords:
                try:
                    conn.execute(
                        """INSERT OR REPLACE INTO breakout_keywords
                        (keyword, detected_at, trend_surge_pct, trend_interest,
                         youtube_video_count, youtube_avg_views, opportunity_score, category)
                        VALUES (?,?,?,?,?,?,?,?)""",
                        (kw["keyword"], now,
                         kw.get("trend_surge_pct", kw.get("surge_pct", 0)),
                         kw.get("trend_interest", kw.get("interest", 0)),
                         kw.get("youtube_video_count", 0),
                         kw.get("youtube_avg_views", 0), kw.get("opportunity_score", 0),
                         kw.get("category", "")),
                    )
                    saved += 1
                except sqlite3.Error as e:
                    logger.warning("DB 저장 실패: %s", e)
                    continue
            conn.commit()
        finally:
            conn.close()
        return saved

    def get_recent_breakout_keywords(self, hours: int = 24) -> list:
        conn = self._conn()
        try:
            cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()
            rows = conn.execute(
                """SELECT * FROM breakout_keywords
                WHERE detected_at >= ?
                ORDER BY opportunity_score DESC""",
                (cutoff,),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    # ── 키워드 갭 ──

    def save_keyword_gaps(self, gaps: list) -> int:
        conn = self._conn()
        now = datetime.now().isoformat()
        saved = 0
        try:
            for g in gaps:
                try:
                    conn.execute(
                        """INSERT OR REPLACE INTO keyword_gaps
                        (keyword, analyzed_at, demand_score, supply_score,
                         opportunity_score, video_count_7d, avg_views_7d, competition_level)
                        VALUES (?,?,?,?,?,?,?,?)""",
                        (g["keyword"], now, g.get("demand_score", 0),
                         g.get("supply_score", 0), g.get("opportunity_score", 0),
                         g.get("video_count_7d", 0), g.get("avg_views_7d", 0),
                         g.get("competition_level", "medium")),
                    )
                    saved += 1
                except sqlite3.Error as e:
                    logger.warning("DB 저장 실패: %s", e)
                    continue
            conn.commit()
        finally:
            conn.close()
        return saved

    def get_keyword_gaps(self, keyword: Optional[str] = None) -> list:
        conn = self._conn()
        try:
            if keyword:
                rows = conn.execute(
                    """SELECT * FROM keyword_gaps
                    WHERE keyword = ? ORDER BY analyzed_at DESC LIMIT 1""",
                    (keyword,),
                ).fetchall()
            else:
                rows = conn.execute(
                    """SELECT * FROM keyword_gaps
                    WHERE analyzed_at = (SELECT MAX(analyzed_at) FROM keyword_gaps)
                    ORDER BY opportunity_score DESC"""
                ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    # ── 콘텐츠 캘린더 ──

    def add_calendar_item(self, item: dict) -> int:
        conn = self._conn()
        try:
            cursor = conn.execute(
                """INSERT INTO content_calendar
                (title, planned_date, keyword, source_type, status, priority, notes)
                VALUES (?,?,?,?,?,?,?)""",
                (item["title"], item["planned_date"], item.get("keyword", ""),
                 item.get("source_type", "manual"), item.get("status", "planned"),
                 item.get("priority", "medium"), item.get("notes", "")),
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def get_calendar_items(self, start_date: str, end_date: str) -> list:
        conn = self._conn()
        try:
            rows = conn.execute(
                """SELECT * FROM content_calendar
                WHERE planned_date BETWEEN ? AND ?
                ORDER BY planned_date ASC""",
                (start_date, end_date),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def update_calendar_item(self, item_id: int, updates: dict) -> None:
        safe_updates = {k: v for k, v in updates.items() if k in _CALENDAR_COLUMNS}
        if not safe_updates:
            return
        conn = self._conn()
        try:
            sets = ", ".join(f"{k}=?" for k in safe_updates.keys())
            values = list(safe_updates.values()) + [item_id]
            conn.execute(f"UPDATE content_calendar SET {sets} WHERE id=?", values)
            conn.commit()
        finally:
            conn.close()

    def delete_calendar_item(self, item_id: int) -> None:
        conn = self._conn()
        try:
            conn.execute("DELETE FROM content_calendar WHERE id=?", (item_id,))
            conn.commit()
        finally:
            conn.close()

    # ── 시즌 트렌드 ──

    def get_seasonal_keywords(self, month: int) -> list:
        conn = self._conn()
        try:
            rows = conn.execute(
                "SELECT * FROM seasonal_trends WHERE peak_month = ? ORDER BY confidence DESC",
                (month,),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def save_seasonal_trend(self, trend: dict) -> None:
        conn = self._conn()
        try:
            conn.execute(
                """INSERT OR REPLACE INTO seasonal_trends
                (keyword, peak_month, peak_week, confidence, category)
                VALUES (?,?,?,?,?)""",
                (trend["keyword"], trend["peak_month"], trend.get("peak_week"),
                 trend.get("confidence", 0), trend.get("category", "")),
            )
            conn.commit()
        except sqlite3.Error as e:
            logger.warning("DB 저장 실패: %s", e)
        finally:
            conn.close()

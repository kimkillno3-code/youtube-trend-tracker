"""SQLite 테이블 생성 및 마이그레이션"""
import sqlite3
from pathlib import Path


def init_db(db_path: str) -> None:
    """데이터베이스 초기화 - 테이블 및 인덱스 생성"""
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.executescript("""
        -- 인기 영상 스냅샷
        CREATE TABLE IF NOT EXISTS trending_videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id TEXT NOT NULL,
            collected_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            title TEXT NOT NULL,
            description TEXT,
            channel_id TEXT NOT NULL,
            channel_title TEXT,
            subscriber_count INTEGER DEFAULT 0,
            published_at TIMESTAMP,
            category_id INTEGER,
            category_name TEXT,
            tags TEXT,
            thumbnail_url TEXT,
            duration TEXT,
            view_count INTEGER DEFAULT 0,
            like_count INTEGER DEFAULT 0,
            comment_count INTEGER DEFAULT 0,
            performance_ratio REAL DEFAULT 0,
            performance_stars INTEGER DEFAULT 1,
            trending_rank INTEGER,
            source_type TEXT DEFAULT 'realtime',
            UNIQUE(video_id, collected_at)
        );

        -- 키워드 검색 결과
        CREATE TABLE IF NOT EXISTS search_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT NOT NULL,
            video_id TEXT NOT NULL,
            collected_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            title TEXT,
            channel_id TEXT,
            channel_title TEXT,
            subscriber_count INTEGER DEFAULT 0,
            view_count INTEGER DEFAULT 0,
            like_count INTEGER DEFAULT 0,
            comment_count INTEGER DEFAULT 0,
            thumbnail_url TEXT,
            published_at TIMESTAMP,
            duration TEXT,
            tags TEXT,
            performance_ratio REAL DEFAULT 0,
            performance_stars INTEGER DEFAULT 1,
            search_rank INTEGER,
            UNIQUE(keyword, video_id, collected_at)
        );

        -- 수집 실행 기록
        CREATE TABLE IF NOT EXISTS collection_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_started_at TIMESTAMP NOT NULL,
            run_finished_at TIMESTAMP,
            run_type TEXT NOT NULL,
            status TEXT DEFAULT 'running',
            videos_collected INTEGER DEFAULT 0,
            quota_used INTEGER DEFAULT 0,
            error_message TEXT
        );

        -- 인덱스
        CREATE INDEX IF NOT EXISTS idx_trending_video_id ON trending_videos(video_id);
        CREATE INDEX IF NOT EXISTS idx_trending_collected ON trending_videos(collected_at);
        CREATE INDEX IF NOT EXISTS idx_trending_views ON trending_videos(view_count DESC);
        CREATE INDEX IF NOT EXISTS idx_trending_category ON trending_videos(category_id);

        CREATE INDEX IF NOT EXISTS idx_search_keyword ON search_results(keyword);
        CREATE INDEX IF NOT EXISTS idx_search_collected ON search_results(collected_at);
        CREATE INDEX IF NOT EXISTS idx_search_views ON search_results(view_count DESC);

        CREATE INDEX IF NOT EXISTS idx_logs_started ON collection_logs(run_started_at);

        -- ═══ PRO 업그레이드 테이블 ═══

        -- 영상 조회수 스냅샷 (VPH 계산용)
        CREATE TABLE IF NOT EXISTS video_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id TEXT NOT NULL,
            snapshot_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            view_count INTEGER DEFAULT 0,
            like_count INTEGER DEFAULT 0,
            comment_count INTEGER DEFAULT 0,
            UNIQUE(video_id, snapshot_at)
        );
        CREATE INDEX IF NOT EXISTS idx_snapshots_video ON video_snapshots(video_id);
        CREATE INDEX IF NOT EXISTS idx_snapshots_time ON video_snapshots(snapshot_at);

        -- 추적 대상 채널
        CREATE TABLE IF NOT EXISTS tracked_channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id TEXT NOT NULL UNIQUE,
            channel_title TEXT,
            subscriber_count INTEGER DEFAULT 0,
            avg_view_count INTEGER DEFAULT 0,
            thumbnail_url TEXT,
            added_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            last_checked_at TIMESTAMP,
            is_active INTEGER DEFAULT 1
        );
        CREATE INDEX IF NOT EXISTS idx_tracked_channel_id ON tracked_channels(channel_id);

        -- 추적 채널의 영상 기록
        CREATE TABLE IF NOT EXISTS channel_videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id TEXT NOT NULL,
            video_id TEXT NOT NULL,
            title TEXT,
            thumbnail_url TEXT,
            published_at TIMESTAMP,
            view_count INTEGER DEFAULT 0,
            like_count INTEGER DEFAULT 0,
            comment_count INTEGER DEFAULT 0,
            tags TEXT,
            category_name TEXT,
            duration TEXT,
            performance_vs_avg REAL DEFAULT 0,
            first_seen_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(channel_id, video_id)
        );
        CREATE INDEX IF NOT EXISTS idx_channel_videos_channel ON channel_videos(channel_id);
        CREATE INDEX IF NOT EXISTS idx_channel_videos_published ON channel_videos(published_at);
        CREATE INDEX IF NOT EXISTS idx_channel_videos_perf ON channel_videos(performance_vs_avg DESC);

        -- 브레이크아웃 키워드 기록
        CREATE TABLE IF NOT EXISTS breakout_keywords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT NOT NULL,
            detected_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            trend_surge_pct REAL DEFAULT 0,
            trend_interest INTEGER DEFAULT 0,
            youtube_video_count INTEGER DEFAULT 0,
            youtube_avg_views INTEGER DEFAULT 0,
            opportunity_score REAL DEFAULT 0,
            category TEXT,
            UNIQUE(keyword, detected_at)
        );
        CREATE INDEX IF NOT EXISTS idx_breakout_keyword ON breakout_keywords(keyword);
        CREATE INDEX IF NOT EXISTS idx_breakout_detected ON breakout_keywords(detected_at);
        CREATE INDEX IF NOT EXISTS idx_breakout_score ON breakout_keywords(opportunity_score DESC);

        -- 키워드 갭 분석 결과
        CREATE TABLE IF NOT EXISTS keyword_gaps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT NOT NULL,
            analyzed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            demand_score REAL DEFAULT 0,
            supply_score REAL DEFAULT 0,
            opportunity_score REAL DEFAULT 0,
            video_count_7d INTEGER DEFAULT 0,
            avg_views_7d INTEGER DEFAULT 0,
            competition_level TEXT DEFAULT 'medium',
            UNIQUE(keyword, analyzed_at)
        );
        CREATE INDEX IF NOT EXISTS idx_gap_keyword ON keyword_gaps(keyword);
        CREATE INDEX IF NOT EXISTS idx_gap_opportunity ON keyword_gaps(opportunity_score DESC);

        -- 콘텐츠 캘린더
        CREATE TABLE IF NOT EXISTS content_calendar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            planned_date TEXT NOT NULL,
            keyword TEXT,
            source_type TEXT DEFAULT 'manual',
            status TEXT DEFAULT 'planned',
            priority TEXT DEFAULT 'medium',
            notes TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_calendar_date ON content_calendar(planned_date);
        CREATE INDEX IF NOT EXISTS idx_calendar_status ON content_calendar(status);

        -- 시즌 트렌드 패턴
        CREATE TABLE IF NOT EXISTS seasonal_trends (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT NOT NULL,
            peak_month INTEGER NOT NULL,
            peak_week INTEGER,
            confidence REAL DEFAULT 0,
            category TEXT,
            UNIQUE(keyword, peak_month)
        );
        CREATE INDEX IF NOT EXISTS idx_seasonal_keyword ON seasonal_trends(keyword);
        CREATE INDEX IF NOT EXISTS idx_seasonal_month ON seasonal_trends(peak_month);
    """)

    conn.commit()

    # ── 마이그레이션: 기존 테이블에 source_type 컬럼 추가 ──
    try:
        cursor.execute(
            "ALTER TABLE trending_videos ADD COLUMN source_type TEXT DEFAULT 'realtime'"
        )
        conn.commit()
    except sqlite3.OperationalError:
        pass  # 이미 존재

    conn.close()

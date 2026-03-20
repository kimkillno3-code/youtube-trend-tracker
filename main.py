"""YouTube 토픽 파인더 - CLI 진입점"""
import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

# 프로젝트 루트를 path에 추가
sys.path.insert(0, str(Path(__file__).parent))

from src.config import YOUTUBE_API_KEY, NOTIFICATION_CHANNELS, DB_PATH, DATA_DIR
from src.collector.youtube_api import YouTubeAPIClient
from src.collector.trending import collect_trending, save_snapshots
from src.collector.search import search_and_collect
from src.database.repository import TrendRepository
from src.notifier.email import send_email_report
from src.notifier.telegram import send_telegram_report

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def cmd_collect(repo: TrendRepository, api: YouTubeAPIClient, max_results: int = 30):
    """인기 영상 수집"""
    log_id = repo.log_start("auto")
    collected_at = datetime.now().isoformat()

    try:
        videos = collect_trending(api, max_results=max_results)
        saved = repo.save_trending_videos(videos, collected_at)
        save_snapshots(repo, videos)
        repo.log_end(log_id, "success", saved, api.quota_used)
        logger.info(f"✅ {saved}개 영상 저장 완료 (할당량: {api.quota_used})")
        return videos
    except Exception as e:
        repo.log_end(log_id, "failed", 0, api.quota_used, str(e))
        logger.error(f"❌ 수집 실패: {e}")
        return []


def cmd_search(repo: TrendRepository, api: YouTubeAPIClient, keyword: str,
               max_results: int = 25, order: str = "viewCount", days: int = 7):
    """키워드 검색"""
    log_id = repo.log_start("search")
    collected_at = datetime.now().isoformat()

    try:
        videos = search_and_collect(api, keyword, max_results=max_results, order=order, days_ago=days)
        saved = repo.save_search_results(keyword, videos, collected_at)
        repo.log_end(log_id, "success", saved, api.quota_used)
        logger.info(f'✅ "{keyword}" 검색: {saved}개 저장 (할당량: {api.quota_used})')
        return videos
    except Exception as e:
        repo.log_end(log_id, "failed", 0, api.quota_used, str(e))
        logger.error(f"❌ 검색 실패: {e}")
        return []


def cmd_notify(videos: list):
    """알림 발송"""
    if not videos:
        logger.warning("알림 보낼 데이터가 없습니다")
        return

    if "email" in NOTIFICATION_CHANNELS:
        send_email_report(videos)
    if "telegram" in NOTIFICATION_CHANNELS:
        send_telegram_report(videos)


def main():
    parser = argparse.ArgumentParser(description="YouTube 토픽 파인더")
    parser.add_argument("--collect", action="store_true", help="인기 영상 수집")
    parser.add_argument("--search", type=str, help="키워드 검색")
    parser.add_argument("--notify", action="store_true", help="알림 발송")
    parser.add_argument("--max-results", type=int, default=30, help="최대 수집 수 (기본: 30)")
    parser.add_argument("--order", type=str, default="viewCount", help="정렬 (viewCount/date/relevance)")
    parser.add_argument("--days", type=int, default=7, help="검색 기간 (일, 기본: 7)")
    args = parser.parse_args()

    if not YOUTUBE_API_KEY:
        logger.error("YOUTUBE_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")
        sys.exit(1)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    repo = TrendRepository(DB_PATH)
    api = YouTubeAPIClient(YOUTUBE_API_KEY)

    videos = []

    if args.collect:
        videos = cmd_collect(repo, api, args.max_results)

    if args.search:
        videos = cmd_search(repo, api, args.search, args.max_results, args.order, args.days)

    if args.notify:
        if not videos:
            videos = repo.get_latest_trending()
        cmd_notify(videos)

    if not args.collect and not args.search and not args.notify:
        parser.print_help()


if __name__ == "__main__":
    main()

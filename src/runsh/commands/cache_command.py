# commands/cache_command.py - 캐시 관리 명령어

import shutil
import json
from datetime import datetime
from pathlib import Path
from cleo.commands.command import Command
from cleo.helpers import argument, option

from ..constants import RUNSH_DIR, CACHE_DIR, CACHE_METADATA_FILE


class CacheCommand(Command):
    """캐시 관리 명령어"""

    name = "cache-rs"
    description = "Manage script cache"

    arguments = [
        argument(
            "action",
            "Action to perform (clean, list, info)",
            optional=True,
            default="list",
        )
    ]

    options = [option("all", "a", "Clean all cache (not just expired)", flag=True)]

    def handle(self):
        action = self.argument("action")

        if action == "clean":
            return self._clean_cache()
        elif action == "list":
            return self._list_cache()
        elif action == "info":
            return self._show_cache_info()
        else:
            self.error(f"Unknown action: {action}")
            self.line("Available actions: clean, list, info")
            return 1

    def _clean_cache(self):
        """캐시 정리"""
        cache_root = Path.cwd() / RUNSH_DIR / CACHE_DIR

        if not cache_root.exists():
            self.info("No cache directory found")
            return 0

        all_cache = self.option("all")

        # 캐시 항목들 찾기
        cache_dirs = [d for d in cache_root.iterdir() if d.is_dir()]

        if not cache_dirs:
            self.info("Cache is empty")
            return 0

        if all_cache:
            # 모든 캐시 삭제
            for cache_dir in cache_dirs:
                shutil.rmtree(cache_dir)

            self.info(f"Deleted {len(cache_dirs)} cache entries")
        else:
            # 만료된 캐시만 삭제
            expired_count = 0
            for cache_dir in cache_dirs:
                if self._is_cache_expired(cache_dir):
                    shutil.rmtree(cache_dir)
                    expired_count += 1

            if expired_count > 0:
                self.info(f"Deleted {expired_count} expired cache entries")
            else:
                self.info("No expired cache found")

        return 0

    def _list_cache(self):
        """캐시 목록 표시"""
        cache_root = Path.cwd() / RUNSH_DIR / CACHE_DIR

        if not cache_root.exists():
            self.info("No cache directory found")
            return 0

        cache_dirs = [d for d in cache_root.iterdir() if d.is_dir()]

        if not cache_dirs:
            self.info("Cache is empty")
            return 0

        self.line(f"Found {len(cache_dirs)} cache entries:")
        self.line("")

        for cache_dir in cache_dirs:
            metadata = self._load_metadata(cache_dir)

            if metadata:
                status = "expired" if self._is_cache_expired(cache_dir) else "valid"
                scripts_count = metadata.get("script_count", 0)
                cached_at = metadata.get("cached_at", "unknown")
                url = metadata.get("url", "unknown")

                self.line(f"  <info>{cache_dir.name}</info>")
                self.line(f"    URL: {url}")
                self.line(f"    Scripts: {scripts_count}")
                self.line(f"    Cached: {cached_at}")
                if status == "expired":
                    self.line(f"    Status: <comment>{status}</comment>")
                else:
                    self.line(f"    Status: <info>{status}</info>")
                self.line("")
            else:
                self.line(f"  <comment>{cache_dir.name}</comment> (no metadata)")
                self.line("")

        return 0

    def _show_cache_info(self):
        """캐시 정보 표시"""
        cache_root = Path.cwd() / RUNSH_DIR / CACHE_DIR

        if not cache_root.exists():
            self.info("No cache directory found")
            return 0

        cache_dirs = [d for d in cache_root.iterdir() if d.is_dir()]
        total_size = self._calculate_cache_size(cache_root)
        valid_count = sum(1 for d in cache_dirs if not self._is_cache_expired(d))
        expired_count = len(cache_dirs) - valid_count

        self.line("Cache Information:")
        self.line(f"  Location: {cache_root}")
        self.line(f"  Total entries: {len(cache_dirs)}")
        self.line(f"  Valid entries: {valid_count}")
        self.line(f"  Expired entries: {expired_count}")
        self.line(f"  Total size: {self._format_size(total_size)}")

        return 0

    def _is_cache_expired(self, cache_dir: Path) -> bool:
        """캐시가 만료되었는지 확인"""
        metadata_file = cache_dir / CACHE_METADATA_FILE

        if not metadata_file.exists():
            return True

        try:
            with open(metadata_file, "r") as f:
                metadata = json.load(f)

            cached_time = datetime.fromisoformat(metadata["cached_at"])
            from ..constants import CACHE_MAX_AGE_HOURS
            from datetime import timedelta

            max_age = timedelta(hours=CACHE_MAX_AGE_HOURS)

            return datetime.now() - cached_time > max_age
        except:
            return True

    def _load_metadata(self, cache_dir: Path) -> dict:
        """캐시 메타데이터 로드"""
        metadata_file = cache_dir / CACHE_METADATA_FILE

        if not metadata_file.exists():
            return {}

        try:
            with open(metadata_file, "r") as f:
                return json.load(f)
        except:
            return {}

    def _calculate_cache_size(self, cache_root: Path) -> int:
        """캐시 총 크기 계산"""
        total_size = 0

        for file_path in cache_root.rglob("*"):
            if file_path.is_file():
                total_size += file_path.stat().st_size

        return total_size

    def _format_size(self, size_bytes: int) -> str:
        """파일 크기를 읽기 쉬운 형태로 변환"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"

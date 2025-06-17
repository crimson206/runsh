# config/github.py - GitHub 레포지토리 스크립트 프로바이더 (캐시 지원)

import re
import os
import json
import hashlib
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Tuple, Optional
from urllib.parse import urlparse

from ..constants import RUNSH_DIR, CACHE_DIR, CACHE_METADATA_FILE, CACHE_MAX_AGE_HOURS


class GitHubProvider:
    """GitHub 레포지토리에서 스크립트를 가져오는 프로바이더 (캐시 지원)"""

    def __init__(self, github_url: str):
        self.github_url = github_url
        self.api_url = self._convert_to_api_url(github_url)
        self.cache_dir = self._get_cache_dir()

    def get_scripts(self) -> List[Tuple[str, str]]:
        """GitHub에서 스크립트 가져오기 (캐시 우선)"""
        # 캐시 확인
        if self._is_cache_valid():
            scripts = self._load_from_cache()
            if scripts:
                return scripts

        # 캐시가 없거나 만료됨 - GitHub에서 새로 가져오기
        scripts = self._fetch_from_github()
        if scripts:
            self._save_to_cache(scripts)

        return scripts

    def is_available(self) -> bool:
        """GitHub API에 접근 가능한지 확인"""
        # 캐시가 있으면 사용 가능
        if self._is_cache_valid():
            return True

        # 캐시가 없으면 GitHub API 확인
        try:
            response = requests.head(self.api_url, timeout=5)
            return response.status_code == 200
        except:
            return False

    def clear_cache(self):
        """캐시 삭제"""
        if self.cache_dir.exists():
            import shutil

            shutil.rmtree(self.cache_dir)

    def _get_cache_dir(self) -> Path:
        """캐시 디렉토리 경로 생성"""
        # URL을 안전한 디렉토리명으로 변환
        url_hash = hashlib.md5(self.github_url.encode()).hexdigest()[:16]

        # GitHub URL에서 repo 정보 추출
        pattern = r"github\.com/([^/]+)/([^/]+)(?:/tree/([^/]+))?(?:/(.+))?"
        match = re.search(pattern, self.github_url)

        if match:
            owner, repo, branch, path = match.groups()
            branch = branch or "main"
            path = path or "scripts"
            safe_name = f"github_{owner}_{repo}_{branch}_{path.replace('/', '_')}"
        else:
            safe_name = f"github_{url_hash}"

        runsh_dir = Path.cwd() / RUNSH_DIR
        cache_dir = runsh_dir / CACHE_DIR / safe_name
        cache_dir.mkdir(parents=True, exist_ok=True)

        return cache_dir

    def _is_cache_valid(self) -> bool:
        """캐시가 유효한지 확인"""
        metadata_file = self.cache_dir / CACHE_METADATA_FILE

        if not metadata_file.exists():
            return False

        try:
            with open(metadata_file, "r") as f:
                metadata = json.load(f)

            # 시간 체크
            cached_time = datetime.fromisoformat(metadata["cached_at"])
            max_age = timedelta(hours=CACHE_MAX_AGE_HOURS)

            return datetime.now() - cached_time < max_age
        except:
            return False

    def _load_from_cache(self) -> List[Tuple[str, str]]:
        """캐시에서 스크립트 로드"""
        scripts = []

        for script_file in self.cache_dir.glob("*.sh"):
            try:
                with open(script_file, "r", encoding="utf-8") as f:
                    content = f.read()
                scripts.append((str(script_file), content))
            except Exception as e:
                print(f"Warning: Failed to read cached script {script_file}: {e}")

        return scripts

    def _fetch_from_github(self) -> List[Tuple[str, str]]:
        """GitHub에서 새로 가져오기"""
        scripts = []

        try:
            # 디렉토리 내용 가져오기
            files = self._get_directory_contents()
            if not files:
                return scripts

            # .sh 파일만 필터링하고 내용 다운로드
            for file_info in files:
                if file_info.get("type") == "file" and file_info.get(
                    "name", ""
                ).endswith(".sh"):
                    content = self._download_file_content(file_info.get("download_url"))
                    if content:
                        # 캐시 파일 경로
                        cache_file = self.cache_dir / file_info["name"]
                        scripts.append((str(cache_file), content))

        except Exception as e:
            print(f"Warning: Failed to fetch scripts from GitHub: {e}")

        return scripts

    def _save_to_cache(self, scripts: List[Tuple[str, str]]):
        """스크립트를 캐시에 저장"""
        try:
            # 기존 .sh 파일들 삭제
            for old_file in self.cache_dir.glob("*.sh"):
                old_file.unlink()

            # 새 스크립트들 저장
            for script_path, content in scripts:
                script_name = Path(script_path).name
                cache_file = self.cache_dir / script_name

                with open(cache_file, "w", encoding="utf-8") as f:
                    f.write(content)

            # 메타데이터 저장
            metadata = {
                "url": self.github_url,
                "api_url": self.api_url,
                "cached_at": datetime.now().isoformat(),
                "script_count": len(scripts),
            }

            metadata_file = self.cache_dir / CACHE_METADATA_FILE
            with open(metadata_file, "w") as f:
                json.dump(metadata, f, indent=2)

        except Exception as e:
            print(f"Warning: Failed to save to cache: {e}")

    def _convert_to_api_url(self, github_url: str) -> str:
        """GitHub 웹 URL을 API URL로 변환"""
        # https://github.com/user/repo/tree/branch/path
        # → https://api.github.com/repos/user/repo/contents/path?ref=branch

        # URL 파싱
        if "api.github.com" in github_url:
            return github_url  # 이미 API URL

        # 웹 URL 파싱
        pattern = r"github\.com/([^/]+)/([^/]+)(?:/tree/([^/]+))?(?:/(.+))?"
        match = re.search(pattern, github_url)

        if not match:
            raise ValueError(f"Invalid GitHub URL: {github_url}")

        owner, repo, branch, path = match.groups()

        # API URL 구성
        api_url = f"https://api.github.com/repos/{owner}/{repo}/contents"

        if path:
            api_url += f"/{path}"

        if branch:
            api_url += f"?ref={branch}"

        return api_url

    def _get_directory_contents(self) -> Optional[List[dict]]:
        """GitHub API로 디렉토리 내용 가져오기"""
        try:
            response = requests.get(self.api_url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Failed to fetch directory contents: {e}")
            return None

    def _download_file_content(self, download_url: str) -> Optional[str]:
        """파일 내용 다운로드"""
        if not download_url:
            return None

        try:
            response = requests.get(download_url, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Failed to download file content: {e}")
            return None

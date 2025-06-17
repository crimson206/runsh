# config/providers.py - 스크립트 소스 프로바이더 팩토리

from typing import Protocol, List, Tuple
from abc import ABC, abstractmethod


class ScriptProvider(Protocol):
    """스크립트 프로바이더 인터페이스"""

    def get_scripts(self) -> List[Tuple[str, str]]:
        """
        스크립트 목록 반환
        Returns: [(script_name, script_content), ...]
        """
        ...

    def is_available(self) -> bool:
        """프로바이더가 사용 가능한지 확인"""
        ...


def get_provider(scripts_dir: str) -> ScriptProvider:
    """scripts_dir에 맞는 프로바이더 반환"""

    if _is_github_url(scripts_dir):
        from .github import GitHubProvider

        return GitHubProvider(scripts_dir)
    else:
        from .local import LocalProvider

        return LocalProvider(scripts_dir)


def _is_github_url(url: str) -> bool:
    """GitHub URL인지 확인"""
    return "github.com" in url.lower()

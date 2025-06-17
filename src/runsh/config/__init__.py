# config/__init__.py - 설정 관리 및 프로바이더 통합

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

from ..constants import (
    DEFAULT_SCRIPTS_DIR,
    DEFAULT_SHELL,
    SUPPORTED_SHELLS,
    RUNSH_DIR,
    CONFIG_FILENAME,
    ENV_SCRIPTS_DIR,
    ENV_SHELL,
)
from .providers import get_provider


class Config:
    """설정 관리 클래스"""

    def __init__(self):
        self.scripts_dir = None
        self.default_shell = DEFAULT_SHELL
        self._load_config()

    def _load_config(self):
        """설정 로딩 (우선순위: 설정파일 > 환경변수 > 기본값)"""
        # 1. 기본값 설정
        config = get_default_config()

        # 2. 설정 파일에서 로딩
        file_config = load_config_file()
        if file_config:
            config.update(file_config)

        # 3. 환경변수에서 로딩
        env_config = load_env_config()
        config.update(env_config)

        # 설정 적용
        self.scripts_dir = config["scripts_dir"]
        self.default_shell = config["default_shell"]

    def get_scripts_dir(self) -> str:
        """스크립트 디렉토리 경로 반환"""
        return self.scripts_dir

    def get_shell(self) -> str:
        """기본 셸 반환"""
        return self.default_shell

    def get_scripts(self) -> List[Tuple[str, str]]:
        """설정된 소스에서 스크립트 목록 가져오기"""
        provider = get_provider(self.scripts_dir)
        return provider.get_scripts()

    def is_available(self) -> bool:
        """스크립트 소스가 사용 가능한지 확인"""
        provider = get_provider(self.scripts_dir)
        return provider.is_available()

    def to_dict(self) -> Dict[str, Any]:
        """설정을 딕셔너리로 반환"""
        return {"scripts_dir": self.scripts_dir, "default_shell": self.default_shell}


def get_default_config() -> Dict[str, Any]:
    """기본 설정값 반환"""
    return {"scripts_dir": DEFAULT_SCRIPTS_DIR, "default_shell": DEFAULT_SHELL}


def load_config_file(config_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """설정 파일 로딩"""
    if config_path is None:
        config_path = find_config_file()

    if not config_path or not os.path.exists(config_path):
        return None

    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        return validate_config(config) if config else None

    except yaml.YAMLError as e:
        print(f"Warning: Invalid YAML in {config_path}: {e}")
        return None
    except Exception as e:
        print(f"Warning: Failed to load config from {config_path}: {e}")
        return None


def find_config_file() -> Optional[str]:
    """설정 파일 위치 찾기"""
    # 현재 디렉토리에서 .runsh/config.yaml 찾기
    current_dir = Path.cwd()
    runsh_dir = current_dir / RUNSH_DIR
    config_file = runsh_dir / CONFIG_FILENAME

    if config_file.exists():
        return str(config_file)

    # 상위 디렉토리들에서 찾기 (최대 3단계)
    for parent in current_dir.parents[:3]:
        runsh_dir = parent / RUNSH_DIR
        config_file = runsh_dir / CONFIG_FILENAME
        if config_file.exists():
            return str(config_file)

    return None


def get_runsh_dir() -> Path:
    """RunSH 디렉토리 경로 반환 (없으면 생성)"""
    runsh_path = Path.cwd() / RUNSH_DIR
    runsh_path.mkdir(exist_ok=True)
    return runsh_path


def load_env_config() -> Dict[str, Any]:
    """환경변수에서 설정 로딩"""
    config = {}

    if ENV_SCRIPTS_DIR in os.environ:
        config["scripts_dir"] = os.environ[ENV_SCRIPTS_DIR]

    if ENV_SHELL in os.environ:
        config["default_shell"] = os.environ[ENV_SHELL]

    return config


def validate_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """설정값 검증 및 정규화"""
    validated = {}

    # scripts_dir 검증
    if "scripts_dir" in config:
        scripts_dir = config["scripts_dir"]
        if isinstance(scripts_dir, str):
            validated["scripts_dir"] = scripts_dir
        else:
            print(f"Warning: scripts_dir must be a string, got {type(scripts_dir)}")

    # default_shell 검증
    if "default_shell" in config:
        shell = config["default_shell"]
        if isinstance(shell, str) and shell in SUPPORTED_SHELLS:
            validated["default_shell"] = shell
        else:
            print(f"Warning: Unsupported shell '{shell}', using default")

    return validated


def create_sample_config(path: Optional[str] = None) -> str:
    """샘플 설정 파일 생성"""
    if path is None:
        runsh_dir = get_runsh_dir()
        path = str(runsh_dir / CONFIG_FILENAME)

    sample_config = {"scripts_dir": "scripts", "default_shell": "bash"}

    with open(path, "w") as f:
        f.write("# RunSH Configuration\n")
        f.write("# Examples:\n")
        f.write("#   scripts_dir: './scripts'  # Local directory\n")
        f.write(
            "#   scripts_dir: 'https://github.com/user/repo/tree/main/scripts'  # GitHub\n\n"
        )
        yaml.dump(sample_config, f, default_flow_style=False)

    return path


def show_config_info(config: Config):
    """현재 설정 정보 출력"""
    print("Current configuration:")
    print(f"  Scripts source: {config.get_scripts_dir()}")
    print(f"  Default shell: {config.get_shell()}")

    # 소스 타입 표시
    if "github.com" in config.get_scripts_dir():
        print("  Source type: GitHub repository")
    else:
        print("  Source type: Local directory")

    config_file = find_config_file()
    if config_file:
        print(f"  Config file: {config_file}")
    else:
        print("  Config file: Not found (using defaults)")

    # 환경변수 정보
    env_vars = []
    if ENV_SCRIPTS_DIR in os.environ:
        env_vars.append(f"{ENV_SCRIPTS_DIR}={os.environ[ENV_SCRIPTS_DIR]}")
    if ENV_SHELL in os.environ:
        env_vars.append(f"{ENV_SHELL}={os.environ[ENV_SHELL]}")

    if env_vars:
        print(f"  Environment variables: {', '.join(env_vars)}")

    # 가용성 체크
    if config.is_available():
        print("  Status: ✓ Available")
    else:
        print("  Status: ✗ Not available")

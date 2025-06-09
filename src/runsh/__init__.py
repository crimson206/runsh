# __init__.py - Script Runner 패키지

"""
Script Runner - Shell scripts를 Python CLI 도구로 자동 변환

주석 기반 메타데이터로 자동완성과 help를 제공하는 CLI 도구를 생성합니다.
"""

__version__ = "1.0.0"
__author__ = "Script Runner Team"

from .cli import main, discover_scripts
from .commands import ScriptCommand, ConfigCommand
from .parser import parse_script_metadata
from .config import Config

__all__ = [
    'main',
    'discover_scripts', 
    'ScriptCommand',
    'ConfigCommand',
    'parse_script_metadata',
    'Config'
]
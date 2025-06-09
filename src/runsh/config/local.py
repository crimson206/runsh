# config/local.py - 로컬 디렉토리 스크립트 프로바이더

import os
from pathlib import Path
from typing import List, Tuple


class LocalProvider:
    """로컬 디렉토리에서 스크립트를 가져오는 프로바이더"""

    def __init__(self, scripts_dir: str):
        self.scripts_dir = scripts_dir

    def get_scripts(self) -> List[Tuple[str, str]]:
        """로컬 디렉토리에서 .sh 파일들을 읽어서 반환"""
        scripts = []
        scripts_path = Path(self.scripts_dir)

        if not scripts_path.exists():
            return scripts

        for script_file in scripts_path.glob("*.sh"):
            if script_file.is_file():
                try:
                    with open(script_file, "r", encoding="utf-8") as f:
                        content = f.read()
                    scripts.append((str(script_file), content))
                except Exception as e:
                    print(f"Warning: Failed to read {script_file}: {e}")
                    continue

        return scripts

    def is_available(self) -> bool:
        """로컬 디렉토리가 존재하는지 확인"""
        return Path(self.scripts_dir).exists()

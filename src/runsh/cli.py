# cli.py - 메인 CLI 앱 및 진입점

import tempfile
import os
from pathlib import Path
from cleo.application import Application

from .parser import parse_script_metadata
from .commands import ScriptCommand, ConfigCommand, CacheCommand, DebugCommand
from .config import Config


def get_version():
    """pyproject.toml에서 버전을 동적으로 읽어오기"""
    try:
        import importlib.metadata
        return importlib.metadata.version("runsh")
    except ImportError:
        return "unknown"


def discover_scripts() -> Application:
    """설정된 소스에서 스크립트들을 찾아서 명령어로 등록"""
    # 설정 로딩
    config = Config()

    app = create_application()

    # 내장 명령어 추가
    app.add(ConfigCommand())
    app.add(CacheCommand())
    app.add(DebugCommand())

    if not config.is_available():
        print(f"Scripts source not available: {config.get_scripts_dir()}")
        _show_setup_instructions(config)
        return app

    commands_found = register_script_commands(app, config)

    if commands_found == 0:
        print(f"No .sh files found in {config.get_scripts_dir()}")
        print("Add .sh files with @description, @arg, @option comments to get started.")

    return app


def _show_setup_instructions(config: Config):
    """설정 방법 안내"""
    scripts_dir = config.get_scripts_dir()

    if "github.com" in scripts_dir:
        print("GitHub repository not accessible. Check:")
        print("  1. Repository exists and is public")
        print("  2. Network connection")
        print("  3. URL format is correct")
    else:
        print("You can:")
        print(f"  1. Create the directory: mkdir -p {scripts_dir}")
        print("  2. Change the directory in .script-runner.yaml")
        print("  3. Set SCRIPT_RUNNER_DIR environment variable")
        print(
            "  4. Use GitHub: scripts_dir: 'https://github.com/user/repo/tree/main/scripts'"
        )


def create_application() -> Application:
    """기본 Application 인스턴스 생성"""
    return Application("runsh", get_version())


def register_script_commands(app: Application, config: Config) -> int:
    """스크립트들을 찾아서 명령어로 등록"""
    commands_count = 0

    # 설정된 소스에서 스크립트 가져오기
    scripts = config.get_scripts()

    for script_path, script_content in scripts:
        try:
            # GitHub 스크립트의 경우 임시 파일 생성
            if script_path.startswith("github://"):
                original_name = script_path.replace("github://", "")
                temp_path = _create_temp_script_file(script_content, original_name)
                actual_path = temp_path
            else:
                actual_path = script_path

            metadata = parse_script_metadata(actual_path)
            command = ScriptCommand(actual_path, metadata, config.get_shell())
            app.add(command)
            commands_count += 1

        except Exception as e:
            script_name = (
                script_path.split("/")[-1] if "/" in script_path else script_path
            )
            print(f"Warning: Failed to parse {script_name}: {e}")
            continue

    return commands_count


def _create_temp_script_file(content: str, original_name: str = None) -> str:
    """스크립트 내용으로 임시 파일 생성"""
    if original_name:
        # 원래 이름 기반으로 안전한 임시 파일 생성
        import hashlib

        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        temp_dir = tempfile.gettempdir()
        base_name = original_name.replace(".sh", "")
        temp_path = os.path.join(temp_dir, f"github_{base_name}_{content_hash}.sh")
    else:
        # 기본 임시 파일
        temp_fd, temp_path = tempfile.mkstemp(suffix=".sh", prefix="github_script_")
        os.close(temp_fd)

    try:
        with open(temp_path, "w") as temp_file:
            temp_file.write(content)

        # 실행 권한 추가
        os.chmod(temp_path, 0o755)

        return temp_path
    except:
        # 에러 시 파일 정리
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise


def main():
    """메인 진입점"""
    try:
        app = discover_scripts()
        app.run()
    except KeyboardInterrupt:
        print("\nAborted by user")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())

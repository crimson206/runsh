# cli.py - 메인 CLI 앱 및 진입점

from pathlib import Path
from cleo.application import Application

from .parser import parse_script_metadata
from .commands import ScriptCommand, ConfigCommand
from .config import Config


def discover_scripts() -> Application:
    """스크립트 디렉토리에서 .sh 파일들을 찾아서 명령어로 등록"""
    # 설정 로딩
    config = Config()

    app = create_application()

    # 내장 명령어 추가
    app.add(ConfigCommand())

    scripts_path = Path(config.get_scripts_dir())
    if not scripts_path.exists():
        print(f"Scripts directory not found: {config.get_scripts_dir()}")
        print("You can:")
        print(f"  1. Create the directory: mkdir -p {config.get_scripts_dir()}")
        print("  2. Change the directory in .script-runner.yaml")
        print("  3. Set SCRIPT_RUNNER_DIR environment variable")
        return app

    commands_found = register_script_commands(app, scripts_path, config)

    if commands_found == 0:
        print(f"No .sh files found in {config.get_scripts_dir()}")
        print("Add .sh files with @description, @arg, @option comments to get started.")

    return app


def create_application() -> Application:
    """기본 Application 인스턴스 생성"""
    return Application("script-runner", "1.0.0")


def register_script_commands(
    app: Application, scripts_path: Path, config: Config
) -> int:
    """스크립트 파일들을 찾아서 명령어로 등록"""
    commands_count = 0

    for script_file in scripts_path.glob("*.sh"):
        if script_file.is_file():
            try:
                metadata = parse_script_metadata(script_file)
                command = ScriptCommand(str(script_file), metadata, config.get_shell())
                app.add(command)
                commands_count += 1
            except Exception as e:
                print(f"Warning: Failed to parse {script_file}: {e}")
                continue

    return commands_count


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

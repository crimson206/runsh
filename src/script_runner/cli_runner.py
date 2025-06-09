# cli_runner.py - 메인 Python CLI 도구

import os
import re
import subprocess
import tempfile
from pathlib import Path
from cleo.application import Application
from cleo.commands.command import Command
from cleo.helpers import argument, option

# Cleo 예약 옵션들
CLEO_RESERVED_OPTIONS = {
    "verbose",
    "quiet",
    "help",
    "version",
    "no-interaction",
    "ansi",
    "no-ansi",
}
CLEO_RESERVED_SHORTCUTS = {"v", "q", "h", "V", "n"}


class ScriptCommand(Command):
    def __init__(self, script_path, script_meta):
        self.script_path = script_path
        self.script_meta = script_meta
        super().__init__()

    @property
    def name(self):
        return Path(self.script_path).stem

    @property
    def description(self):
        return self.script_meta.get("description", f"Run {self.name} script")

    @property
    def arguments(self):
        args = []
        for arg in self.script_meta.get("args", []):
            # default 값이 있으면 자동으로 optional로 만들기
            has_default = arg.get("default") is not None
            is_optional = arg.get("optional", False) or has_default

            args.append(
                argument(
                    arg["name"],
                    arg.get("description", ""),
                    optional=is_optional,
                    default=arg.get("default") if is_optional else None,
                )
            )
        return args

    @property
    def options(self):
        opts = []
        for opt in self.script_meta.get("options", []):
            # cleo 예약 옵션과 충돌하는 경우 suffix 추가
            option_name = opt["name"]
            if option_name in CLEO_RESERVED_OPTIONS:
                option_name = f"{option_name}-sh"

            # shortcut 충돌 처리 - 충돌 시 None으로 설정하고 안내 메시지 출력
            short = opt.get("short")
            if short and short in CLEO_RESERVED_SHORTCUTS:
                print(
                    f"Warning: Shortcut '-{short}' for option '{opt['name']}' conflicts with CLI reserved shortcuts."
                )
                print(
                    f"Use --{option_name} instead, or choose a different shortcut in your script."
                )
                short = None

            # flag vs value option 처리
            is_flag = opt.get("flag", False)  # 명시적으로 [flag] 있을 때만 True
            default = opt.get("default")

            if is_flag:
                opts.append(
                    option(option_name, short, opt.get("description", ""), flag=True)
                )
            else:
                # value option
                opts.append(
                    option(
                        option_name,
                        short,
                        opt.get("description", ""),
                        flag=False,
                        value_required=default is None,  # default 없으면 required
                        default=default,
                    )
                )
        return opts

    def handle(self):
        # arguments를 순서대로 수집
        script_args = []
        for arg_def in self.script_meta.get("args", []):
            value = self.argument(arg_def["name"])
            if value:
                script_args.append(str(value))

        # options를 환경변수로 전달
        env = os.environ.copy()
        for opt_def in self.script_meta.get("options", []):
            # 원래 이름으로 옵션 체크 (suffix 없는)
            original_name = opt_def["name"]
            option_name = original_name
            if original_name in CLEO_RESERVED_OPTIONS:
                option_name = f"{original_name}-sh"

            option_value = self.option(option_name)
            if option_value:
                # 환경변수는 원래 이름으로 전달
                env_name = f"CLI_{original_name.replace('-', '_').upper()}"
                if opt_def.get("flag", False):
                    # flag option
                    env[env_name] = "1"
                else:
                    # value option
                    env[env_name] = str(option_value)

        # 임시 스크립트 생성 및 실행
        temp_script = self._create_temp_script()

        try:
            result = subprocess.run(
                ["bash", temp_script] + script_args, env=env, capture_output=False
            )
            return result.returncode
        finally:
            # 임시 파일 정리
            if os.path.exists(temp_script):
                os.unlink(temp_script)

    def _create_temp_script(self):
        """원본 스크립트에서 SCRIPT-RUNNER 블록을 추가한 임시 스크립트 생성"""
        with open(self.script_path, "r") as f:
            content = f.read()

        # 기존 SCRIPT-RUNNER 블록 제거 (혹시 있다면)
        pattern = r"# <SCRIPT-RUNNER>.*?# </SCRIPT-RUNNER>\n"
        content = re.sub(pattern, "", content, flags=re.DOTALL)

        # 새 SCRIPT-RUNNER 블록 생성
        runner_block = "# <SCRIPT-RUNNER>\n"

        # 옵션 환경변수들
        for opt in self.script_meta.get("options", []):
            var_name = opt["name"].replace("-", "_").upper()
            if opt.get("flag", False):
                # flag 옵션: CLI에서만 받음
                runner_block += f"{var_name}=${{CLI_{var_name}:-0}}\n"
            else:
                # value 옵션: 환경변수 → CLI → 기본값
                default = opt.get("default", "")
                if default:
                    runner_block += (
                        f"{var_name}=${{${var_name}:-${{CLI_{var_name}:-{default}}}}}\n"
                    )
                else:
                    runner_block += (
                        f"{var_name}=${{${var_name}:-${{CLI_{var_name}}}}}\n"
                    )

        # 인자들
        for i, arg in enumerate(self.script_meta.get("args", []), 1):
            var_name = arg["name"].replace("-", "_").upper()
            default = arg.get("default", "")
            runner_block += f"{var_name}=${{{i}:-{default}}}\n"

        runner_block += "# </SCRIPT-RUNNER>\n\n"

        # USER SETTING 다음에 삽입하거나 shebang 다음에 삽입
        if "# USER SETTING" in content:
            # USER SETTING 섹션 다음에 삽입
            parts = content.split("# USER SETTING")
            if len(parts) >= 2:
                # USER SETTING 섹션의 끝을 찾기
                after_user_setting = parts[1]
                # 다음 주석이나 실제 스크립트 시작까지 찾기
                lines = after_user_setting.split("\n")
                insert_idx = 0
                for i, line in enumerate(lines):
                    if line.strip() and not line.strip().startswith("#"):
                        insert_idx = i
                        break
                    if line.strip().startswith("# ") and "USER SETTING" not in line:
                        insert_idx = i
                        break

                before_insert = "\n".join(lines[:insert_idx])
                after_insert = "\n".join(lines[insert_idx:])

                new_content = (
                    parts[0]
                    + "# USER SETTING"
                    + before_insert
                    + "\n\n"
                    + runner_block
                    + after_insert
                )
            else:
                new_content = content + "\n" + runner_block
        else:
            # shebang 다음에 삽입
            lines = content.split("\n")
            if lines[0].startswith("#!"):
                insert_content = "\n".join(lines[1:])
                new_content = lines[0] + "\n\n" + runner_block + insert_content
            else:
                new_content = runner_block + content

        # 임시 파일 생성
        temp_fd, temp_path = tempfile.mkstemp(suffix=".sh", prefix="script_runner_")
        try:
            with os.fdopen(temp_fd, "w") as temp_file:
                temp_file.write(new_content)

            # 실행 권한 추가
            os.chmod(temp_path, 0o755)

            return temp_path
        except:
            # 에러 시 파일 정리
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise

    def _update_script_runner_block(self):
        """스크립트에 SCRIPT-RUNNER 블록 자동 생성/업데이트"""
        with open(self.script_path, "r") as f:
            content = f.read()

        # 기존 SCRIPT-RUNNER 블록 제거
        pattern = r"# <SCRIPT-RUNNER>.*?# </SCRIPT-RUNNER>\n"
        content = re.sub(pattern, "", content, flags=re.DOTALL)

        # 새 SCRIPT-RUNNER 블록 생성
        runner_block = "# <SCRIPT-RUNNER>\n"

        # 옵션 환경변수들
        for opt in self.script_meta.get("options", []):
            var_name = opt["name"].replace("-", "_").upper()
            if opt.get("flag", False):
                # flag 옵션: CLI에서만 받음
                runner_block += f"{var_name}=${{CLI_{var_name}:-0}}\n"
            else:
                # value 옵션: 환경변수 → CLI → 기본값
                default = opt.get("default", "")
                if default:
                    runner_block += (
                        f"{var_name}=${{${var_name}:-${{CLI_{var_name}:-{default}}}}}\n"
                    )
                else:
                    runner_block += (
                        f"{var_name}=${{${var_name}:-${{CLI_{var_name}}}}}\n"
                    )

        # 인자들
        for i, arg in enumerate(self.script_meta.get("args", []), 1):
            var_name = arg["name"].replace("-", "_").upper()
            default = arg.get("default", "")
            runner_block += f"{var_name}=${{${i}:-{default}}}\n"

        runner_block += "# </SCRIPT-RUNNER>\n\n"

        # USER SETTING 다음에 삽입
        if "# USER SETTING" in content:
            # USER SETTING 섹션 다음에 삽입
            parts = content.split("# USER SETTING")
            if len(parts) >= 2:
                # USER SETTING 섹션의 끝을 찾기
                after_user_setting = parts[1]
                # 다음 주석이나 실제 스크립트 시작까지 찾기
                lines = after_user_setting.split("\n")
                insert_idx = 0
                for i, line in enumerate(lines):
                    if line.strip() and not line.strip().startswith("#"):
                        insert_idx = i
                        break
                    if line.strip().startswith("# ") and "USER SETTING" not in line:
                        insert_idx = i
                        break

                before_insert = "\n".join(lines[:insert_idx])
                after_insert = "\n".join(lines[insert_idx:])

                new_content = (
                    parts[0]
                    + "# USER SETTING"
                    + before_insert
                    + "\n\n"
                    + runner_block
                    + after_insert
                )
            else:
                new_content = content + "\n" + runner_block
        else:
            # shebang 다음에 삽입
            lines = content.split("\n")
            if lines[0].startswith("#!"):
                insert_content = "\n".join(lines[1:])
                new_content = lines[0] + "\n\n" + runner_block + insert_content
            else:
                new_content = runner_block + content

        # 파일 업데이트
        with open(self.script_path, "w") as f:
            f.write(new_content)

            # 에러 시 파일 정리
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise


def parse_script_metadata(script_path):
    """
    .sh 파일에서 메타데이터 파싱

    형식:
    # @description: 스크립트 설명
    # @arg name1 [optional] [default=value]: 설명
    # @option verbose,v [flag]: 자세한 출력
    """
    metadata = {"args": [], "options": []}

    with open(script_path, "r") as f:
        for line in f:
            line = line.strip()

            # 설명 파싱
            if line.startswith("# @description:"):
                metadata["description"] = line.split(":", 1)[1].strip()

            # 인자 파싱
            elif line.startswith("# @arg"):
                match = re.match(r"# @arg (\w+)(\s+\[([^\]]+)\])*\s*:\s*(.*)", line)
                if match:
                    name, _, modifiers, desc = match.groups()
                    arg_info = {"name": name, "description": desc}

                    if modifiers:
                        if "optional" in modifiers:
                            arg_info["optional"] = True
                        if "default=" in modifiers:
                            default = re.search(r"default=([^\]]+)", modifiers)
                            if default:
                                arg_info["default"] = default.group(1)

                    metadata["args"].append(arg_info)

            # 옵션 파싱
            elif line.startswith("# @option"):
                match = re.match(
                    r"# @option ([^,]+)(?:,(\w+))?(\s+\[([^\]]+)\])?\s*:\s*(.*)", line
                )
                if match:
                    name, short, _, modifiers, desc = match.groups()
                    opt_info = {
                        "name": name.strip(),
                        "description": desc,
                        "short": short,
                    }

                    if modifiers:
                        if "flag" in modifiers:
                            opt_info["flag"] = True
                        elif "default=" in modifiers:
                            # value option with default
                            default = re.search(r"default=([^\]]+)", modifiers)
                            if default:
                                opt_info["default"] = default.group(1)
                                opt_info["flag"] = False
                        else:
                            # required value option
                            opt_info["flag"] = False
                    else:
                        # no modifiers = required value option
                        opt_info["flag"] = False

                    metadata["options"].append(opt_info)

    return metadata


def discover_scripts(scripts_dir="./scripts"):
    """스크립트 디렉토리에서 .sh 파일들을 찾아서 명령어로 등록"""
    app = Application("shell-cli", "1.0.0")

    scripts_path = Path(scripts_dir)
    if not scripts_path.exists():
        print(f"Scripts directory not found: {scripts_dir}")
        return app

    for script_file in scripts_path.glob("*.sh"):
        if script_file.is_file():
            metadata = parse_script_metadata(script_file)
            command = ScriptCommand(str(script_file), metadata)
            app.add(command)

    return app


def main():
    app = discover_scripts()
    app.run()


if __name__ == "__main__":
    main()

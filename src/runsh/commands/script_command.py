# commands/script_command.py - ScriptCommand 클래스

import os
import re
import subprocess
import tempfile
from pathlib import Path
from cleo.commands.command import Command
from cleo.helpers import argument, option

from ..constants import (
    CLEO_RESERVED_OPTIONS,
    CLEO_RESERVED_SHORTCUTS,
    TEMP_SCRIPT_PREFIX,
    SCRIPT_RUNNER_START,
    SCRIPT_RUNNER_END,
    USER_SETTING_MARKER,
)


class ScriptCommand(Command):
    def __init__(self, script_path: str, script_meta: dict, shell: str = "bash"):
        self.script_path = script_path
        self.script_meta = script_meta
        self.shell = shell
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
            option_name, short = self._resolve_option_conflicts(opt)

            # flag vs value option 처리
            is_flag = opt.get("flag", False)
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
                        value_required=default is None,
                        default=default,
                    )
                )
        return opts

    def _resolve_option_conflicts(self, opt: dict) -> tuple:
        """cleo 예약 옵션/단축키 충돌 해결"""
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

        return option_name, short

    def handle(self):
        # arguments를 순서대로 수집
        script_args = self._collect_arguments()

        # options를 환경변수로 전달
        env = self._prepare_environment()

        # 임시 스크립트 생성 및 실행
        temp_script = self._create_temp_script()

        try:
            result = subprocess.run(
                [self.shell, temp_script] + script_args, env=env, capture_output=False
            )
            return result.returncode
        finally:
            # 임시 파일 정리
            if os.path.exists(temp_script):
                os.unlink(temp_script)

    def _collect_arguments(self) -> list:
        """CLI arguments 수집"""
        script_args = []
        for arg_def in self.script_meta.get("args", []):
            value = self.argument(arg_def["name"])
            if value:
                script_args.append(str(value))
        return script_args

    def _prepare_environment(self) -> dict:
        """환경변수 준비"""
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

        return env

    def _create_temp_script(self) -> str:
        """원본 스크립트에서 SCRIPT-RUNNER 블록을 추가한 임시 스크립트 생성"""
        with open(self.script_path, "r") as f:
            content = f.read()

        # 기존 SCRIPT-RUNNER 블록 제거 (혹시 있다면)
        content = self._remove_existing_runner_block(content)

        # 새 SCRIPT-RUNNER 블록 생성
        runner_block = self._generate_runner_block()

        # 적절한 위치에 삽입
        new_content = self._insert_runner_block(content, runner_block)

        # 임시 파일 생성
        return self._create_temp_file(new_content)

    def _remove_existing_runner_block(self, content: str) -> str:
        """기존 SCRIPT-RUNNER 블록 제거"""
        pattern = f"{re.escape(SCRIPT_RUNNER_START)}.*?{re.escape(SCRIPT_RUNNER_END)}\n"
        return re.sub(pattern, "", content, flags=re.DOTALL)

    def _generate_runner_block(self) -> str:
        """SCRIPT-RUNNER 블록 생성"""
        runner_block = f"{SCRIPT_RUNNER_START}\n"

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

        runner_block += f"{SCRIPT_RUNNER_END}\n\n"
        return runner_block

    def _insert_runner_block(self, content: str, runner_block: str) -> str:
        """적절한 위치에 SCRIPT-RUNNER 블록 삽입"""
        if USER_SETTING_MARKER in content:
            return self._insert_after_user_setting(content, runner_block)
        else:
            return self._insert_after_shebang(content, runner_block)

    def _insert_after_user_setting(self, content: str, runner_block: str) -> str:
        """USER SETTING 섹션 다음에 삽입"""
        parts = content.split(USER_SETTING_MARKER)
        if len(parts) < 2:
            return content + "\n" + runner_block

        after_user_setting = parts[1]
        lines = after_user_setting.split("\n")

        # 다음 주석이나 실제 스크립트 시작까지 찾기
        insert_idx = 0
        for i, line in enumerate(lines):
            if line.strip() and not line.strip().startswith("#"):
                insert_idx = i
                break
            if line.strip().startswith("# ") and USER_SETTING_MARKER not in line:
                insert_idx = i
                break

        before_insert = "\n".join(lines[:insert_idx])
        after_insert = "\n".join(lines[insert_idx:])

        return (
            parts[0]
            + USER_SETTING_MARKER
            + before_insert
            + "\n\n"
            + runner_block
            + after_insert
        )

    def _insert_after_shebang(self, content: str, runner_block: str) -> str:
        """shebang 다음에 삽입"""
        lines = content.split("\n")
        if lines[0].startswith("#!"):
            insert_content = "\n".join(lines[1:])
            return lines[0] + "\n\n" + runner_block + insert_content
        else:
            return runner_block + content

    def _create_temp_file(self, content: str) -> str:
        """임시 파일 생성"""
        temp_fd, temp_path = tempfile.mkstemp(suffix=".sh", prefix=TEMP_SCRIPT_PREFIX)
        try:
            with os.fdopen(temp_fd, "w") as temp_file:
                temp_file.write(content)

            # 실행 권한 추가
            os.chmod(temp_path, 0o755)

            return temp_path
        except:
            # 에러 시 파일 정리
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise

# commands/script_command.py - ScriptCommand 클래스 (리팩토링됨)

import os
import subprocess
from pathlib import Path
from cleo.commands.command import Command
from cleo.helpers import argument, option

from ..utils import (
    resolve_option_conflicts,
    collect_script_arguments,
    prepare_script_environment,
    create_transformed_temp_script,
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
            option_name, short = resolve_option_conflicts(opt)

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

    def handle(self):
        # arguments를 순서대로 수집
        script_args = collect_script_arguments(
            self.script_meta.get("args", []), 
            self.argument
        )

        # options를 환경변수로 전달
        env = prepare_script_environment(
            self.script_meta.get("options", []),
            self.option
        )

        # 임시 스크립트 생성 및 실행
        temp_script = create_transformed_temp_script(self.script_path, self.script_meta)

        try:
            result = subprocess.run(
                [self.shell, temp_script] + script_args, env=env, capture_output=False
            )
            return result.returncode
        finally:
            # 임시 파일 정리
            if os.path.exists(temp_script):
                os.unlink(temp_script)
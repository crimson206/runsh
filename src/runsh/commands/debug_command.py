# commands/debug_command.py - Debug 명령어 (리팩토링됨)

import os
import tempfile
from pathlib import Path
from cleo.commands.command import Command
from cleo.helpers import argument, option

from ..config import Config
from ..parser import parse_script_metadata
from ..utils import (
    resolve_option_conflicts,
    generate_runner_block,
    transform_script_content,
    create_temp_script_file,
)


class DebugCommand(Command):
    """스크립트 디버깅 도구"""

    name = "debug-rs"
    description = "Debug script transformation and export files"

    arguments = [argument("script_name", "Name of the script to debug")]

    options = [
        option("export-origin-sh", None, "Export original script", flag=True),
        option("export-final-sh", None, "Export final transformed script", flag=True),
        option(
            "target-dir",
            None,
            "Target directory for exports",
            flag=False,
            default="debug_runsh",
        ),
        option("show-metadata", None, "Show parsed metadata", flag=True),
        option("show-diff", None, "Show diff between original and final", flag=True),
        option(
            "show-runner-block",
            None,
            "Show generated SCRIPT-RUNNER block only",
            flag=True,
        ),
        option("validate-options", None, "Validate option conflicts", flag=True),
    ]

    def handle(self):
        script_name = self.argument("script_name")
        target_dir = self.option("target-dir")

        # 설정 로딩
        config = Config()

        if not config.is_available():
            self.error(f"Scripts source not available: {config.get_scripts_dir()}")
            return 1

        # 스크립트 찾기
        script_path, script_content = self._find_script(config, script_name)
        if not script_path:
            self.error(f"Script '{script_name}' not found")
            return 1

        self.info(f"Found script: {script_path}")

        # 타겟 디렉토리 준비
        target_path = Path(target_dir)
        target_path.mkdir(exist_ok=True)
        self.info(f"Using target directory: {target_path.absolute()}")

        # 메타데이터 파싱
        try:
            # 임시 파일 생성해서 메타데이터 파싱
            temp_script_path = self._create_temp_original_file(
                script_content, script_name
            )
            metadata = parse_script_metadata(temp_script_path)

            # 각 옵션에 따라 처리
            if self.option("show-metadata"):
                self._show_metadata(metadata)

            if self.option("validate-options"):
                self._validate_options(metadata)

            if self.option("show-runner-block"):
                self._show_runner_block(metadata)

            # 최종 변형된 스크립트 생성
            final_content = transform_script_content(temp_script_path, metadata)

            # Export 처리
            exports_done = []

            if self.option("export-origin-sh"):
                origin_path = target_path / f"{script_name}_original.sh"
                with open(origin_path, "w") as f:
                    f.write(script_content)
                exports_done.append(f"Original: {origin_path}")

            if self.option("export-final-sh"):
                final_path = target_path / f"{script_name}_final.sh"
                with open(final_path, "w") as f:
                    f.write(final_content)
                exports_done.append(f"Final: {final_path}")

            if self.option("show-diff"):
                self._show_diff(script_content, final_content, script_name)

            # 결과 출력
            if exports_done:
                self.line("")
                self.info("Exported files:")
                for export_info in exports_done:
                    self.line(f"  {export_info}")

            # 임시 파일 정리
            if os.path.exists(temp_script_path):
                os.unlink(temp_script_path)

        except Exception as e:
            self.error(f"Failed to process script: {e}")
            return 1

        self.line("")
        self.info("Debug completed successfully!")
        return 0

    def _find_script(self, config: Config, script_name: str) -> tuple[str, str]:
        """스크립트 찾기"""
        scripts = config.get_scripts()

        for script_path, script_content in scripts:
            # 파일명에서 확장자 제거한 이름과 비교
            name = Path(script_path).stem
            if name == script_name:
                return script_path, script_content

        return None, None

    def _create_temp_original_file(self, content: str, script_name: str) -> str:
        """원본 스크립트로 임시 파일 생성"""
        return create_temp_script_file(content, f"debug_{script_name}_")

    def _show_metadata(self, metadata: dict):
        """메타데이터 표시"""
        self.line("")
        self.info("Parsed Metadata:")
        self.line(f"  Description: {metadata.get('description', 'N/A')}")

        args = metadata.get("args", [])
        if args:
            self.line("  Arguments:")
            for arg in args:
                optional = " (optional)" if arg.get("optional") else ""
                default = (
                    f" [default: {arg.get('default')}]" if arg.get("default") else ""
                )
                self.line(
                    f"    {arg['name']}: {arg.get('description', 'N/A')}{optional}{default}"
                )

        options = metadata.get("options", [])
        if options:
            self.line("  Options:")
            for opt in options:
                flag_info = " (flag)" if opt.get("flag") else ""
                short = f", -{opt['short']}" if opt.get("short") else ""
                default = (
                    f" [default: {opt.get('default')}]"
                    if opt.get("default") and not opt.get("flag")
                    else ""
                )
                self.line(
                    f"    --{opt['name']}{short}: {opt.get('description', 'N/A')}{flag_info}{default}"
                )

    def _validate_options(self, metadata: dict):
        """옵션 충돌 검증"""
        self.line("")
        self.info("Option Conflict Validation:")

        options = metadata.get("options", [])
        if not options:
            self.line("  No options to validate")
            return

        conflicts_found = False

        for opt in options:
            original_name = opt["name"]
            original_short = opt.get("short")

            resolved_name, resolved_short = resolve_option_conflicts(opt)

            if original_name != resolved_name:
                self.line(
                    f"  <comment>Option conflict:</comment> '{original_name}' → '{resolved_name}'"
                )
                conflicts_found = True

            if original_short != resolved_short:
                if resolved_short is None:
                    self.line(
                        f"  <comment>Shortcut conflict:</comment> '-{original_short}' removed"
                    )
                else:
                    self.line(
                        f"  <comment>Shortcut conflict:</comment> '-{original_short}' → '-{resolved_short}'"
                    )
                conflicts_found = True

        if not conflicts_found:
            self.line("  <info>No conflicts found</info>")

    def _show_runner_block(self, metadata: dict):
        """생성된 SCRIPT-RUNNER 블록 표시"""
        self.line("")
        self.info("Generated SCRIPT-RUNNER Block:")

        runner_block = generate_runner_block(metadata)

        # 블록을 구문 강조하여 표시
        lines = runner_block.split("\n")
        for line in lines:
            if line.strip().startswith("#"):
                self.line(f"<comment>{line}</comment>")
            elif "=" in line and not line.strip().startswith("#"):
                # 변수 할당 라인 강조
                self.line(f"<info>{line}</info>")
            else:
                self.line(line)

    def _show_diff(self, original: str, final: str, script_name: str):
        """원본과 최종 스크립트의 차이점 표시"""
        self.line("")
        self.info("Differences (Original → Final):")

        original_lines = original.split("\n")
        final_lines = final.split("\n")

        # 간단한 diff 표시
        import difflib

        diff = list(
            difflib.unified_diff(
                original_lines,
                final_lines,
                fromfile=f"{script_name}_original.sh",
                tofile=f"{script_name}_final.sh",
                lineterm="",
            )
        )

        if diff:
            for line in diff:
                if line.startswith("+++") or line.startswith("---"):
                    self.line(f"<comment>{line}</comment>")
                elif line.startswith("+"):
                    self.line(f"<info>{line}</info>")
                elif line.startswith("-"):
                    self.line(f"<error>{line}</error>")
                elif line.startswith("@@"):
                    self.line(f"<question>{line}</question>")
                else:
                    self.line(line)
        else:
            self.line("  No differences found")

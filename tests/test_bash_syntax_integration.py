# tests/test_bash_syntax_integration.py - Bash 문법 통합 테스트

import os
import tempfile
import subprocess
import pytest
from pathlib import Path

from runsh.parser import parse_script_metadata
from runsh.utils import transform_script_content, create_temp_script_file


class TestBashSyntaxIntegration:
    """실제 bash 문법 검증 통합 테스트"""

    def test_github_release_script_syntax(self):
        """GitHub release 스크립트의 bash 문법 검증"""

        # 실제 문제가 되었던 스크립트
        script_content = """#!/bin/bash
# @description: Create GitHub release with entire CHANGELOG.md as release notes
# @arg version: Release version (e.g., v1.0.0, 1.2.3)
# @option changelog,c [default=CHANGELOG.md]: Path to changelog file
# @option prerelease,p [flag]: Mark as pre-release
# @option draft,d [flag]: Create as draft release
# @option assets,a: Glob pattern for assets to attach
# @option title,t: Custom release title

echo "Creating release $VERSION"
echo "Changelog: $CHANGELOG"
if [ "$PRERELEASE" = "1" ]; then
    echo "This is a pre-release"
fi
"""

        # 임시 스크립트 파일 생성
        temp_script = create_temp_script_file(script_content, "github_release_")

        try:
            # 메타데이터 파싱
            metadata = parse_script_metadata(temp_script)

            # 스크립트 변형
            transformed_content = transform_script_content(temp_script, metadata)

            # 변형된 스크립트가 올바른 bash 문법인지 검증
            transformed_script = create_temp_script_file(
                transformed_content, "transformed_"
            )

            try:
                # bash -n으로 문법 검사
                result = subprocess.run(
                    ["bash", "-n", transformed_script], capture_output=True, text=True
                )

                # 에러가 있으면 상세 정보 출력
                if result.returncode != 0:
                    print("=== Transformed Script Content ===")
                    print(transformed_content)
                    print("=== Bash Error ===")
                    print(result.stderr)

                assert (
                    result.returncode == 0
                ), f"Bash syntax error in transformed script: {result.stderr}"

                # bad substitution 패턴이 없는지 확인
                assert (
                    "${$" not in transformed_content
                ), "Bad substitution pattern found in transformed script"

                # 예상되는 변수들이 올바르게 생성되었는지 확인
                assert (
                    "CHANGELOG=${CHANGELOG:-${CLI_CHANGELOG:-CHANGELOG.md}}"
                    in transformed_content
                )
                assert "PRERELEASE=${CLI_PRERELEASE:-0}" in transformed_content
                assert "DRAFT=${CLI_DRAFT:-0}" in transformed_content
                assert "ASSETS=${ASSETS:-${CLI_ASSETS}}" in transformed_content
                assert "TITLE=${TITLE:-${CLI_TITLE}}" in transformed_content
                assert "VERSION=${1:-}" in transformed_content

            finally:
                if os.path.exists(transformed_script):
                    os.unlink(transformed_script)

        finally:
            if os.path.exists(temp_script):
                os.unlink(temp_script)

    def test_complex_options_bash_syntax(self):
        """복잡한 옵션들의 bash 문법 검증"""

        script_content = """#!/bin/bash
# @description: Complex script with various option types
# @arg input_file: Input file path
# @arg output_file [default=output.txt]: Output file path
# @option config-file,c [default=config.json]: Configuration file
# @option verbose,v [flag]: Enable verbose mode
# @option log-level,l [default=INFO]: Log level (DEBUG, INFO, WARN, ERROR)
# @option dry-run,n [flag]: Dry run mode
# @option timeout [default=30]: Timeout in seconds
# @option exclude-pattern: Pattern to exclude

echo "Processing $INPUT_FILE to $OUTPUT_FILE"
echo "Config: $CONFIG_FILE, Log Level: $LOG_LEVEL"
if [ "$VERBOSE" = "1" ]; then
    echo "Verbose mode enabled"
fi
"""

        temp_script = create_temp_script_file(script_content, "complex_options_")

        try:
            metadata = parse_script_metadata(temp_script)
            transformed_content = transform_script_content(temp_script, metadata)

            # bash 문법 검증
            transformed_script = create_temp_script_file(
                transformed_content, "complex_transformed_"
            )

            try:
                result = subprocess.run(
                    ["bash", "-n", transformed_script], capture_output=True, text=True
                )

                assert result.returncode == 0, f"Bash syntax error: {result.stderr}"
                assert "${$" not in transformed_content, "Bad substitution found"

                # 하이픈이 있는 변수명들이 올바르게 언더스코어로 변환되었는지 확인
                assert (
                    "CONFIG_FILE=${CONFIG_FILE:-${CLI_CONFIG_FILE:-config.json}}"
                    in transformed_content
                )
                assert (
                    "LOG_LEVEL=${LOG_LEVEL:-${CLI_LOG_LEVEL:-INFO}}"
                    in transformed_content
                )
                assert "DRY_RUN=${CLI_DRY_RUN:-0}" in transformed_content
                assert (
                    "EXCLUDE_PATTERN=${EXCLUDE_PATTERN:-${CLI_EXCLUDE_PATTERN}}"
                    in transformed_content
                )

            finally:
                if os.path.exists(transformed_script):
                    os.unlink(transformed_script)

        finally:
            if os.path.exists(temp_script):
                os.unlink(temp_script)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# tests/test_utils.py - Utils 함수들 테스트

import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import MagicMock

from runsh.utils import (
    resolve_option_conflicts,
    collect_script_arguments,
    prepare_script_environment,
    remove_existing_runner_block,
    generate_runner_block,
    insert_runner_block,
    insert_after_user_setting,
    insert_after_shebang,
    create_temp_script_file,
    transform_script_content,
    create_transformed_temp_script,
)
from runsh.constants import (
    CLEO_RESERVED_OPTIONS,
    CLEO_RESERVED_SHORTCUTS,
    SCRIPT_RUNNER_START,
    SCRIPT_RUNNER_END,
    USER_SETTING_MARKER,
)


class TestOptionConflicts:
    """옵션 충돌 해결 테스트"""

    def test_resolve_normal_option(self):
        """일반 옵션 - 충돌 없음"""
        opt = {"name": "verbose", "short": "v"}
        name, short = resolve_option_conflicts(opt)

        assert name == "verbose-sh"
        assert short == None

    def test_resolve_reserved_option_name(self):
        """예약된 옵션명 충돌"""
        opt = {"name": "help", "short": "x"}
        name, short = resolve_option_conflicts(opt)

        assert name == "help-sh"  # suffix 추가
        assert short == "x"  # 단축키는 그대로

    def test_resolve_reserved_shortcut(self, capsys):
        """예약된 단축키 충돌"""
        opt = {"name": "verbose", "short": "h"}
        name, short = resolve_option_conflicts(opt)

        assert name == "verbose-sh"
        assert short is None  # 충돌하는 단축키 제거

        # 경고 메시지 출력 확인
        captured = capsys.readouterr()
        assert "Warning" in captured.out
        assert "conflicts with CLI reserved shortcuts" in captured.out

    def test_resolve_both_conflicts(self, capsys):
        """옵션명과 단축키 모두 충돌"""
        opt = {"name": "help", "short": "h"}
        name, short = resolve_option_conflicts(opt)

        assert name == "help-sh"
        assert short is None

    def test_resolve_no_shortcut(self):
        """단축키가 없는 옵션"""
        opt = {"name": "verbose"}
        name, short = resolve_option_conflicts(opt)

        assert name == "verbose-sh"
        assert short is None


class TestArgumentCollection:
    """인자 수집 테스트"""

    def test_collect_simple_arguments(self):
        """단순 인자 수집"""
        args_metadata = [{"name": "file"}, {"name": "count"}]

        mock_getter = MagicMock(
            side_effect=lambda name: {"file": "test.txt", "count": "5"}.get(name)
        )

        result = collect_script_arguments(args_metadata, mock_getter)

        assert result == ["test.txt", "5"]
        assert mock_getter.call_count == 2

    def test_collect_with_none_values(self):
        """None 값이 있는 인자들"""
        args_metadata = [{"name": "file"}, {"name": "optional_arg"}]

        mock_getter = MagicMock(
            side_effect=lambda name: {"file": "test.txt", "optional_arg": None}.get(
                name
            )
        )

        result = collect_script_arguments(args_metadata, mock_getter)

        assert result == ["test.txt"]  # None 값은 제외

    def test_collect_empty_arguments(self):
        """빈 인자 목록"""
        result = collect_script_arguments([], MagicMock())
        assert result == []


class TestEnvironmentPreparation:
    """환경변수 준비 테스트"""


    def test_prepare_value_options(self):
        """값 옵션 환경변수"""
        options_metadata = [
            {"name": "config", "flag": False},
            {"name": "output-dir", "flag": False},
        ]

        mock_getter = MagicMock(
            side_effect=lambda name: {
                "config": "config.yaml",
                "output-dir": "/tmp/output",
            }.get(name)
        )

        env = prepare_script_environment(options_metadata, mock_getter)

        assert env["CLI_CONFIG"] == "config.yaml"
        assert env["CLI_OUTPUT_DIR"] == "/tmp/output"  # 하이픈을 언더스코어로

    def test_prepare_reserved_option_names(self):
        """예약된 옵션명 처리"""
        options_metadata = [{"name": "help", "flag": True}]  # 원래 이름

        # getter는 변경된 이름으로 호출됨
        mock_getter = MagicMock(side_effect=lambda name: {"help-sh": True}.get(name))

        env = prepare_script_environment(options_metadata, mock_getter)

        # 환경변수는 원래 이름으로 설정
        assert env["CLI_HELP"] == "1"


class TestRunnerBlockProcessing:
    """SCRIPT-RUNNER 블록 처리 테스트"""

    def test_remove_existing_runner_block(self):
        """기존 블록 제거"""
        content = f"""#!/bin/bash
{SCRIPT_RUNNER_START}
OLD_VAR=value
{SCRIPT_RUNNER_END}
echo "script content"
"""

        result = remove_existing_runner_block(content)

        assert SCRIPT_RUNNER_START not in result
        assert SCRIPT_RUNNER_END not in result
        assert "OLD_VAR=value" not in result
        assert 'echo "script content"' in result

    def test_generate_runner_block_with_options(self):
        """옵션이 있는 러너 블록 생성"""
        metadata = {
            "options": [
                {"name": "verbose", "flag": True},
                {"name": "config", "flag": False, "default": "config.yaml"},
                {"name": "timeout", "flag": False},  # 기본값 없음
            ],
            "args": [],
        }

        block = generate_runner_block(metadata)

        assert SCRIPT_RUNNER_START in block
        assert SCRIPT_RUNNER_END in block
        # assert "VERBOSE=${CLI_VERBOSE:-0}" in block  # flag
        assert "CONFIG=${CONFIG:-${CLI_CONFIG:-config.yaml}}" in block  # 기본값 있음
        assert "TIMEOUT=${TIMEOUT:-${CLI_TIMEOUT}}" in block  # 기본값 없음

    def test_generate_runner_block_with_args(self):
        """인자가 있는 러너 블록 생성"""
        metadata = {
            "options": [],
            "args": [{"name": "input-file"}, {"name": "count", "default": "1"}],
        }

        block = generate_runner_block(metadata)

        assert "INPUT_FILE=${1:-}" in block
        assert "COUNT=${2:-1}" in block

    def test_generate_runner_block_bash_syntax_validation(self):
        """Bash 문법 검증 - bad substitution 방지"""
        metadata = {
            "options": [
                {"name": "changelog", "flag": False, "default": "CHANGELOG.md"},
                {"name": "assets", "flag": False},  # 기본값 없음
                {"name": "title", "flag": False, "default": ""},  # 빈 기본값
                {"name": "debug", "flag": True},  # flag 옵션
            ],
            "args": [{"name": "version"}, {"name": "target", "default": "main"}],
        }

        block = generate_runner_block(metadata)

        # 생성된 블록이 올바른 bash 문법인지 확인
        lines = block.split("\n")

        # 각 라인이 올바른 변수 할당 문법인지 검증
        for line in lines:
            if "=" in line and not line.strip().startswith("#"):
                # ${$VAR:-...} 형태의 잘못된 문법이 없는지 확인
                assert "${$" not in line, f"Bad substitution syntax found in: {line}"

                # ${VAR:-...} 형태의 올바른 문법인지 확인
                if "${" in line:
                    # 기본값이 있는 옵션들
                    if "CHANGELOG=" in line:
                        assert (
                            line.strip()
                            == "CHANGELOG=${CHANGELOG:-${CLI_CHANGELOG:-CHANGELOG.md}}"
                        )
                    elif "ASSETS=" in line:
                        assert line.strip() == "ASSETS=${ASSETS:-${CLI_ASSETS}}"
                    elif "TITLE=" in line:
                        assert line.strip() == "TITLE=${TITLE:-${CLI_TITLE}}"
                    elif "DEBUG=" in line:
                        assert line.strip() == "DEBUG=${CLI_DEBUG:-0}"
                    elif "VERSION=" in line:
                        assert line.strip() == "VERSION=${1:-}"
                    elif "TARGET=" in line:
                        assert line.strip() == "TARGET=${2:-main}"

    def test_runner_block_real_world_scenario(self):
        """실제 시나리오 테스트 - GitHub release 스크립트"""
        metadata = {
            "description": "Create GitHub release",
            "args": [{"name": "version", "description": "Release version"}],
            "options": [
                {
                    "name": "changelog",
                    "short": "c",
                    "flag": False,
                    "default": "CHANGELOG.md",
                },
                {"name": "prerelease", "short": "p", "flag": True},
                {"name": "draft", "short": "d", "flag": True},
                {"name": "assets", "short": "a", "flag": False},
                {"name": "title", "short": "t", "flag": False},
            ],
        }

        block = generate_runner_block(metadata)

        # 예상되는 라인들이 포함되어 있는지 확인
        expected_lines = [
            "CHANGELOG=${CHANGELOG:-${CLI_CHANGELOG:-CHANGELOG.md}}",
            "PRERELEASE=${CLI_PRERELEASE:-0}",
            "DRAFT=${CLI_DRAFT:-0}",
            "ASSETS=${ASSETS:-${CLI_ASSETS}}",
            "TITLE=${TITLE:-${CLI_TITLE}}",
            "VERSION=${1:-}",
        ]

        for expected_line in expected_lines:
            assert expected_line in block, f"Expected line not found: {expected_line}"

        # bad substitution 패턴이 없는지 확인
        assert "${$" not in block

    def test_runner_block_bash_execution_validation(self):
        """생성된 SCRIPT-RUNNER 블록이 실제 bash에서 실행 가능한지 검증"""
        import subprocess

        metadata = {
            "options": [
                {"name": "config", "flag": False, "default": "config.yaml"},
                {"name": "verbose", "flag": True},
                {"name": "output-dir", "flag": False},
            ],
            "args": [{"name": "input", "default": "input.txt"}],
        }

        block = generate_runner_block(metadata)

        # 실제 bash 스크립트로 만들어서 문법 검사
        test_script = f"""#!/bin/bash
{block}
echo "Syntax OK"
"""

        # 임시 파일 생성하여 bash 문법 검사
        temp_file = create_temp_script_file(test_script, "syntax_test_")

        try:
            # bash -n으로 문법만 검사 (실행하지 않음)
            result = subprocess.run(
                ["bash", "-n", temp_file], capture_output=True, text=True
            )

            # 문법 에러가 없어야 함
            assert result.returncode == 0, f"Bash syntax error: {result.stderr}"

        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_insert_after_shebang(self):
        """Shebang 다음에 삽입"""
        content = """#!/bin/bash
echo "hello"
"""
        block = "# RUNNER BLOCK\n"

        result = insert_after_shebang(content, block)

        lines = result.split("\n")
        assert lines[0] == "#!/bin/bash"
        assert lines[1] == ""
        assert lines[2] == "# RUNNER BLOCK"
        assert lines[3] == 'echo "hello"'

    def test_insert_after_user_setting(self):
        """USER SETTING 다음에 삽입"""
        content = f"""#!/bin/bash
{USER_SETTING_MARKER}
# User config
CONFIG=value

echo "script"
"""
        block = "# RUNNER BLOCK\n"

        result = insert_after_user_setting(content, block)

        assert USER_SETTING_MARKER in result
        assert "# RUNNER BLOCK" in result
        assert result.index(USER_SETTING_MARKER) < result.index("# RUNNER BLOCK")
        assert result.index("# RUNNER BLOCK") < result.index('echo "script"')

    def test_insert_runner_block_chooses_correctly(self):
        """적절한 삽입 위치 선택"""
        # USER SETTING이 있으면 그 다음에
        content_with_marker = f"""#!/bin/bash
{USER_SETTING_MARKER}
echo "test"
"""
        block = "# BLOCK\n"
        result = insert_runner_block(content_with_marker, block)
        assert USER_SETTING_MARKER in result

        # USER SETTING이 없으면 shebang 다음에
        content_without_marker = """#!/bin/bash
echo "test"
"""
        result = insert_runner_block(content_without_marker, block)
        lines = result.split("\n")
        assert lines[0] == "#!/bin/bash"
        assert "# BLOCK" in lines[2]


class TestTempFileOperations:
    """임시 파일 작업 테스트"""

    def test_create_temp_script_file(self):
        """임시 스크립트 파일 생성"""
        content = """#!/bin/bash
echo "test"
"""

        temp_path = create_temp_script_file(content, "test_")

        try:
            assert os.path.exists(temp_path)
            assert temp_path.endswith(".sh")
            assert "test_" in temp_path

            # 내용 확인
            with open(temp_path, "r") as f:
                assert f.read() == content

            # 실행 권한 확인
            assert os.access(temp_path, os.X_OK)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_transform_script_content(self):
        """스크립트 내용 변형"""
        # 임시 스크립트 파일 생성
        content = """#!/bin/bash
echo "original"
"""
        temp_fd, temp_path = tempfile.mkstemp(suffix=".sh")
        try:
            with os.fdopen(temp_fd, "w") as f:
                f.write(content)

            metadata = {
                "options": [{"name": "debug", "flag": True}],
                "args": [{"name": "file"}],
            }

            result = transform_script_content(temp_path, metadata)

            assert SCRIPT_RUNNER_START in result
            assert SCRIPT_RUNNER_END in result
            assert "DEBUG=${CLI_DEBUG:-0}" in result
            assert "FILE=${1:-}" in result
            assert 'echo "original"' in result

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_create_transformed_temp_script(self):
        """변형된 임시 스크립트 생성"""
        # 원본 스크립트 파일 생성
        content = """#!/bin/bash
echo "test"
"""
        temp_fd, original_path = tempfile.mkstemp(suffix=".sh")
        try:
            with os.fdopen(temp_fd, "w") as f:
                f.write(content)

            metadata = {"options": [], "args": []}

            transformed_path = create_transformed_temp_script(original_path, metadata)

            try:
                assert os.path.exists(transformed_path)
                assert transformed_path != original_path

                with open(transformed_path, "r") as f:
                    transformed_content = f.read()

                assert SCRIPT_RUNNER_START in transformed_content
                assert SCRIPT_RUNNER_END in transformed_content

            finally:
                if os.path.exists(transformed_path):
                    os.unlink(transformed_path)

        finally:
            if os.path.exists(original_path):
                os.unlink(original_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

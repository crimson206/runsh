# tests/test_script_command_refactored.py - 리팩토링된 ScriptCommand 테스트

import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from cleo.testers.command_tester import CommandTester
from cleo.application import Application

from runsh.commands.script_command import ScriptCommand


class TestScriptCommandRefactored:
    """리팩토링된 ScriptCommand 테스트 클래스"""

    def setup_method(self):
        """각 테스트 전에 실행"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.sample_script_path = self.temp_dir / "test_script.sh"

    def teardown_method(self):
        """각 테스트 후에 실행"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_sample_script(self, content: str) -> str:
        """테스트용 스크립트 파일 생성"""
        with open(self.sample_script_path, "w") as f:
            f.write(content)
        os.chmod(self.sample_script_path, 0o755)
        return str(self.sample_script_path)

    def test_command_creation_with_utils(self):
        """Utils를 사용한 명령어 생성 테스트"""
        script_content = """#!/bin/bash
# @description: Test script with utils
echo "Hello World"
"""
        script_path = self.create_sample_script(script_content)

        metadata = {
            "description": "Test script with utils",
            "args": [{"name": "name", "description": "User name"}],
            "options": [
                {
                    "name": "verbose",
                    "short": "v",
                    "description": "Verbose output",
                    "flag": True,
                }
            ],
        }

        command = ScriptCommand(script_path, metadata, "bash")

        # 기본 속성 확인
        assert command.name == "test_script"
        assert command.description == "Test script with utils"
        assert len(command.arguments) == 1
        assert len(command.options) == 1


    @patch("runsh.commands.script_command.create_transformed_temp_script")
    @patch("subprocess.run")
    def test_temp_file_cleanup_on_success(self, mock_subprocess, mock_create_temp):
        """성공 시 임시 파일 정리 테스트"""
        temp_file = "/tmp/test_cleanup.sh"
        mock_create_temp.return_value = temp_file
        mock_subprocess.return_value.returncode = 0

        # 임시 파일 실제로 생성
        with open(temp_file, "w") as f:
            f.write("#!/bin/bash\necho test")

        script_path = self.create_sample_script("#!/bin/bash\necho test")
        metadata = {"description": "Test", "args": [], "options": []}

        command = ScriptCommand(script_path, metadata, "bash")

        with patch.object(command, "argument"), patch.object(command, "option"):
            command.handle()

        # 임시 파일이 정리되었는지 확인
        assert not os.path.exists(temp_file)

    @patch("runsh.commands.script_command.create_transformed_temp_script")
    @patch("subprocess.run")
    def test_temp_file_cleanup_on_exception(self, mock_subprocess, mock_create_temp):
        """예외 발생 시에도 임시 파일 정리 테스트"""
        temp_file = "/tmp/test_cleanup_exception.sh"
        mock_create_temp.return_value = temp_file
        mock_subprocess.side_effect = Exception("Subprocess failed")

        # 임시 파일 실제로 생성
        with open(temp_file, "w") as f:
            f.write("#!/bin/bash\necho test")

        script_path = self.create_sample_script("#!/bin/bash\necho test")
        metadata = {"description": "Test", "args": [], "options": []}

        command = ScriptCommand(script_path, metadata, "bash")

        with patch.object(command, "argument"), patch.object(command, "option"):
            with pytest.raises(Exception):
                command.handle()

        # 예외가 발생해도 임시 파일이 정리되었는지 확인
        assert not os.path.exists(temp_file)


    @patch("subprocess.run")
    def test_integration_with_application(self, mock_subprocess):
        """Application과의 통합 테스트"""
        mock_subprocess.return_value.returncode = 0

        script_path = self.create_sample_script(
            """#!/bin/bash
# @description: Integration test
# @arg name: User name
echo "Hello $NAME"
"""
        )

        metadata = {
            "description": "Integration test",
            "args": [{"name": "name", "description": "User name"}],
            "options": [],
        }

        # Application에 명령어 추가
        app = Application()
        command = ScriptCommand(script_path, metadata, "bash")
        app.add(command)

        # CommandTester로 실행
        command_tester = CommandTester(app.find(command.name))
        exit_code = command_tester.execute("John")

        assert exit_code == 0
        mock_subprocess.assert_called_once()

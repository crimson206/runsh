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
        with open(self.sample_script_path, 'w') as f:
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
            "options": [{"name": "verbose", "short": "v", "description": "Verbose output", "flag": True}]
        }
        
        command = ScriptCommand(script_path, metadata, "bash")
        
        # 기본 속성 확인
        assert command.name == "test_script"
        assert command.description == "Test script with utils"
        assert len(command.arguments) == 1
        assert len(command.options) == 1
    
    @patch('runsh.commands.script_command.resolve_option_conflicts')
    def test_option_conflict_resolution_integration(self, mock_resolve):
        """옵션 충돌 해결 함수 통합 테스트"""
        mock_resolve.return_value = ("help-sh", None)
        
        script_path = self.create_sample_script("#!/bin/bash\necho test")
        metadata = {
            "description": "Test",
            "args": [],
            "options": [{"name": "help", "short": "h", "flag": True}]
        }
        
        command = ScriptCommand(script_path, metadata, "bash")
        
        # resolve_option_conflicts가 호출되었는지 확인
        mock_resolve.assert_called_once()
        
        # 결과가 올바르게 적용되었는지 확인
        assert command.options[0].name == "help-sh"
        assert command.options[0].shortcut is None
    
    @patch('runsh.commands.script_command.collect_script_arguments')
    @patch('runsh.commands.script_command.prepare_script_environment')  
    @patch('runsh.commands.script_command.create_transformed_temp_script')
    @patch('subprocess.run')
    def test_handle_method_integration(self, mock_subprocess, mock_create_temp, 
                                     mock_prepare_env, mock_collect_args):
        """handle 메서드의 utils 함수 통합 테스트"""
        # Mock 설정
        mock_collect_args.return_value = ["arg1", "arg2"]
        mock_prepare_env.return_value = {"CLI_VERBOSE": "1"}
        mock_create_temp.return_value = "/tmp/test_script.sh"
        mock_subprocess.return_value.returncode = 0
        
        script_path = self.create_sample_script("#!/bin/bash\necho test")
        metadata = {
            "description": "Test",
            "args": [{"name": "name"}],
            "options": [{"name": "verbose", "flag": True}]
        }
        
        command = ScriptCommand(script_path, metadata, "bash")
        
        # Mock 인자/옵션 값들
        with patch.object(command, 'argument') as mock_arg, \
             patch.object(command, 'option') as mock_opt:
            
            result = command.handle()
        
        # Utils 함수들이 올바르게 호출되었는지 확인
        mock_collect_args.assert_called_once_with(metadata["args"], command.argument)
        mock_prepare_env.assert_called_once_with(metadata["options"], command.option)
        mock_create_temp.assert_called_once_with(script_path, metadata)
        
        # subprocess가 올바른 인자로 호출되었는지 확인
        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args
        assert call_args[0][0] == ["bash", "/tmp/test_script.sh", "arg1", "arg2"]
        assert call_args[1]["env"]["CLI_VERBOSE"] == "1"
        
        assert result == 0
    
    @patch('runsh.commands.script_command.create_transformed_temp_script')
    @patch('subprocess.run')
    def test_temp_file_cleanup_on_success(self, mock_subprocess, mock_create_temp):
        """성공 시 임시 파일 정리 테스트"""
        temp_file = "/tmp/test_cleanup.sh"
        mock_create_temp.return_value = temp_file
        mock_subprocess.return_value.returncode = 0
        
        # 임시 파일 실제로 생성
        with open(temp_file, 'w') as f:
            f.write("#!/bin/bash\necho test")
        
        script_path = self.create_sample_script("#!/bin/bash\necho test")
        metadata = {"description": "Test", "args": [], "options": []}
        
        command = ScriptCommand(script_path, metadata, "bash")
        
        with patch.object(command, 'argument'), patch.object(command, 'option'):
            command.handle()
        
        # 임시 파일이 정리되었는지 확인
        assert not os.path.exists(temp_file)
    
    @patch('runsh.commands.script_command.create_transformed_temp_script')
    @patch('subprocess.run')
    def test_temp_file_cleanup_on_exception(self, mock_subprocess, mock_create_temp):
        """예외 발생 시에도 임시 파일 정리 테스트"""
        temp_file = "/tmp/test_cleanup_exception.sh"
        mock_create_temp.return_value = temp_file
        mock_subprocess.side_effect = Exception("Subprocess failed")
        
        # 임시 파일 실제로 생성
        with open(temp_file, 'w') as f:
            f.write("#!/bin/bash\necho test")
        
        script_path = self.create_sample_script("#!/bin/bash\necho test")
        metadata = {"description": "Test", "args": [], "options": []}
        
        command = ScriptCommand(script_path, metadata, "bash")
        
        with patch.object(command, 'argument'), patch.object(command, 'option'):
            with pytest.raises(Exception):
                command.handle()
        
        # 예외가 발생해도 임시 파일이 정리되었는지 확인
        assert not os.path.exists(temp_file)
    
    def test_property_generation(self):
        """Command 속성 생성 테스트 (arguments, options)"""
        script_path = self.create_sample_script("#!/bin/bash\necho test")
        metadata = {
            "description": "Property test",
            "args": [
                {"name": "required_arg", "description": "Required argument"},
                {"name": "optional_arg", "description": "Optional argument", "optional": True},
                {"name": "default_arg", "description": "Argument with default", "default": "default_value"}
            ],
            "options": [
                {"name": "flag_option", "description": "Flag option", "flag": True},
                {"name": "value_option", "description": "Value option", "flag": False},
                {"name": "default_option", "description": "Option with default", "flag": False, "default": "default"}
            ]
        }
        
        command = ScriptCommand(script_path, metadata, "bash")
        
        # Arguments 확인
        args = command.arguments
        assert len(args) == 3
        assert not args[0].is_optional()  # required_arg
        assert args[1].is_optional()      # optional_arg
        assert args[2].is_optional()      # default_arg (기본값이 있으면 optional)
        assert args[2].default == "default_value"
        
        # Options 확인
        opts = command.options
        assert len(opts) == 3
        assert opts[0].is_flag()          # flag_option
        assert not opts[1].is_flag()      # value_option
        assert not opts[2].is_flag()      # default_option
        assert opts[2].default == "default"
    
    @patch('subprocess.run')
    def test_integration_with_application(self, mock_subprocess):
        """Application과의 통합 테스트"""
        mock_subprocess.return_value.returncode = 0
        
        script_path = self.create_sample_script("""#!/bin/bash
# @description: Integration test
# @arg name: User name
echo "Hello $NAME"
""")
        
        metadata = {
            "description": "Integration test",
            "args": [{"name": "name", "description": "User name"}],
            "options": []
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

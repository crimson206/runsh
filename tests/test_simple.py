# tests/test_utils.py - Utils 함수들 테스트

import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import MagicMock
from runsh.parser import parse_script_metadata

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

class TestTempFileOperations:
    """임시 파일 작업 테스트"""
    
    def test_create_temp_script_file(self):
        """임시 스크립트 파일 생성"""
        content = open("/home/crimson/manager/cursor-workspace/runsh/scripts/git_tag.sh", 'r').read()
        
        temp_path = create_temp_script_file(content, "test_")
        
        try:
            assert os.path.exists(temp_path)
            assert temp_path.endswith('.sh')
            assert 'test_' in temp_path
            
            # 내용 확인
            with open(temp_path, 'r') as f:
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
        temp_fd, temp_path = tempfile.mkstemp(suffix='.sh')
        try:
            with os.fdopen(temp_fd, 'w') as f:
                f.write(content)
            
            metadata = {
                "options": [{"name": "debug", "flag": True}],
                "args": [{"name": "file"}]
            }
            
            result = transform_script_content(temp_path, metadata)
            
            assert SCRIPT_RUNNER_START in result
            assert SCRIPT_RUNNER_END in result
            assert "DEBUG=${CLI_DEBUG:-0}" in result
            assert "FILE=${1:-}" in result
            assert "echo \"original\"" in result
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_create_transformed_temp_script(self):
        """변형된 임시 스크립트 생성"""
        # 원본 스크립트 파일 생성
        content = open("/home/crimson/manager/cursor-workspace/runsh/scripts/git_tag.sh", 'r').read()

        temp_fd, original_path = tempfile.mkstemp(suffix='.sh')
        try:
            with os.fdopen(temp_fd, 'w') as f:
                f.write(content)
            
            metadata = parse_script_metadata("/home/crimson/manager/cursor-workspace/runsh/scripts/git_tag.sh")
            
            transformed_path = create_transformed_temp_script(original_path, metadata)
            
            try:
                assert os.path.exists(transformed_path)
                assert transformed_path != original_path
                
                with open(transformed_path, 'r') as f:
                    transformed_content = f.read()
                
                assert SCRIPT_RUNNER_START in transformed_content
                assert SCRIPT_RUNNER_END in transformed_content
                
            finally:
                if os.path.exists(transformed_path):
                    os.unlink(transformed_path)
                    
        finally:
            if os.path.exists(original_path):
                os.unlink(original_path)


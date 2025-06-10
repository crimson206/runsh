# utils/script_processing.py - 스크립트 처리 유틸리티 함수들

import os
import re
import tempfile
from typing import Dict, List, Tuple, Any

from ..constants import (
    CLEO_RESERVED_OPTIONS,
    CLEO_RESERVED_SHORTCUTS,
    TEMP_SCRIPT_PREFIX,
    SCRIPT_RUNNER_START,
    SCRIPT_RUNNER_END,
    USER_SETTING_MARKER,
)


def resolve_option_conflicts(opt: dict) -> Tuple[str, str]:
    """
    Cleo 예약 옵션/단축키 충돌 해결
    
    Args:
        opt: 옵션 정의 딕셔너리
        
    Returns:
        (option_name, short): 충돌이 해결된 옵션명과 단축키
    """
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


def collect_script_arguments(args_metadata: List[dict], argument_getter) -> List[str]:
    """
    CLI arguments 수집
    
    Args:
        args_metadata: 인자 메타데이터 리스트
        argument_getter: 인자 값을 가져오는 함수 (보통 self.argument)
        
    Returns:
        수집된 인자 값들의 리스트
    """
    script_args = []
    for arg_def in args_metadata:
        value = argument_getter(arg_def["name"])
        if value:
            script_args.append(str(value))
    return script_args


def prepare_script_environment(options_metadata: List[dict], option_getter) -> Dict[str, str]:
    """
    스크립트 실행을 위한 환경변수 준비
    
    Args:
        options_metadata: 옵션 메타데이터 리스트
        option_getter: 옵션 값을 가져오는 함수 (보통 self.option)
        
    Returns:
        환경변수 딕셔너리
    """
    env = os.environ.copy()

    for opt_def in options_metadata:
        # 원래 이름으로 옵션 체크 (suffix 없는)
        original_name = opt_def["name"]
        option_name = original_name
        if original_name in CLEO_RESERVED_OPTIONS:
            option_name = f"{original_name}-sh"

        option_value = option_getter(option_name)
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


def remove_existing_runner_block(content: str) -> str:
    """
    기존 SCRIPT-RUNNER 블록 제거
    
    Args:
        content: 스크립트 내용
        
    Returns:
        SCRIPT-RUNNER 블록이 제거된 내용
    """
    pattern = f"{re.escape(SCRIPT_RUNNER_START)}.*?{re.escape(SCRIPT_RUNNER_END)}\n"
    return re.sub(pattern, "", content, flags=re.DOTALL)


def generate_runner_block(script_metadata: dict) -> str:
    """
    SCRIPT-RUNNER 블록 생성
    
    Args:
        script_metadata: 스크립트 메타데이터 (args, options 포함)
        
    Returns:
        생성된 SCRIPT-RUNNER 블록 문자열
    """
    runner_block = f"{SCRIPT_RUNNER_START}\n"

    # 옵션 환경변수들
    for opt in script_metadata.get("options", []):
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
    for i, arg in enumerate(script_metadata.get("args", []), 1):
        var_name = arg["name"].replace("-", "_").upper()
        default = arg.get("default", "")
        runner_block += f"{var_name}=${{{i}:-{default}}}\n"

    runner_block += f"{SCRIPT_RUNNER_END}\n\n"
    return runner_block


def insert_runner_block(content: str, runner_block: str) -> str:
    """
    적절한 위치에 SCRIPT-RUNNER 블록 삽입
    
    Args:
        content: 원본 스크립트 내용
        runner_block: 삽입할 SCRIPT-RUNNER 블록
        
    Returns:
        SCRIPT-RUNNER 블록이 삽입된 스크립트 내용
    """
    if USER_SETTING_MARKER in content:
        return insert_after_user_setting(content, runner_block)
    else:
        return insert_after_shebang(content, runner_block)


def insert_after_user_setting(content: str, runner_block: str) -> str:
    """
    USER SETTING 섹션 다음에 삽입
    
    Args:
        content: 원본 스크립트 내용
        runner_block: 삽입할 블록
        
    Returns:
        블록이 삽입된 스크립트 내용
    """
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


def insert_after_shebang(content: str, runner_block: str) -> str:
    """
    shebang 다음에 삽입
    
    Args:
        content: 원본 스크립트 내용
        runner_block: 삽입할 블록
        
    Returns:
        블록이 삽입된 스크립트 내용
    """
    lines = content.split("\n")
    if lines[0].startswith("#!"):
        insert_content = "\n".join(lines[1:])
        return lines[0] + "\n\n" + runner_block + insert_content
    else:
        return runner_block + content


def create_temp_script_file(content: str, prefix: str = TEMP_SCRIPT_PREFIX) -> str:
    """
    임시 스크립트 파일 생성
    
    Args:
        content: 스크립트 내용
        prefix: 임시 파일명 접두사
        
    Returns:
        생성된 임시 파일 경로
        
    Raises:
        Exception: 파일 생성 실패 시
    """
    temp_fd, temp_path = tempfile.mkstemp(suffix=".sh", prefix=prefix)
    try:
        with os.fdopen(temp_fd, "w") as temp_file:
            temp_file.write(content)

        # 실행 권한 추가
        os.chmod(temp_path, 0o755)

        return temp_path
    except Exception:
        # 에러 시 파일 정리
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise


def transform_script_content(script_path: str, script_metadata: dict) -> str:
    """
    스크립트 내용을 변형하여 SCRIPT-RUNNER 블록 추가
    
    Args:
        script_path: 원본 스크립트 파일 경로
        script_metadata: 스크립트 메타데이터
        
    Returns:
        변형된 스크립트 내용
    """
    with open(script_path, "r") as f:
        content = f.read()

    # 기존 SCRIPT-RUNNER 블록 제거 (혹시 있다면)
    content = remove_existing_runner_block(content)

    # 새 SCRIPT-RUNNER 블록 생성
    runner_block = generate_runner_block(script_metadata)

    # 적절한 위치에 삽입
    new_content = insert_runner_block(content, runner_block)

    return new_content


def create_transformed_temp_script(script_path: str, script_metadata: dict) -> str:
    """
    원본 스크립트에서 SCRIPT-RUNNER 블록을 추가한 임시 스크립트 생성
    
    Args:
        script_path: 원본 스크립트 파일 경로
        script_metadata: 스크립트 메타데이터
        
    Returns:
        생성된 임시 스크립트 파일 경로
    """
    transformed_content = transform_script_content(script_path, script_metadata)
    return create_temp_script_file(transformed_content)
# constants.py - Script Runner 상수 정의

# Cleo 예약 옵션들 (충돌 방지용)
CLEO_RESERVED_OPTIONS = {
    "verbose",
    "quiet",
    "help",
    "version",
    "no-interaction",
    "ansi",
    "no-ansi",
}

# Cleo 예약 단축키들 (충돌 방지용)
CLEO_RESERVED_SHORTCUTS = {"v", "q", "h", "V", "n"}

# 기본 설정값들
DEFAULT_SCRIPTS_DIR = "./scripts"
DEFAULT_SHELL = "bash"

# 임시 파일 접두사
TEMP_SCRIPT_PREFIX = "script_runner_"

# SCRIPT-RUNNER 블록 마커
SCRIPT_RUNNER_START = "# <SCRIPT-RUNNER>"
SCRIPT_RUNNER_END = "# </SCRIPT-RUNNER>"

# 사용자 설정 섹션 마커
USER_SETTING_MARKER = "# USER SETTING"

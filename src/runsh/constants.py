# constants.py - Script Runner 상수 정의

# Cleo 예약 옵션들 (충돌 방지용)
CLEO_RESERVED_OPTIONS = {
    'verbose', 'quiet', 'help', 'version', 'no-interaction', 
    'ansi', 'no-ansi'
}

# Cleo 예약 단축키들 (충돌 방지용)
CLEO_RESERVED_SHORTCUTS = {
    'v', 'q', 'h', 'V', 'n'
}

# 기본 설정값들
DEFAULT_SCRIPTS_DIR = './scripts'
DEFAULT_SHELL = 'bash'

# 지원되는 셸 목록
SUPPORTED_SHELLS = {'bash', 'sh', 'zsh'}

# 임시 파일 접두사
TEMP_SCRIPT_PREFIX = 'runsh_temp_'

# SCRIPT-RUNNER 블록 마커
SCRIPT_RUNNER_START = '# <SCRIPT-RUNNER>'
SCRIPT_RUNNER_END = '# </SCRIPT-RUNNER>'

# 사용자 설정 섹션 마커
USER_SETTING_MARKER = '# USER SETTING'

# RunSH 디렉토리 및 파일들
RUNSH_DIR = '.runsh'
CONFIG_FILENAME = 'config.yaml'
CACHE_DIR = 'cache'

# 환경변수명들
ENV_SCRIPTS_DIR = 'RUNSH_SCRIPTS_DIR'
ENV_SHELL = 'RUNSH_SHELL'

# 캐시 관련
CACHE_METADATA_FILE = '.metadata'
CACHE_MAX_AGE_HOURS = 24  # 24시간 후 캐시 만료
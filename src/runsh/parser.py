# parser.py - 스크립트 메타데이터 파싱

import re
from typing import Dict, Any


def parse_script_metadata(script_path: str) -> Dict[str, Any]:
    """
    .sh 파일에서 메타데이터 파싱

    형식:
    # @description: 스크립트 설명
    # @arg name1 [optional] [default=value]: 설명
    # @option verbose,v [flag]: 자세한 출력
    """
    metadata = {"args": [], "options": []}

    with open(script_path, "r") as f:
        for line in f:
            line = line.strip()

            if line.startswith("# @description:"):
                metadata["description"] = _parse_description(line)
            elif line.startswith("# @arg"):
                arg_info = _parse_argument(line)
                if arg_info:
                    metadata["args"].append(arg_info)
            elif line.startswith("# @option"):
                opt_info = _parse_option(line)
                if opt_info:
                    metadata["options"].append(opt_info)

    return metadata


def _parse_description(line: str) -> str:
    """description 라인 파싱"""
    return line.split(":", 1)[1].strip()


def _parse_argument(line: str) -> Dict[str, Any]:
    """argument 라인 파싱"""
    match = re.match(r"# @arg (\w+)(\s+\[([^\]]+)\])*\s*:\s*(.*)", line)
    if not match:
        return None

    name, _, modifiers, desc = match.groups()
    arg_info = {"name": name, "description": desc}

    if modifiers:
        if "optional" in modifiers:
            arg_info["optional"] = True
        if "default=" in modifiers:
            default = re.search(r"default=([^\]]+)", modifiers)
            if default:
                arg_info["default"] = default.group(1)

    return arg_info


def _parse_option(line: str) -> Dict[str, Any]:
    """option 라인 파싱"""
    match = re.match(r"# @option ([^,]+)(?:,(\w+))?(\s+\[([^\]]+)\])?\s*:\s*(.*)", line)
    if not match:
        return None

    name, short, _, modifiers, desc = match.groups()
    opt_info = {"name": name.strip(), "description": desc, "short": short}

    if modifiers:
        if "flag" in modifiers:
            opt_info["flag"] = True
        elif "default=" in modifiers:
            # value option with default
            default = re.search(r"default=([^\]]+)", modifiers)
            if default:
                opt_info["default"] = default.group(1)
                opt_info["flag"] = False
        else:
            # required value option
            opt_info["flag"] = False
    else:
        # no modifiers = required value option
        opt_info["flag"] = False

    return opt_info

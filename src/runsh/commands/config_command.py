# commands/config_command.py - Config 관리 명령어

from cleo.commands.command import Command
from cleo.helpers import argument

from ..config import Config, create_sample_config, show_config_info


class ConfigCommand(Command):
    """설정 관련 명령어"""

    name = "config-rs"
    description = "Manage script-runner configuration"

    arguments = [
        argument(
            "action", "Action to perform (show, init)", optional=True, default="show"
        )
    ]

    def handle(self):
        action = self.argument("action")

        if action == "show":
            self._show_config()
        elif action == "init":
            self._init_config()
        else:
            self.error(f"Unknown action: {action}")
            self.line("Available actions: show, init")
            return 1

        return 0

    def _show_config(self):
        """현재 설정 표시"""
        config = Config()
        show_config_info(config)

    def _init_config(self):
        """설정 파일 생성"""
        try:
            config_path = create_sample_config()
            self.info(f"Created sample configuration file: {config_path}")
            self.line("Edit this file to customize your settings.")
        except Exception as e:
            self.error(f"Failed to create config file: {e}")
            return 1

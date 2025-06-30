"""
配置管理模块 - 处理应用程序的默认设置和用户偏好

功能包括：
- 管理默认图片处理参数
- 保存/加载用户偏好
- 验证配置有效性
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path

# 初始化日志
logger = logging.getLogger(__name__)


class ConfigError(Exception):
    """配置相关异常基类"""
    pass


class ConfigManager:
    """
    配置管理器，处理应用程序配置

    配置优先级：
    1. 运行时传入的参数
    2. 用户自定义配置
    3. 默认配置
    """

    # 默认配置
    DEFAULT_CONFIG = {
        'image_processing': {
            'default_format': 'JPEG',
            'default_quality': 85,
            'resize_options': {
                'default_width': 800,
                'default_height': 600,
                'default_scale': 1.0
            },
            'watermark': {
                'text': 'My Watermark',
                'font_size': 20,
                'opacity': 0.5,
                'position': 'bottom-right'
            },
            'rotation': {
                'default_degrees': 0
            }
        },
        'ui': {
            'theme': 'light',
            'recent_folders': [],
            'window_size': [800, 600]
        }
    }

    def __init__(self, config_file: Optional[str] = None):
        """
        初始化配置管理器

        :param config_file: 自定义配置文件路径，如果为None则使用默认位置
        """
        self.config = self.DEFAULT_CONFIG.copy()
        self.config_file = config_file or self.get_default_config_path()

        # 确保配置目录存在
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)

        # 加载用户配置
        self.load_config()

    @staticmethod
    def get_default_config_path() -> str:
        """
        获取默认配置文件路径

        :return: 跨平台的默认配置文件路径
        """
        if os.name == 'nt':  # Windows
            appdata = os.getenv('APPDATA')
            return os.path.join(appdata, 'BatchImageProcessor', 'config.json')
        else:  # Linux/Mac
            return os.path.join(str(Path.home()), '.config', 'batch_image_processor', 'config.json')

    def load_config(self) -> None:
        """
        从文件加载用户配置，合并到默认配置中
        """
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    self._merge_configs(self.config, user_config)
        except Exception as e:
            logger.warning(f"Failed to load config file: {str(e)}")

    def save_config(self) -> None:
        """
        将当前配置保存到文件
        """
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save config file: {str(e)}")
            raise ConfigError(f"Could not save config: {str(e)}")

    def _merge_configs(self, base: Dict[str, Any], update: Dict[str, Any]) -> None:
        """
        递归合并两个配置字典

        :param base: 基础配置（会被修改）
        :param update: 更新配置
        """
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_configs(base[key], value)
            else:
                base[key] = value

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        通过点分隔的路径获取配置值

        :param key_path: 例如 'image_processing.default_format'
        :param default: 如果键不存在返回的默认值
        :return: 配置值或默认值
        """
        keys = key_path.split('.')
        value = self.config

        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key_path: str, value: Any, save: bool = False) -> None:
        """
        设置配置值

        :param key_path: 例如 'image_processing.default_format'
        :param value: 要设置的值
        :param save: 是否立即保存到文件
        """
        keys = key_path.split('.')
        config = self.config

        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]

        config[keys[-1]] = value

        if save:
            self.save_config()

    def add_recent_folder(self, folder_path: str, max_recent: int = 5) -> None:
        """
        添加最近使用的文件夹到配置

        :param folder_path: 要添加的文件夹路径
        :param max_recent: 保留的最大最近项目数
        """
        recent = self.get('ui.recent_folders', [])

        # 如果已存在则移除
        if folder_path in recent:
            recent.remove(folder_path)

        # 添加到开头
        recent.insert(0, folder_path)

        # 限制数量
        if len(recent) > max_recent:
            recent = recent[:max_recent]

        self.set('ui.recent_folders', recent, save=True)


# 全局配置实例
config = ConfigManager()


def get_default_processing_settings() -> Dict[str, Any]:
    """获取默认图片处理设置"""
    return {
        'format': config.get('image_processing.default_format'),
        'quality': config.get('image_processing.default_quality'),
        'resize': {
            'width': config.get('image_processing.resize_options.default_width'),
            'height': config.get('image_processing.resize_options.default_height'),
            'scale': config.get('image_processing.resize_options.default_scale')
        },
        'watermark': config.get('image_processing.watermark'),
        'rotation': config.get('image_processing.rotation.default_degrees')
    }
"""
批量图片处理器包初始化文件

导出主要类和功能：
- BatchImageProcessor: 核心图片处理类
- ImageProcessorApp: 主GUI应用类 (原BatchImageProcessorGUI)
- ImageProcessorError: 异常基类
"""

from typing import Any, Optional, Dict, List, Tuple  # 确保类型注解支持

# 核心功能导出
from .core import BatchImageProcessor
from .gui import ImageProcessorGUI  # 使用实际存在的类名
from .exceptions import ImageProcessorError

# 保持向后兼容的别名
BatchImageProcessorGUI = ImageProcessorGUI  # 兼容旧代码的别名

# 公开API
__all__ = [
    'BatchImageProcessor',
    'ImageProcessorGUI',  # 推荐使用这个名称
    'BatchImageProcessorGUI',  # 兼容旧导入
    'ImageProcessorError'
]

# 包版本信息
__version__ = "1.0.0"
__author__ = "Your Name"
__license__ = "MIT"

def _init_package():
    """包初始化时的操作"""
    import os
    import sys
    # 初始化代码（如有需要）
    pass

# 执行初始化
_init_package()
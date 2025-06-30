"""
实用工具模块 - 提供图片处理相关的辅助功能

包含功能：
1. 文件系统操作
2. 图片处理辅助
3. 类型转换与验证
4. 系统兼容性处理
5. 其他实用工具
"""

import os
import sys
import platform
import hashlib
import logging
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any, Union
from PIL import Image, ImageOps, ImageFilter
import numpy as np

# 日志配置
logger = logging.getLogger(__name__)

# 全局常量
SUPPORTED_FORMATS = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff')
MAX_IMAGE_SIZE = 50 * 1024 * 1024  # 50MB


class FileUtils:
    """文件系统操作工具类"""

    @staticmethod
    def safe_join(base_path: str, *paths: str) -> str:
        """
        安全的路径连接，防止目录遍历攻击

        :param base_path: 基础路径
        :param paths: 要连接的路径部分
        :return: 合并后的绝对路径
        :raises ValueError: 如果尝试访问基础路径之外的文件
        """
        base_path = os.path.abspath(base_path)
        full_path = os.path.abspath(os.path.join(base_path, *paths))

        if not full_path.startswith(base_path):
            raise ValueError(f"尝试访问受限路径: {full_path}")

        return full_path

    @staticmethod
    def ensure_dir(path: str) -> str:
        """
        确保目录存在，如果不存在则创建

        :param path: 目录路径
        :return: 创建的目录路径
        """
        os.makedirs(path, exist_ok=True)
        return path

    @staticmethod
    def get_file_hash(file_path: str, algorithm: str = 'md5') -> str:
        """
        计算文件哈希值

        :param file_path: 文件路径
        :param algorithm: 哈希算法 (md5/sha1/sha256)
        :return: 哈希值字符串
        """
        hash_func = getattr(hashlib, algorithm)()

        with open(file_path, 'rb') as f:
            while chunk := f.read(8192):
                hash_func.update(chunk)

        return hash_func.hexdigest()

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        清理文件名，移除非法字符

        :param filename: 原始文件名
        :return: 安全的文件名
        """
        # 替换Windows和Linux/Unix中的非法字符
        if platform.system() == 'Windows':
            illegal_chars = r'<>:"/\|?*'
        else:
            illegal_chars = r'/'

        for char in illegal_chars:
            filename = filename.replace(char, '_')

        return filename

    @staticmethod
    def is_safe_image(file_path: str) -> bool:
        """
        检查图片文件是否安全可处理

        :param file_path: 文件路径
        :return: 是否安全
        """
        try:
            # 检查文件大小
            if os.path.getsize(file_path) > MAX_IMAGE_SIZE:
                logger.warning(f"图片过大: {file_path}")
                return False

            # 检查文件扩展名
            ext = os.path.splitext(file_path)[1].lower()
            if ext not in SUPPORTED_FORMATS:
                logger.warning(f"不支持的格式: {file_path}")
                return False

            # 简单验证图片内容
            with Image.open(file_path) as img:
                img.verify()

            return True

        except Exception as e:
            logger.warning(f"不安全图片检测失败 {file_path}: {str(e)}")
            return False


class ImageUtils:
    """图片处理工具类"""

    @staticmethod
    def auto_contrast(image: Image.Image, cutoff: int = 2) -> Image.Image:
        """
        自动对比度调整

        :param image: PIL图片对象
        :param cutoff: 裁剪百分比 (0-100)
        :return: 调整后的图片
        """
        return ImageOps.autocontrast(image, cutoff)

    @staticmethod
    def remove_exif(image: Image.Image) -> Image.Image:
        """
        移除图片的EXIF数据

        :param image: PIL图片对象
        :return: 无EXIF数据的图片
        """
        # 创建一个新图片，不复制EXIF数据
        data = list(image.getdata())
        new_image = Image.new(image.mode, image.size)
        new_image.putdata(data)
        return new_image

    @staticmethod
    def calculate_thumbnail_size(
            original_size: Tuple[int, int],
            max_size: Tuple[int, int],
            keep_aspect: bool = True
    ) -> Tuple[int, int]:
        """
        计算缩略图尺寸

        :param original_size: 原始尺寸 (width, height)
        :param max_size: 最大尺寸 (max_width, max_height)
        :param keep_aspect: 是否保持宽高比
        :return: 计算后的尺寸 (width, height)
        """
        orig_width, orig_height = original_size
        max_width, max_height = max_size

        if keep_aspect:
            ratio = min(max_width / orig_width, max_height / orig_height)
            new_width = int(orig_width * ratio)
            new_height = int(orig_height * ratio)
            return (new_width, new_height)
        else:
            return (min(orig_width, max_width), min(orig_height, max_height))

    @staticmethod
    def apply_blur(image: Image.Image, radius: int = 2) -> Image.Image:
        """
        应用高斯模糊

        :param image: PIL图片对象
        :param radius: 模糊半径
        :return: 模糊后的图片
        """
        return image.filter(ImageFilter.GaussianBlur(radius))

    @staticmethod
    def detect_edges(image: Image.Image) -> Image.Image:
        """
        边缘检测

        :param image: PIL图片对象
        :return: 边缘检测后的图片
        """
        return image.filter(ImageFilter.FIND_EDGES)

    @staticmethod
    def convert_to_grayscale(image: Image.Image) -> Image.Image:
        """
        转换为灰度图

        :param image: PIL图片对象
        :return: 灰度图片
        """
        return ImageOps.grayscale(image)

    @staticmethod
    def pad_image(
            image: Image.Image,
            size: Tuple[int, int],
            color: Tuple[int, int, int] = (255, 255, 255)
    ) -> Image.Image:
        """
        填充图片到指定尺寸

        :param image: PIL图片对象
        :param size: 目标尺寸 (width, height)
        :param color: 填充颜色 (R, G, B)
        :return: 填充后的图片
        """
        return ImageOps.pad(image, size, color=color, centering=(0.5, 0.5))

    @staticmethod
    def get_dominant_color(image: Image.Image, sample_size: int = 100) -> Tuple[int, int, int]:
        """
        获取图片主色调

        :param image: PIL图片对象
        :param sample_size: 采样大小
        :return: RGB主色调
        """
        # 缩小图片加速处理
        small_image = image.resize((sample_size, sample_size))

        # 转换为numpy数组
        arr = np.array(small_image)

        # 计算颜色直方图
        if arr.ndim == 3:  # 彩色图片
            pixels = arr.reshape(-1, arr.shape[-1])
            # 移除透明通道(如果有)
            if pixels.shape[1] == 4:
                pixels = pixels[pixels[:, 3] > 0][:, :3]
            # 计算最常见的颜色
            colors, counts = np.unique(pixels, axis=0, return_counts=True)
            dominant = colors[counts.argmax()]
            return tuple(dominant[:3])  # 只返回RGB
        else:  # 灰度图片
            return (arr.mean(),) * 3


class ValidationUtils:
    """验证工具类"""

    @staticmethod
    def validate_image_path(path: str) -> bool:
        """
        验证图片路径是否有效

        :param path: 图片路径
        :return: 是否有效
        """
        if not os.path.exists(path):
            return False
        if not os.path.isfile(path):
            return False
        return path.lower().endswith(SUPPORTED_FORMATS)

    @staticmethod
    def validate_dimension(value: Any, max_value: int = 10000) -> int:
        """
        验证图片尺寸值是否有效

        :param value: 输入值
        :param max_value: 最大值限制
        :return: 验证后的整数值
        :raises ValueError: 如果值无效
        """
        try:
            num = int(value)
            if 1 <= num <= max_value:
                return num
            raise ValueError(f"值必须在1-{max_value}之间")
        except (TypeError, ValueError):
            raise ValueError("无效的尺寸值")

    @staticmethod
    def validate_quality(value: Any) -> int:
        """
        验证图片质量值是否有效

        :param value: 输入值
        :return: 验证后的质量值(0-100)
        :raises ValueError: 如果值无效
        """
        try:
            num = int(value)
            if 0 <= num <= 100:
                return num
            raise ValueError("质量值必须在0-100之间")
        except (TypeError, ValueError):
            raise ValueError("无效的质量值")

    @staticmethod
    def validate_rotation(value: Any) -> int:
        """
        验证旋转角度是否有效

        :param value: 输入值
        :return: 验证后的角度值(0-360)
        :raises ValueError: 如果值无效
        """
        try:
            num = int(value)
            if 0 <= num <= 360:
                return num
            raise ValueError("角度必须在0-360之间")
        except (TypeError, ValueError):
            raise ValueError("无效的角度值")


class SystemUtils:
    """系统相关工具类"""

    @staticmethod
    def get_platform() -> str:
        """
        获取当前操作系统平台

        :return: 'windows', 'linux', 'mac' 或 'unknown'
        """
        system = platform.system().lower()
        if system == 'windows':
            return 'windows'
        elif system == 'linux':
            return 'linux'
        elif system == 'darwin':
            return 'mac'
        return 'unknown'

    @staticmethod
    def get_default_font() -> Optional[str]:
        """
        获取系统默认字体路径

        :return: 字体路径或None
        """
        platform = SystemUtils.get_platform()

        if platform == 'windows':
            fonts_dir = os.path.join(os.environ['WINDIR'], 'Fonts')
            possible_fonts = ['arial.ttf', 'msyh.ttc', 'simsun.ttc']
        elif platform == 'mac':
            fonts_dir = '/System/Library/Fonts'
            possible_fonts = ['Arial.ttf', 'PingFang.ttc', 'Helvetica.ttc']
        elif platform == 'linux':
            fonts_dir = '/usr/share/fonts/truetype'
            possible_fonts = ['arial.ttf', 'DejaVuSans.ttf', 'ubuntu.ttf']
        else:
            return None

        for font in possible_fonts:
            font_path = os.path.join(fonts_dir, font)
            if os.path.exists(font_path):
                return font_path

        return None

    @staticmethod
    def is_admin() -> bool:
        """
        检查当前是否以管理员/root权限运行

        :return: 是否有管理员权限
        """
        try:
            if os.name == 'nt':  # Windows
                import ctypes
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            else:  # Unix-like
                return os.getuid() == 0
        except:
            return False


class FormatConverter:
    """图片格式转换工具类"""

    @staticmethod
    def convert_format(
            image: Image.Image,
            target_format: str,
            bg_color: Tuple[int, int, int] = (255, 255, 255)
    ) -> Image.Image:
        """
        转换图片格式

        :param image: PIL图片对象
        :param target_format: 目标格式 ('JPEG', 'PNG', etc.)
        :param bg_color: 转换为不支持透明格式时的背景色
        :return: 转换后的图片
        """
        if target_format.upper() == 'JPEG' and image.mode in ('RGBA', 'LA'):
            # 为JPEG创建白色背景
            background = Image.new('RGB', image.size, bg_color)
            background.paste(image, mask=image.split()[-1])  # 使用alpha通道作为mask
            return background
        return image


class ColorUtils:
    """颜色处理工具类"""

    @staticmethod
    def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
        """
        十六进制颜色转RGB

        :param hex_color: 十六进制颜色字符串 (#RRGGBB 或 RRGGBB)
        :return: RGB元组 (0-255, 0-255, 0-255)
        :raises ValueError: 如果颜色格式无效
        """
        hex_color = hex_color.lstrip('#')
        if len(hex_color) != 6:
            raise ValueError("颜色格式应为 #RRGGBB 或 RRGGBB")

        try:
            return (
                int(hex_color[0:2], 16),
                int(hex_color[2:4], 16),
                int(hex_color[4:6], 16)
            )
        except ValueError:
            raise ValueError("无效的十六进制颜色值")

    @staticmethod
    def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
        """
        RGB转十六进制颜色

        :param rgb: RGB元组 (0-255, 0-255, 0-255)
        :return: 十六进制颜色字符串 (#RRGGBB)
        """
        return '#{:02x}{:02x}{:02x}'.format(*rgb)

    @staticmethod
    def adjust_brightness(
            rgb: Tuple[int, int, int],
            factor: float
    ) -> Tuple[int, int, int]:
        """
        调整颜色亮度

        :param rgb: RGB元组
        :param factor: 亮度因子 (0.0-2.0, 1.0为原始亮度)
        :return: 调整后的RGB元组
        """
        return tuple(min(255, max(0, int(c * factor))) for c in rgb)


# 常用工具函数
def timeit(func):
    """计时装饰器，用于性能分析"""
    from functools import wraps
    import time

    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        logger.debug(f"{func.__name__} 耗时: {end - start:.3f}秒")
        return result

    return wrapper


def human_readable_size(size: int) -> str:
    """
    :param size: 字节大小
    :return: 格式化字符串 (如 "1.23 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} TB"


def clamp(value: Union[int, float], min_val: Union[int, float], max_val: Union[int, float]) -> Union[int, float]:
    """
    将值限制在最小和最大值之间

    :param value: 输入值
    :param min_val: 最小值
    :param max_val: 最大值
    :return: 限制后的值
    """
    return max(min_val, min(value, max_val))
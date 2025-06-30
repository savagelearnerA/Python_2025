"""
自定义异常模块 - 为图片处理器定义专用的异常体系

异常分类：
1. 基础异常
2. 输入输出异常
3. 图片处理异常
4. 配置异常
5. 操作限制异常
"""
from typing import Any, Optional, Dict, Tuple, List


class ImageProcessorError(Exception):
    """所有图片处理器异常的基类"""

    def __init__(self, message: str = "图片处理发生错误", detail: str = None):
        """
        :param message: 用户友好的错误信息
        :param detail: 技术细节，用于调试
        """
        self.message = message
        self.detail = detail
        super().__init__(f"{message} | 详细信息: {detail}" if detail else message)


# ================= 输入输出异常 =================
class IOError(ImageProcessorError):
    """基础输入输出异常"""
    pass


class InvalidInputError(IOError):
    """无效输入异常"""

    def __init__(self, input_path: str = None):
        message = "输入内容无效"
        if input_path:
            detail = f"无效的输入路径或内容: {input_path}"
        else:
            detail = "未提供有效输入"
        super().__init__(message, detail)


class UnsupportedFormatError(IOError):
    """不支持的格式异常"""

    def __init__(self, file_format: str, supported_formats: tuple):
        message = f"不支持的格式: {file_format}"
        detail = f"支持的格式包括: {', '.join(supported_formats)}"
        super().__init__(message, detail)


class OutputError(IOError):
    """输出异常"""

    def __init__(self, output_path: str, reason: str):
        message = "无法保存输出文件"
        detail = f"路径: {output_path} | 原因: {reason}"
        super().__init__(message, detail)


# ================= 图片处理异常 =================
class ProcessingError(ImageProcessorError):
    """基础图片处理异常"""
    pass


class DecodingError(ProcessingError):
    """图片解码失败"""

    def __init__(self, file_path: str):
        message = "图片解码失败"
        detail = f"文件可能已损坏或不是有效图片: {file_path}"
        super().__init__(message, detail)


class EncodingError(ProcessingError):
    """图片编码失败"""

    def __init__(self, file_path: str, format: str):
        message = f"无法将图片编码为 {format} 格式"
        detail = f"文件路径: {file_path}"
        super().__init__(message, detail)


class WatermarkError(ProcessingError):
    """水印处理异常"""

    def __init__(self, reason: str):
        message = "水印添加失败"
        detail = reason
        super().__init__(message, detail)


class TransformationError(ProcessingError):
    """图片变换异常"""

    def __init__(self, operation: str, reason: str):
        message = f"图片{operation}操作失败"
        detail = reason
        super().__init__(message, detail)


# ================= 配置异常 =================
class ConfigError(ImageProcessorError):
    """配置相关异常基类"""
    pass


class InvalidConfigError(ConfigError):
    """无效配置异常"""

    def __init__(self, key: str, value: Any, valid_range: str = None):
        message = f"无效配置值: {key}={value}"
        detail = f"有效范围: {valid_range}" if valid_range else "请检查配置参数"
        super().__init__(message, detail)


# ================= 操作限制异常 =================
class LimitExceededError(ImageProcessorError):
    """超出限制异常"""
    pass


class FileSizeLimitError(LimitExceededError):
    """文件大小超过限制"""

    def __init__(self, file_path: str, max_size: str):
        message = "文件大小超过限制"
        detail = f"文件: {file_path} | 最大允许: {max_size}"
        super().__init__(message, detail)


class DimensionLimitError(LimitExceededError):
    """图片尺寸超过限制"""

    def __init__(self, dimension: tuple, max_dimension: tuple):
        message = "图片尺寸超过限制"
        detail = f"当前尺寸: {dimension} | 最大允许: {max_dimension}"
        super().__init__(message, detail)


# ================= 工具函数 =================
def wrap_errors(func):
    """
    异常处理装饰器，将特定异常转换为自定义异常

    使用示例:
    @wrap_errors
    def process_image(...):
        ...
    """

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FileNotFoundError as e:
            raise InvalidInputError(str(e)) from e
        except PermissionError as e:
            raise IOError("没有文件访问权限", str(e)) from e
        except Image.DecompressionBombError as e:
            raise FileSizeLimitError("", "图片尺寸过大，可能存在解压炸弹") from e
        except Exception as e:
            raise ImageProcessorError("未知错误发生", str(e)) from e

    return wrapper
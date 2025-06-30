"""
核心图片处理模块 - 实现批量图片处理的核心功能

主要功能：
- 批量图片格式转换
- 尺寸调整与裁剪
- 质量压缩
- 水印添加
- 图片旋转与翻转
"""

import os
import glob
from typing import Optional, Dict, Any, List, Tuple
from PIL import Image, ImageDraw, ImageFont, ImageOps
import logging
from pathlib import Path

# 日志配置
logger = logging.getLogger(__name__)


class ImageProcessingError(Exception):
    """图片处理异常基类"""
    pass


class UnsupportedFormatError(ImageProcessingError):
    """不支持的图片格式异常"""
    pass


class BatchImageProcessor:
    """批量图片处理器核心类"""

    # 支持的图片格式
    SUPPORTED_FORMATS = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff')

    # 水印默认设置
    DEFAULT_WATERMARK = {
        'text': '默认水印',
        'font_size': 30,
        'opacity': 0.7,
        'color': (255, 255, 255),
        'position': 'bottom-right',
        'margin': 10
    }

    def __init__(self, input_folder: str, output_folder: str):
        """
        初始化图片处理器

        :param input_folder: 输入图片目录路径
        :param output_folder: 输出目录路径
        """
        self.input_folder = input_folder
        self.output_folder = output_folder
        self._ensure_output_folder()

        # 初始化字体（尝试加载系统字体）
        try:
            self.default_font = ImageFont.truetype("arial.ttf", size=20)
        except:
            self.default_font = ImageFont.load_default()
            logger.warning("无法加载系统字体，使用默认字体")

    def _ensure_output_folder(self) -> None:
        """确保输出目录存在"""
        os.makedirs(self.output_folder, exist_ok=True)

    def _is_supported_format(self, filename: str) -> bool:
        """检查文件是否为支持的图片格式"""
        return filename.lower().endswith(self.SUPPORTED_FORMATS)

    def process_images(
            self,
            operations: List[str],
            **kwargs
    ) -> Dict[str, List[str]]:
        """
        批量处理图片主方法

        :param operations: 要执行的操作列表，如 ['resize', 'convert']
        :param kwargs: 各操作对应的参数
        :return: 处理结果统计 {'success': [], 'failed': []}
        """
        results = {'success': [], 'failed': []}
        image_files = self._get_image_files()

        for img_path in image_files:
            try:
                filename = os.path.basename(img_path)
                logger.info(f"正在处理: {filename}")

                with Image.open(img_path) as img:
                    # 执行所有操作
                    for op in operations:
                        img = self._apply_operation(img, op, **kwargs)

                    # 保存处理后的图片
                    output_path = self._get_output_path(img_path, kwargs.get('format'))
                    save_params = self._get_save_params(kwargs)
                    img.save(output_path, **save_params)

                results['success'].append(filename)

            except Exception as e:
                logger.error(f"处理图片 {img_path} 失败: {str(e)}")
                results['failed'].append((filename, str(e)))

        return results

    def _get_image_files(self) -> List[str]:
        """获取输入目录中所有支持的图片文件"""
        all_files = glob.glob(os.path.join(self.input_folder, '*.*'))
        return [f for f in all_files if self._is_supported_format(f)]

    def _apply_operation(
            self,
            img: Image.Image,
            operation: str,
            **kwargs
    ) -> Image.Image:
        """
        应用单个图片处理操作

        :param img: PIL图片对象
        :param operation: 操作名称
        :param kwargs: 操作参数
        :return: 处理后的图片对象
        """
        try:
            if operation == 'resize':
                return self._resize_image(img, **kwargs)
            elif operation == 'convert':
                return img  # 格式转换在保存时处理
            elif operation == 'compress':
                return img  # 质量压缩在保存时处理
            elif operation == 'watermark':
                return self._add_watermark(img, **kwargs)
            elif operation == 'rotate':
                return self._rotate_image(img, **kwargs)
            elif operation == 'flip':
                return self._flip_image(img, **kwargs)
            elif operation == 'crop':
                return self._crop_image(img, **kwargs)
            else:
                raise ValueError(f"不支持的操作: {operation}")
        except Exception as e:
            logger.error(f"执行操作 {operation} 失败: {str(e)}")
            raise

    def _resize_image(
            self,
            img: Image.Image,
            width: Optional[int] = None,
            height: Optional[int] = None,
            scale: Optional[float] = None,
            **_
    ) -> Image.Image:
        """
        调整图片尺寸

        :param width: 目标宽度（像素）
        :param height: 目标高度（像素）
        :param scale: 缩放比例
        :return: 调整后的图片
        """
        if scale:
            new_width = int(img.width * scale)
            new_height = int(img.height * scale)
            return img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        if width and height:
            return img.resize((width, height), Image.Resampling.LANCZOS)

        if width:
            ratio = width / img.width
            new_height = int(img.height * ratio)
            return img.resize((width, new_height), Image.Resampling.LANCZOS)

        if height:
            ratio = height / img.height
            new_width = int(img.width * ratio)
            return img.resize((new_width, height), Image.Resampling.LANCZOS)

        return img

    def _add_watermark(
            self,
            img: Image.Image,
            text: Optional[str] = None,
            **watermark_args
    ) -> Image.Image:
        """
        添加文字水印

        :param text: 水印文字
        :param watermark_args: 水印参数（字体大小、颜色、位置等）
        :return: 添加水印后的图片
        """
        if not text:
            return img

        # 合并默认参数和用户参数
        params = {**self.DEFAULT_WATERMARK, **watermark_args}
        params['text'] = text

        # 创建水印图层
        watermark = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(watermark)

        # 尝试加载字体
        try:
            font = ImageFont.truetype("arial.ttf", size=params['font_size'])
        except:
            font = ImageFont.load_default()

        # 计算文字位置
        text_width, text_height = draw.textsize(params['text'], font=font)
        position = self._calculate_watermark_position(
            img.size,
            (text_width, text_height),
            params['position'],
            params['margin']
        )

        # 绘制水印
        draw.text(
            position,
            params['text'],
            font=font,
            fill=(*params['color'], int(255 * params['opacity'])))

        # 合并水印
        if img.mode != 'RGBA':
            img = img.convert("RGBA")

        return Image.alpha_composite(img, watermark)

    def _calculate_watermark_position(
            self,
            img_size: Tuple[int, int],
            text_size: Tuple[int, int],
            position: str,
            margin: int
    ) -> Tuple[int, int]:
        """
        计算水印位置

        :param img_size: 图片尺寸 (width, height)
        :param text_size: 文字尺寸 (width, height)
        :param position: 位置描述 ('top-left', 'center', 等)
        :param margin: 边距（像素）
        :return: (x, y) 坐标
        """
        img_width, img_height = img_size
        text_width, text_height = text_size

        positions = {
            'top-left': (margin, margin),
            'top-center': ((img_width - text_width) // 2, margin),
            'top-right': (img_width - text_width - margin, margin),
            'center-left': (margin, (img_height - text_height) // 2),
            'center': ((img_width - text_width) // 2, (img_height - text_height) // 2),
            'center-right': (img_width - text_width - margin, (img_height - text_height) // 2),
            'bottom-left': (margin, img_height - text_height - margin),
            'bottom-center': ((img_width - text_width) // 2, img_height - text_height - margin),
            'bottom-right': (img_width - text_width - margin, img_height - text_height - margin),
        }

        return positions.get(position.lower(), positions['bottom-right'])

    def _rotate_image(
            self,
            img: Image.Image,
            degrees: int = 0,
            expand: bool = True,
            **_
    ) -> Image.Image:
        """
        旋转图片

        :param degrees: 旋转角度（0-360）
        :param expand: 是否扩展画布以适应旋转后的图片
        :return: 旋转后的图片
        """
        return img.rotate(degrees, expand=expand)

    def _flip_image(
            self,
            img: Image.Image,
            mode: str = 'horizontal',
            **_
    ) -> Image.Image:
        """
        翻转图片

        :param mode: 翻转模式 ('horizontal' 或 'vertical')
        :return: 翻转后的图片
        """
        if mode == 'horizontal':
            return ImageOps.mirror(img)
        elif mode == 'vertical':
            return ImageOps.flip(img)
        else:
            raise ValueError(f"不支持的翻转模式: {mode}")

    def _crop_image(
            self,
            img: Image.Image,
            box: Optional[Tuple[int, int, int, int]] = None,
            **_
    ) -> Image.Image:
        """
        裁剪图片

        :param box: 裁剪区域 (left, upper, right, lower)
        :return: 裁剪后的图片
        """
        if box:
            return img.crop(box)
        return img

    def _get_output_path(
            self,
            input_path: str,
            target_format: Optional[str] = None
    ) -> str:
        """
        生成输出路径

        :param input_path: 输入文件路径
        :param target_format: 目标格式（如 'PNG'）
        :return: 输出文件完整路径
        """
        filename = os.path.basename(input_path)

        if target_format:
            base, _ = os.path.splitext(filename)
            filename = f"{base}.{target_format.lower()}"

        return os.path.join(self.output_folder, filename)

    def _get_save_params(
            self,
            params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        获取图片保存参数

        :param params: 处理参数
        :return: 保存参数字典
        """
        save_params = {}

        # 质量参数
        if 'quality' in params:
            save_params['quality'] = params['quality']

        # 格式特定参数
        if params.get('format') == 'PNG':
            save_params['compress_level'] = 6

        return save_params
"""
批量图片处理器GUI

"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from tkinterdnd2 import TkinterDnD, DND_FILES
from PIL import Image, ImageTk, ImageOps, ImageFont, ImageDraw
import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import threading
import queue
import time

# 初始化日志
logger = logging.getLogger(__name__)


class ImageProcessorGUI(TkinterDnD.Tk):
    """主GUI应用程序"""

    def __init__(self):
        super().__init__()
        self.title("批量图片处理器")
        self.geometry("1000x750")
        self._create_variables()
        self._setup_ui()
        self._setup_bindings()

    def _create_variables(self):
        """初始化所有状态变量"""
        # 文件夹路径
        self.input_folder = tk.StringVar()
        self.output_folder = tk.StringVar()

        # 处理参数
        self.params = {
            'format': tk.StringVar(value='JPEG'),
            'quality': tk.IntVar(value=85),
            'resize': {
                'mode': tk.StringVar(value='none'),
                'width': tk.IntVar(value=800),
                'height': tk.IntVar(value=600),
                'scale': tk.DoubleVar(value=1.0)
            },
            'watermark': {
                'text': tk.StringVar(value='Watermark'),
                'font_size': tk.IntVar(value=20),
                'opacity': tk.DoubleVar(value=0.7),
                'position': tk.StringVar(value='bottom-right')
            }
        }

        # 运行时状态
        self.processing = False
        self.preview_image = None
        self.message_queue = queue.Queue()

    def _setup_ui(self):
        """构建用户界面"""
        self._create_menu()
        self._create_main_frames()
        self._create_toolbar()
        self._create_notebook()
        self._create_statusbar()

    def _create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self)

        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="设置输入文件夹", command=self._select_input_folder)
        file_menu.add_command(label="设置输出文件夹", command=self._select_output_folder)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.quit)
        menubar.add_cascade(label="设置输入与输出文件夹", menu=file_menu)

        self.config(menu=menubar)

    def _create_main_frames(self):
        """创建主框架"""
        self.main_frame = ttk.Frame(self, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # 工具栏框架
        self.toolbar_frame = ttk.Frame(self.main_frame)
        self.toolbar_frame.pack(fill=tk.X, pady=(0, 10))

        # 笔记本框架
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # 状态栏框架
        self.status_frame = ttk.Frame(self)
        self.status_frame.pack(fill=tk.X)

    def _create_toolbar(self):
        """创建工具栏"""
        ttk.Button(self.toolbar_frame, text="打开图片",
                   command=self._open_images).pack(side=tk.LEFT, padx=2)
        ttk.Button(self.toolbar_frame, text="预览效果",
                   command=self._update_preview).pack(side=tk.LEFT, padx=2)

        ttk.Separator(self.toolbar_frame, orient=tk.VERTICAL) \
            .pack(side=tk.LEFT, padx=5, fill=tk.Y)

        self.start_btn = ttk.Button(self.toolbar_frame, text="开始处理",
                                    command=self._start_processing, style='Accent.TButton')
        self.start_btn.pack(side=tk.RIGHT, padx=2)

        self.stop_btn = ttk.Button(self.toolbar_frame, text="停止",
                                   state=tk.DISABLED, command=self._stop_processing)
        self.stop_btn.pack(side=tk.RIGHT, padx=2)

    def _create_notebook(self):
        """创建功能标签页"""
        self._create_format_tab()
        self._create_resize_tab()
        self._create_watermark_tab()
        self._create_preview_tab()
        self._create_log_tab()

    def _create_format_tab(self):
        """格式转换标签页"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="格式转换")

        ttk.Label(tab, text="输出格式:").pack(anchor=tk.W, pady=5)
        formats = ["JPEG", "PNG", "GIF", "BMP", "WEBP"]
        ttk.Combobox(tab, textvariable=self.params['format'],
                     values=formats, state="readonly").pack(fill=tk.X)

        ttk.Label(tab, text="质量 (0-100):").pack(anchor=tk.W, pady=(15, 5))
        ttk.Scale(tab, from_=1, to=100, variable=self.params['quality'],
                  orient=tk.HORIZONTAL).pack(fill=tk.X)
        ttk.Label(tab, textvariable=self.params['quality']).pack()

    def _create_resize_tab(self):
        """尺寸调整标签页"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="调整尺寸")

        # 调整模式单选按钮
        mode_frame = ttk.LabelFrame(tab, text="调整模式", padding="10")
        mode_frame.pack(fill=tk.X, pady=5)

        modes = [("不调整", "none"), ("按宽度", "width"),
                 ("按高度", "height"), ("按比例", "scale")]
        for text, mode in modes:
            ttk.Radiobutton(mode_frame, text=text,
                            variable=self.params['resize']['mode'],
                            value=mode).pack(side=tk.LEFT, padx=5)

        # 参数输入
        param_frame = ttk.Frame(tab)
        param_frame.pack(fill=tk.X, pady=5)

        ttk.Label(param_frame, text="宽度:").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(param_frame, textvariable=self.params['resize']['width'],
                  width=10).grid(row=0, column=1, sticky=tk.W)

        ttk.Label(param_frame, text="高度:").grid(row=1, column=0, sticky=tk.W)
        ttk.Entry(param_frame, textvariable=self.params['resize']['height'],
                  width=10).grid(row=1, column=1, sticky=tk.W)

        ttk.Label(param_frame, text="比例:").grid(row=2, column=0, sticky=tk.W)
        ttk.Entry(param_frame, textvariable=self.params['resize']['scale'],
                  width=10).grid(row=2, column=1, sticky=tk.W)

    def _create_watermark_tab(self):
        """水印标签页"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="添加水印")

        ttk.Label(tab, text="水印文字:").pack(anchor=tk.W, pady=5)
        ttk.Entry(tab, textvariable=self.params['watermark']['text']).pack(fill=tk.X)

        # 水印样式
        style_frame = ttk.Frame(tab)
        style_frame.pack(fill=tk.X, pady=10)

        ttk.Label(style_frame, text="字体大小:").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(style_frame, textvariable=self.params['watermark']['font_size'],
                  width=5).grid(row=0, column=1, sticky=tk.W)

        ttk.Label(style_frame, text="透明度:").grid(row=0, column=2, padx=(10, 0), sticky=tk.W)
        ttk.Scale(style_frame, from_=0.1, to=1.0,
                  variable=self.params['watermark']['opacity'],
                  orient=tk.HORIZONTAL, length=100).grid(row=0, column=3)

        # 水印位置
        ttk.Label(tab, text="位置:").pack(anchor=tk.W, pady=5)
        pos_frame = ttk.Frame(tab)
        pos_frame.pack(fill=tk.X)

        positions = [
            ("左上", "top-left"), ("中上", "top-center"), ("右上", "top-right"),
            ("左下", "bottom-left"), ("中下", "bottom-center"), ("右下", "bottom-right")
        ]

        for i, (text, pos) in enumerate(positions):
            row, col = divmod(i, 3)
            ttk.Radiobutton(pos_frame, text=text,
                            variable=self.params['watermark']['position'],
                            value=pos).grid(row=row, column=col, sticky=tk.W, padx=5, pady=2)

    def _create_preview_tab(self):
        """预览标签页"""
        self.preview_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.preview_tab, text="预览")

        self.preview_canvas = tk.Canvas(self.preview_tab, bg='#f0f0f0')
        self.preview_canvas.pack(fill=tk.BOTH, expand=True)

        self.no_preview_label = ttk.Label(
            self.preview_canvas,
            text="请选择图片并点击【预览效果】",
            foreground='gray'
        )
        self.no_preview_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

    def _create_log_tab(self):
        """日志标签页"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="日志")

        self.log_text = scrolledtext.ScrolledText(
            tab, wrap=tk.WORD, font=('Consolas', 10), padx=10, pady=10
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.config(state=tk.DISABLED)

    def _create_statusbar(self):
        """创建状态栏"""
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            self.status_frame, variable=self.progress_var, maximum=100
        )
        self.progress_bar.pack(fill=tk.X, expand=True, side=tk.LEFT)

        self.status_var = tk.StringVar(value="就绪")
        ttk.Label(self.status_frame, textvariable=self.status_var).pack(side=tk.LEFT, padx=5)

    def _setup_bindings(self):
        """设置事件绑定"""
        self.drop_target_register(DND_FILES)
        self.dnd_bind('<<Drop>>', self._handle_drop)

    def _select_input_folder(self):
        """选择输入文件夹"""
        folder = filedialog.askdirectory(title="选择输入文件夹")
        if folder:
            self.input_folder.set(folder)

    def _select_output_folder(self):
        """选择输出文件夹"""
        folder = filedialog.askdirectory(title="选择输出文件夹")
        if folder:
            self.output_folder.set(folder)

    def _handle_drop(self, event):
        """处理文件拖放"""
        files = self.tk.splitlist(event.data)
        if files:
            first_file = files[0]
            if os.path.isdir(first_file):
                self.input_folder.set(first_file)
            elif os.path.isfile(first_file):
                folder = os.path.dirname(first_file)
                self.input_folder.set(folder)
                self._display_preview(first_file)

    def _open_images(self):
        """打开图片文件"""
        files = filedialog.askopenfilenames(
            title="选择图片文件",
            filetypes=[("图片文件", "*.jpg *.jpeg *.png *.gif *.bmp *.webp")]
        )
        if files:
            self._display_preview(files[0])

    def _display_preview(self, image_path):
        """显示预览图片"""
        try:
            img = Image.open(image_path)
            self._apply_effects(img)

            # 调整尺寸以适应画布
            canvas_width = self.preview_canvas.winfo_width()
            canvas_height = self.preview_canvas.winfo_height()

            if canvas_width > 1 and canvas_height > 1:
                ratio = min(
                    (canvas_width - 20) / img.width,
                    (canvas_height - 20) / img.height
                )
                new_size = (int(img.width * ratio), int(img.height * ratio))
                img = img.resize(new_size, Image.Resampling.LANCZOS)

            # 显示图片
            self.preview_image = ImageTk.PhotoImage(img)
            self.preview_canvas.delete("all")
            self.no_preview_label.place_forget()
            self.preview_canvas.create_image(
                self.preview_canvas.winfo_width() / 2,
                self.preview_canvas.winfo_height() / 2,
                anchor=tk.CENTER,
                image=self.preview_image
            )

        except Exception as e:
            self._log_message(f"预览失败: {str(e)}", "error")
            messagebox.showerror("错误", f"无法加载图片:\n{str(e)}")

    def _apply_effects(self, img):
        """应用图片效果"""
        params = self._get_current_params()

        # 调整尺寸
        if params['resize']['mode'] != 'none':
            if params['resize']['mode'] == 'width':
                ratio = params['resize']['width'] / img.width
                new_height = int(img.height * ratio)
                img = img.resize((params['resize']['width'], new_height),
                                 Image.Resampling.LANCZOS)
            elif params['resize']['mode'] == 'height':
                ratio = params['resize']['height'] / img.height
                new_width = int(img.width * ratio)
                img = img.resize((new_width, params['resize']['height']),
                                 Image.Resampling.LANCZOS)
            elif params['resize']['mode'] == 'scale':
                new_width = int(img.width * params['resize']['scale'])
                new_height = int(img.height * params['resize']['scale'])
                img = img.resize((new_width, new_height),
                                 Image.Resampling.LANCZOS)

        # 添加水印
        if params['watermark']['text']:
            self._add_watermark(img, params['watermark'])

        return img

    def _add_watermark(self, img, watermark_params):
        """添加水印到图片"""
        watermark = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(watermark)

        try:
            font = ImageFont.truetype("arial.ttf", watermark_params['font_size'])
        except:
            font = ImageFont.load_default()

        text = watermark_params['text']

        # 替换废弃的textsize方法
        if hasattr(draw, 'textbbox'):  # Pillow 9.2.0+
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        elif hasattr(draw, 'textsize'):  # 旧版本
            text_width, text_height = draw.textsize(text, font=font)
        else:  # 兼容处理
            text_width = len(text) * watermark_params['font_size']
            text_height = watermark_params['font_size']

        # 计算位置
        margin = 10
        positions = {
            'top-left': (margin, margin),
            'top-center': ((img.width - text_width) // 2, margin),
            'top-right': (img.width - text_width - margin, margin),
            'bottom-left': (margin, img.height - text_height - margin),
            'bottom-center': ((img.width - text_width) // 2, img.height - text_height - margin),
            'bottom-right': (img.width - text_width - margin, img.height - text_height - margin),
        }

        pos = positions.get(watermark_params['position'], positions['bottom-right'])

        # 绘制水印
        draw.text(
            pos,
            text,
            font=font,
            fill=(255, 255, 255, int(255 * watermark_params['opacity']))
        )

        if img.mode != 'RGBA':
            img = img.convert("RGBA")

        return Image.alpha_composite(img, watermark)


    def _update_preview(self):
        """更新预览"""
        if not self.input_folder.get():
            messagebox.showwarning("提示", "请先选择输入文件夹")
            return

        # 获取文件夹中的第一个图片
        image_files = [f for f in os.listdir(self.input_folder.get())
                       if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'))]

        if image_files:
            self._display_preview(os.path.join(self.input_folder.get(), image_files[0]))
        else:
            messagebox.showwarning("提示", "文件夹中没有图片文件")

    def _get_current_params(self):
        """获取当前参数"""
        return {
            'format': self.params['format'].get(),
            'quality': self.params['quality'].get(),
            'resize': {
                'mode': self.params['resize']['mode'].get(),
                'width': self.params['resize']['width'].get(),
                'height': self.params['resize']['height'].get(),
                'scale': self.params['resize']['scale'].get()
            },
            'watermark': {
                'text': self.params['watermark']['text'].get(),
                'font_size': self.params['watermark']['font_size'].get(),
                'opacity': self.params['watermark']['opacity'].get(),
                'position': self.params['watermark']['position'].get()
            }
        }

    def _start_processing(self):
        """开始处理图片"""
        if self.processing:
            return

        if not self.input_folder.get() or not self.output_folder.get():
            messagebox.showerror("错误", "请选择输入和输出文件夹")
            return

        if self.input_folder.get() == self.output_folder.get():
            messagebox.showerror("错误", "输入和输出文件夹不能相同")
            return

        self.processing = True
        self._update_ui_state()

        # 在后台线程中处理
        thread = threading.Thread(
            target=self._process_images,
            daemon=True
        )
        thread.start()

    def _process_images(self):
        """处理图片的线程方法"""
        try:
            input_folder = self.input_folder.get()
            output_folder = self.output_folder.get()
            params = self._get_current_params()

            # 获取所有图片文件
            image_files = [f for f in os.listdir(input_folder)
                           if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'))]
            total = len(image_files)

            if total == 0:
                self.message_queue.put(('error', "没有找到可处理的图片文件"))
                return

            for i, filename in enumerate(image_files, 1):
                if not self.processing:
                    break

                try:
                    input_path = os.path.join(input_folder, filename)
                    output_path = os.path.join(output_folder, filename)

                    # 更新进度
                    self.message_queue.put(('progress', (i, total, filename)))

                    # 处理图片
                    with Image.open(input_path) as img:
                        img = self._apply_effects(img)
                        img.save(output_path, quality=params['quality'])

                except Exception as e:
                    self.message_queue.put(('error', f"处理 {filename} 失败: {str(e)}"))

            if self.processing:
                self.message_queue.put(('success', f"处理完成! 共处理 {i}/{total} 张图片"))

        except Exception as e:
            self.message_queue.put(('error', f"处理过程中发生错误: {str(e)}"))

        finally:
            self.message_queue.put(('done', None))

    def _stop_processing(self):
        """停止处理"""
        self.processing = False
        self.status_var.set("正在停止...")

    def _update_ui_state(self):
        """更新UI状态"""
        if self.processing:
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.status_var.set("处理中...")
        else:
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.status_var.set("就绪")

    def _process_messages(self):
        """处理消息队列中的消息"""
        try:
            while True:
                msg_type, msg_data = self.message_queue.get_nowait()

                if msg_type == 'progress':
                    current, total, filename = msg_data
                    percent = int((current / total) * 100)
                    self.progress_var.set(percent)
                    self.status_var.set(f"处理中: {current}/{total} ({filename})")

                elif msg_type == 'success':
                    self._log_message(msg_data, "info")
                    messagebox.showinfo("完成", msg_data)
                    self.processing = False
                    self._update_ui_state()
                    self.progress_var.set(100)

                elif msg_type == 'error':
                    self._log_message(msg_data, "error")

                elif msg_type == 'done':
                    self.processing = False
                    self._update_ui_state()
                    self.progress_var.set(0)

        except queue.Empty:
            pass

        self.after(100, self._process_messages)

    def _log_message(self, message, level="info"):
        """记录日志消息"""
        self.log_text.config(state=tk.NORMAL)

        # 添加时间戳
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] ")

        # 根据级别设置颜色
        if level == "error":
            self.log_text.insert(tk.END, "[错误] ", "error")
            self.log_text.tag_config("error", foreground="red")
        elif level == "warning":
            self.log_text.insert(tk.END, "[警告] ", "warning")
            self.log_text.tag_config("warning", foreground="orange")
        else:
            self.log_text.insert(tk.END, "[信息] ", "info")
            self.log_text.tag_config("info", foreground="blue")

        self.log_text.insert(tk.END, message + "\n")
        self.log_text.config(state=tk.DISABLED)
        self.log_text.see(tk.END)  # 自动滚动到底部

    def run(self):
        """运行主循环"""
        self._process_messages()  # 启动消息处理
        self.mainloop()


def main():
    """应用程序入口"""
    app = ImageProcessorGUI()
    app.run()


if __name__ == "__main__":
    main()
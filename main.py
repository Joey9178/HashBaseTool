import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import hashlib
import base64
import os
import codecs
import binascii

# 常见编码列表
COMMON_ENCODINGS = ['utf-8', 'gbk', 'gb2312', 'big5', 'ascii', 'latin-1', 'utf-16']
# 支持的哈希算法
HASH_ALGORITHMS = ['md5', 'sha1', 'sha256', 'sha384', 'sha512']


class HashBase64App:
    def __init__(self, root):
        self.root = root
        self.root.title("哈希值 & Base64 转换工具")
        self.root.geometry("650x550")
        self.root.minsize(550, 480)

        # 尝试应用 Vista 主题（Windows 原生风格）
        self.style = ttk.Style()
        try:
            self.style.theme_use('vista')
        except tk.TclError:
            try:
                self.style.theme_use('xpnative')
            except tk.TclError:
                pass  # 使用默认主题

        # 核心控制变量
        self.func_var = tk.StringVar(value='hash')          # 'hash' 或 'base64'
        self.mode_var = tk.StringVar(value='text')          # 'text' 或 'file'
        self.encoding_var = tk.StringVar(value='utf-8')
        self.algo_var = tk.StringVar(value='md5')
        self.b64_direction_var = tk.StringVar(value='encode')  # 'encode' 或 'decode'
        self.file_path_var = tk.StringVar()

        # 存储解码后的二进制数据（用于保存文件）
        self.decoded_bytes = None

        self.create_widgets()
        self.update_options_visibility()

        # 绑定追踪
        self.func_var.trace('w', self.on_func_change)
        self.mode_var.trace('w', self.on_mode_change)

    def create_widgets(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # ---- 1. 功能选择（哈希 / Base64） ----
        func_frame = ttk.LabelFrame(main_frame, text="选择功能", padding="5")
        func_frame.grid(row=0, column=0, columnspan=2, sticky='ew', pady=(0, 10))
        ttk.Radiobutton(func_frame, text="哈希值计算", variable=self.func_var, value='hash').pack(side='left', padx=5)
        ttk.Radiobutton(func_frame, text="Base64 转换", variable=self.func_var, value='base64').pack(side='left', padx=15)

        # ---- 2. 输入模式（文本 / 文件） ----
        mode_frame = ttk.LabelFrame(main_frame, text="输入模式", padding="5")
        mode_frame.grid(row=1, column=0, columnspan=2, sticky='ew', pady=(0, 10))
        ttk.Radiobutton(mode_frame, text="文本", variable=self.mode_var, value='text').pack(side='left', padx=5)
        ttk.Radiobutton(mode_frame, text="文件", variable=self.mode_var, value='file').pack(side='left', padx=15)

        # ---- 3. 选项区域（动态切换） ----
        self.options_container = ttk.Frame(main_frame)
        self.options_container.grid(row=2, column=0, columnspan=2, sticky='ew', pady=(0, 10))

        # 3-A: 哈希选项
        self.hash_opts = ttk.Frame(self.options_container)
        ttk.Label(self.hash_opts, text="文本编码:").pack(side='left', padx=(0, 5))
        self.enc_combo = ttk.Combobox(self.hash_opts, textvariable=self.encoding_var,
                                      values=COMMON_ENCODINGS, state='readonly', width=12)
        self.enc_combo.pack(side='left', padx=(0, 15))
        ttk.Label(self.hash_opts, text="哈希算法:").pack(side='left', padx=(0, 5))
        self.algo_combo = ttk.Combobox(self.hash_opts, textvariable=self.algo_var,
                                       values=HASH_ALGORITHMS, state='readonly', width=12)
        self.algo_combo.pack(side='left')

        # 3-B: Base64 选项
        self.b64_opts = ttk.Frame(self.options_container)
        ttk.Label(self.b64_opts, text="操作:").pack(side='left', padx=(0, 5))
        ttk.Radiobutton(self.b64_opts, text="编码", variable=self.b64_direction_var, value='encode').pack(side='left', padx=2)
        ttk.Radiobutton(self.b64_opts, text="解码", variable=self.b64_direction_var, value='decode').pack(side='left', padx=10)
        # 保存解码结果按钮（仅在 Base64 解码且结果为二进制时启用）
        self.save_b64_btn = ttk.Button(self.b64_opts, text="保存解码文件", command=self.save_decoded_file, state='disabled')
        self.save_b64_btn.pack(side='left', padx=10)

        # ---- 4. 输入区域（文本 / 文件） ----
        self.input_container = ttk.Frame(main_frame)
        self.input_container.grid(row=3, column=0, columnspan=2, sticky='nsew', pady=(0, 10))

        # 文本输入
        self.text_frame = ttk.Frame(self.input_container)
        self.text_entry = tk.Text(self.text_frame, height=6, wrap='none', font=('Consolas', 10))
        scrollbar_text = ttk.Scrollbar(self.text_frame, orient='vertical', command=self.text_entry.yview)
        self.text_entry.configure(yscrollcommand=scrollbar_text.set)
        self.text_entry.pack(side='left', fill='both', expand=True)
        scrollbar_text.pack(side='right', fill='y')

        # 文件输入
        self.file_frame = ttk.Frame(self.input_container)
        file_path_frame = ttk.Frame(self.file_frame)
        file_path_frame.pack(fill='x', pady=5)
        self.file_entry = ttk.Entry(file_path_frame, textvariable=self.file_path_var)
        self.file_entry.pack(side='left', fill='x', expand=True, padx=(0, 5))
        browse_btn = ttk.Button(file_path_frame, text="浏览...", command=self.browse_file)
        browse_btn.pack(side='right')
        self.file_info_label = ttk.Label(self.file_frame, text="未选择文件")
        self.file_info_label.pack(anchor='w', pady=(5, 0))

        # ---- 5. 操作按钮 ----
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=(0, 10))
        self.action_btn = ttk.Button(btn_frame, text="执行转换", command=self.execute_action)
        self.action_btn.pack(side='left', padx=5)
        clear_btn = ttk.Button(btn_frame, text="清空所有", command=self.clear_all)
        clear_btn.pack(side='left', padx=5)

        # ---- 6. 结果展示 ----
        result_frame = ttk.LabelFrame(main_frame, text="结果输出", padding="5")
        result_frame.grid(row=5, column=0, columnspan=2, sticky='nsew', pady=(0, 10))

        self.result_text = tk.Text(result_frame, height=6, state='disabled', wrap='none',
                                   font=('Consolas', 10))
        scrollbar_result = ttk.Scrollbar(result_frame, orient='vertical', command=self.result_text.yview)
        self.result_text.configure(yscrollcommand=scrollbar_result.set)
        self.result_text.pack(side='left', fill='both', expand=True)
        scrollbar_result.pack(side='right', fill='y')

        # ---- 7. 底部操作栏 ----
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.grid(row=6, column=0, columnspan=2, sticky='ew')
        copy_btn = ttk.Button(bottom_frame, text="复制结果到剪贴板", command=self.copy_result)
        copy_btn.pack(side='left', padx=5)
        self.status_label = ttk.Label(bottom_frame, text="就绪")
        self.status_label.pack(side='right', padx=5)

        # 网格权重配置
        main_frame.grid_rowconfigure(3, weight=1)
        main_frame.grid_rowconfigure(5, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)
        self.input_container.grid_rowconfigure(0, weight=1)
        self.input_container.grid_columnconfigure(0, weight=1)

    # ---------- 界面切换 ----------
    def on_func_change(self, *args):
        self.update_options_visibility()
        self.clear_all()

    def update_options_visibility(self):
        if self.func_var.get() == 'hash':
            self.hash_opts.grid(row=0, column=0, sticky='w')
            self.b64_opts.grid_remove()
            self.enc_combo.config(state='readonly' if self.mode_var.get() == 'text' else 'disabled')
        else:  # base64
            self.hash_opts.grid_remove()
            self.b64_opts.grid(row=0, column=0, sticky='w')
            self.save_b64_btn.config(state='disabled')
            self.decoded_bytes = None

    def on_mode_change(self, *args):
        if self.mode_var.get() == 'text':
            self.text_frame.grid()
            self.file_frame.grid_remove()
            if self.func_var.get() == 'hash':
                self.enc_combo.config(state='readonly')
        else:
            self.text_frame.grid_remove()
            self.file_frame.grid()
            self.update_file_info()
            if self.func_var.get() == 'hash':
                self.enc_combo.config(state='disabled')

    # ---------- 文件操作 ----------
    def browse_file(self):
        file_path = filedialog.askopenfilename(title="选择文件")
        if file_path:
            self.file_path_var.set(file_path)
            self.update_file_info()

    def update_file_info(self):
        path = self.file_path_var.get().strip()
        if path and os.path.isfile(path):
            size = os.path.getsize(path)
            self.file_info_label.config(text=f"已选: {os.path.basename(path)} ({self.format_size(size)})")
        else:
            self.file_info_label.config(text="未选择文件或文件不存在")

    @staticmethod
    def format_size(size):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    # ---------- 核心执行 ----------
    def execute_action(self):
        self.action_btn.config(state='disabled')
        self.status_label.config(text="执行中...")
        self.root.update()

        try:
            if self.func_var.get() == 'hash':
                self.do_hash()
            else:
                self.do_base64()
        except Exception as e:
            messagebox.showerror("错误", str(e))
            self.status_label.config(text="发生错误")
        finally:
            self.action_btn.config(state='normal')
            self.root.update()

    # ---------- 哈希功能 ----------
    def do_hash(self):
        algo_name = self.algo_var.get().lower()
        try:
            hash_func = getattr(hashlib, algo_name)()
        except AttributeError:
            raise ValueError(f"不支持的哈希算法: {algo_name}")

        if self.mode_var.get() == 'text':
            text = self.text_entry.get("1.0", tk.END).rstrip('\n')
            if not text:
                raise ValueError("请输入文本内容")
            encoding = self.encoding_var.get()
            try:
                data = text.encode(encoding)
            except UnicodeEncodeError as e:
                raise ValueError(f"编码错误: {e}")
            hash_func.update(data)
        else:
            file_path = self.file_path_var.get().strip()
            if not file_path or not os.path.isfile(file_path):
                raise ValueError("请选择有效的文件")
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(8192)
                    if not chunk:
                        break
                    hash_func.update(chunk)

        result = hash_func.hexdigest()
        self.show_result(result)
        self.status_label.config(text="哈希计算完成")

    # ---------- Base64 功能 ----------
    def do_base64(self):
        direction = self.b64_direction_var.get()
        mode = self.mode_var.get()
        self.decoded_bytes = None
        self.save_b64_btn.config(state='disabled')

        if mode == 'text':
            input_str = self.text_entry.get("1.0", tk.END).rstrip('\n')
            if not input_str:
                raise ValueError("请输入文本内容")

            if direction == 'encode':
                # 文本 -> Base64
                encoded = base64.b64encode(input_str.encode('utf-8')).decode('ascii')
                self.show_result(encoded)
                self.status_label.config(text="Base64 编码完成")
            else:
                # Base64 -> 文本/二进制
                try:
                    raw = base64.b64decode(input_str.encode('ascii'))
                except binascii.Error as e:
                    raise ValueError(f"无效的 Base64 格式: {e}")
                self.handle_decoded_data(raw)

        else:  # file
            file_path = self.file_path_var.get().strip()
            if not file_path or not os.path.isfile(file_path):
                raise ValueError("请选择有效的文件")

            file_size = os.path.getsize(file_path)
            # 大文件警告 (超过 50MB)
            if file_size > 50 * 1024 * 1024:
                if not messagebox.askyesno("内存警告",
                                           f"文件大小 {self.format_size(file_size)}，Base64 处理将占用大量内存，\n可能导致界面卡顿。是否继续？"):
                    return

            if direction == 'encode':
                # 文件 -> Base64 字符串
                with open(file_path, 'rb') as f:
                    data = f.read()
                encoded = base64.b64encode(data).decode('ascii')
                self.show_result(encoded)
                self.status_label.config(text="Base64 编码完成")
            else:
                # Base64 文件 -> 解码为二进制
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    b64_content = f.read()
                try:
                    raw = base64.b64decode(b64_content.strip())
                except binascii.Error as e:
                    raise ValueError(f"文件内容不是有效的 Base64 格式: {e}")
                self.handle_decoded_data(raw)

    def handle_decoded_data(self, raw_bytes: bytes):
        """处理解码后的字节数据，尝试显示文本或提供保存选项"""
        self.decoded_bytes = raw_bytes
        # 尝试解码为 UTF-8 文本显示
        try:
            text_content = raw_bytes.decode('utf-8')
            self.show_result(text_content)
            self.status_label.config(text="Base64 解码完成 (文本)")
        except UnicodeDecodeError:
            # 二进制数据，显示十六进制预览
            preview = raw_bytes.hex()
            if len(preview) > 200:
                preview = preview[:200] + "... (截断)"
            self.show_result(f"解码结果为二进制数据 (共 {len(raw_bytes)} 字节)\n\n十六进制预览:\n{preview}")
            self.status_label.config(text="Base64 解码完成 (二进制)")
            self.save_b64_btn.config(state='normal')

    def save_decoded_file(self):
        """保存解码后的二进制数据"""
        if self.decoded_bytes is None:
            messagebox.showinfo("提示", "没有可保存的解码数据")
            return
        file_path = filedialog.asksaveasfilename(title="保存解码文件", defaultextension=".bin")
        if file_path:
            try:
                with open(file_path, 'wb') as f:
                    f.write(self.decoded_bytes)
                messagebox.showinfo("成功", f"文件已保存至:\n{file_path}")
                self.status_label.config(text="解码文件已保存")
            except Exception as e:
                messagebox.showerror("保存失败", str(e))

    # ---------- 通用工具 ----------
    def show_result(self, content):
        self.result_text.config(state='normal')
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert("1.0", content)
        self.result_text.config(state='disabled')

    def copy_result(self):
        content = self.result_text.get("1.0", tk.END).strip()
        if not content:
            messagebox.showinfo("提示", "没有可复制的内容")
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(content)
        self.status_label.config(text="已复制到剪贴板")
        self.root.after(2000, lambda: self.status_label.config(text=""))

    def clear_all(self):
        self.text_entry.delete("1.0", tk.END)
        self.file_path_var.set("")
        self.update_file_info()
        self.show_result("")
        self.decoded_bytes = None
        self.save_b64_btn.config(state='disabled')
        self.status_label.config(text="已清空")


if __name__ == "__main__":
    root = tk.Tk()
    app = HashBase64App(root)
    root.mainloop()

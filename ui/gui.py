"""
Copyright (c) 2026 八方网域-无涯
"""

import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
from typing import Optional
from threading import Thread
from promptbreach.core.game_engine import GameEngine
from utils.api_client import get_client, get_provider_list


class SciFiApp(tk.Tk):
    """科技感主题配置"""
    def __init__(self):
        super().__init__()
        self.configure(bg="#0a0f1a")
        self.style = ttk.Style(self)
        self._setup_styles()


    def _setup_styles(self):
        # 深色主题背景
        self.configure(bg="#0a0f1a")
        
        # Frame 样式
        self.style.configure("SciFi.TFrame", background="#0d1525")
        
        # Label 样式 - 青色科技感
        self.style.configure("SciFi.TLabel", 
                            background="#0d1525", 
                            foreground="#00d4ff",
                            font=("Consolas", 10))
        
        # 标题 Label
        self.style.configure("Title.TLabel", 
                            background="#0a0f1a", 
                            foreground="#00ffcc",
                            font=("Consolas", 12, "bold"))
        
        # 按钮样式 - 霓虹边框
        self.style.configure("SciFi.TButton",
                            background="#1a2535",
                            foreground="#00d4ff",
                            bordercolor="#00d4ff",
                            lightcolor="#00d4ff",
                            darkcolor="#006688",
                            font=("Consolas", 10))
        self.style.map("SciFi.TButton",
                      background=[("active", "#00d4ff"), ("pressed", "#008bb8")],
                      foreground=[("active", "#0a0f1a"), ("pressed", "#ffffff")])
        
        # 危险按钮
        self.style.configure("Danger.TButton",
                            background="#2a1520",
                            foreground="#ff4466",
                            bordercolor="#ff4466",
                            font=("Consolas", 10))
        self.style.map("Danger.TButton",
                      background=[("active", "#ff4466"), ("pressed", "#cc2244")],
                      foreground=[("active", "#0a0f1a")])
        
        # 输入框样式
        self.style.configure("SciFi.TEntry",
                            fieldbackground="#0d1525",
                            foreground="#00ffcc",
                            bordercolor="#00d4ff",
                            lightcolor="#00d4ff",
                            darkcolor="#006688")
        
        # Combobox 样式
        self.style.configure("SciFi.TCombobox",
                            fieldbackground="#0d1525",
                            background="#1a2535",
                            foreground="#00ffcc",
                            bordercolor="#00d4ff",
                            arrowcolor="#00d4ff",
                            selectbackground="#00d4ff",
                            selectforeground="#0a0f1a")
        
        # Text 样式 (通过 tag 配置)


class PromptBreachApp:
    def __init__(self, master: tk.Tk, engine: Optional[GameEngine] = None) -> None:
        self.master = master
        self.master.configure(bg="#0a0f1a")
        self.engine = engine or GameEngine()
        self.master.title("PromptBreach - OMEGA-9 安全注入靶场")
        self._typing_active = False
        self._pending_text = ""
        self._waiting_for_response = False
        self._wait_seconds = 0
        self._wait_job_id = None
        self.build_ui()
        self.refresh_header()
        self.append_chat("OMEGA-9", self.engine.welcome_text())

    def _create_neon_frame(self, parent, **kwargs):
        """创建带霓虹边框效果的 Frame"""
        frame = tk.Frame(parent, bg="#0d1525", **kwargs)
        # 顶部细线装饰
        neon_bar = tk.Frame(frame, bg="#00d4ff", height=2)
        neon_bar.pack(fill=tk.X, side=tk.TOP)
        return frame

    def build_ui(self) -> None:
        # 顶部状态栏
        top = self._create_neon_frame(self.master)
        top.pack(fill=tk.X, padx=12, pady=(8, 4))

        # 标题
        title_label = tk.Label(top, text="◆ OMEGA-9 LLM安全渗透",
                              bg="#0d1525", fg="#00ffcc", 
                              font=("Consolas", 11, "bold"))
        title_label.pack(side=tk.LEFT)
        
        # 关卡选择区域
        control_frame = tk.Frame(top, bg="#0d1525")
        control_frame.pack(side=tk.RIGHT)
        
        tk.Label(control_frame, text="关卡：", bg="#0d1525", fg="#00d4ff",
                font=("Consolas", 10, "bold")).pack(side=tk.LEFT)
        
        self.level_select_var = tk.IntVar()
        level_ids = list(range(1, self.engine.levels.total + 1))
        self.level_menu = ttk.Combobox(control_frame, textvariable=self.level_select_var, 
                                       values=level_ids, width=4, state="readonly",
                                       font=("Consolas", 10))
        self.level_menu.pack(side=tk.LEFT, padx=(4, 12))
        self.level_menu.bind("<<ComboboxSelected>>", 
                             lambda e: self.on_level_switch(self.level_select_var.get()))

        self.level_var = tk.StringVar()
        self.diff_var = tk.StringVar()
        tk.Label(control_frame, textvariable=self.level_var, bg="#0d1525", 
                fg="#00ffcc", font=("Consolas", 10, "bold")).pack(side=tk.LEFT, padx=8)
        
        diff_label = tk.Label(control_frame, text="难度：", bg="#0d1525", 
                             fg="#666", font=("Consolas", 9))
        diff_label.pack(side=tk.LEFT)
        tk.Label(control_frame, textvariable=self.diff_var, bg="#0d1525", 
                fg="#ff6b35", font=("Consolas", 10, "bold")).pack(side=tk.LEFT, padx=(4, 12))
        
        tk.Button(control_frame, text="[ 重置 ]", command=self.on_reset,
                 bg="#2a1520", fg="#ff4466", activebackground="#ff4466",
                 activeforeground="#0a0f1a", relief=tk.RIDGE, bd=1,
                 cursor="hand2", font=("Consolas", 9)).pack(side=tk.LEFT)
        
        # 超时配置
        timeout_frame = tk.Frame(top, bg="#0d1525")
        timeout_frame.pack(side=tk.RIGHT, padx=(8, 0))
        
        tk.Label(timeout_frame, text="超时(s)：", bg="#0d1525", fg="#888",
                font=("Consolas", 9)).pack(side=tk.LEFT)
        
        self.timeout_var = tk.IntVar(value=60)
        timeout_entry = tk.Entry(timeout_frame, textvariable=self.timeout_var, width=5,
                                 bg="#0d1525", fg="#ffcc00",
                                 font=("Consolas", 10),
                                 insertbackground="#ffcc00",
                                 relief=tk.FLAT, bd=0,
                                 highlightthickness=1,
                                 highlightcolor="#ffcc00",
                                 highlightbackground="#3a3a20")
        timeout_entry.pack(side=tk.LEFT)
        timeout_entry.bind("<Return>", lambda e: self._update_timeout())
        timeout_entry.bind("<FocusOut>", lambda e: self._update_timeout())

        # 聊天区域
        chat_frame = self._create_neon_frame(self.master)
        chat_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=6)
        
        self.chat = scrolledtext.ScrolledText(chat_frame, height=16, 
                                               wrap=tk.WORD, state=tk.NORMAL,
                                               bg="#080d15", fg="#c0e0ff",
                                               font=("Consolas", 10),
                                               insertbackground="#00ffcc",
                                               selectbackground="#1a3a5c",
                                               relief=tk.FLAT, bd=0)
        self.chat.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # 配置聊天文本 tag
        self.chat.tag_configure("omega", foreground="#00ffcc", font=("Consolas", 10, "bold"))
        self.chat.tag_configure("user", foreground="#ff9f43", font=("Consolas", 10))
        self.chat.tag_configure("system", foreground="#00d4ff", font=("Consolas", 9))

        # 输入区域
        input_frame = self._create_neon_frame(self.master)
        input_frame.pack(fill=tk.X, padx=12, pady=(4, 2))
        
        input_label = tk.Label(input_frame, text="▶ 输入：", bg="#0d1525",
                               fg="#00d4ff", font=("Consolas", 10))
        input_label.pack(side=tk.LEFT, padx=(8, 4))
        
        self.input = tk.Text(input_frame, height=3, wrap=tk.WORD,
                            bg="#080d15", fg="#00ffcc",
                            font=("Consolas", 10),
                            insertbackground="#00ffcc",
                            selectbackground="#1a3a5c",
                            relief=tk.FLAT, bd=0)
        self.input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        
        send_btn = tk.Button(input_frame, text="[ 发送 ]", command=self.on_send,
                             bg="#1a2535", fg="#00d4ff", activebackground="#00d4ff",
                             activeforeground="#0a0f1a", relief=tk.RIDGE, bd=1,
                             cursor="hand2", font=("Consolas", 10))
        send_btn.pack(side=tk.LEFT, padx=8)
        
        self.master.bind("<Return>", self.on_enter)
        self.master.bind("<Control-r>", self.on_reset_hotkey)

        # 密码验证区域
        pass_frame = self._create_neon_frame(self.master)
        pass_frame.pack(fill=tk.X, padx=12, pady=(2, 2))
        
        tk.Label(pass_frame, text="🔑 密码：", bg="#0d1525",
                fg="#ff6b35", font=("Consolas", 10)).pack(side=tk.LEFT, padx=8)
        
        self.pass_entry = tk.Entry(pass_frame, show=None, width=28,
                                   bg="#0d1525", fg="#00ffcc",
                                   font=("Consolas", 11),
                                   insertbackground="#00ffcc",
                                   selectbackground="#1a3a5c",
                                   relief=tk.FLAT, bd=0,
                                   highlightthickness=1,
                                   highlightcolor="#00d4ff",
                                   highlightbackground="#1a3a5c")
        self.pass_entry.pack(side=tk.LEFT)
        
        tk.Button(pass_frame, text="[ 验证 ]", command=self.on_verify,
                 bg="#1a2535", fg="#00d4ff", activebackground="#00d4ff",
                 activeforeground="#0a0f1a", relief=tk.RIDGE, bd=1,
                 cursor="hand2", font=("Consolas", 10)).pack(side=tk.LEFT, padx=8)
        tk.Button(pass_frame, text="[ 提示 ]", command=self.on_hint,
                 bg="#1a2535", fg="#00ff88", activebackground="#00ff88",
                 activeforeground="#0a0f1a", relief=tk.RIDGE, bd=1,
                 cursor="hand2", font=("Consolas", 10)).pack(side=tk.LEFT)

        # 状态栏
        status_frame = tk.Frame(self.master, bg="#050810", height=28)
        status_frame.pack(fill=tk.X, padx=12, pady=(2, 6))
        
        # 霓虹底边装饰
        neon_bottom = tk.Frame(status_frame, bg="#00d4ff", height=1)
        neon_bottom.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_var = tk.StringVar(value="> 尝试绕过AI的保护规则...")
        self.waiting_var = tk.StringVar(value="")
        tk.Label(status_frame, textvariable=self.status_var, anchor="w",
                bg="#050810", fg="#00d4ff", 
                font=("Consolas", 9)).pack(side=tk.LEFT, padx=8)
        
        self.waiting_label = tk.Label(status_frame, textvariable=self.waiting_var, anchor="w",
                bg="#050810", fg="#ffcc00",
                font=("Consolas", 9))
        self.waiting_label.pack(side=tk.LEFT, padx=8)

        # API配置按钮 - 放在状态栏右侧
        tk.Button(status_frame, text="[ API配置 ]", command=self.on_config_api,
                 bg="#1a2535", fg="#ffcc00", activebackground="#ffcc00",
                 activeforeground="#0a0f1a", relief=tk.RAISED, bd=1,
                 cursor="hand2", font=("Consolas", 9, "bold")).pack(side=tk.RIGHT, padx=8)

        tk.Label(status_frame, text="八方网域-无涯",
                bg="#050810", fg="#666", 
                font=("Consolas", 9)).pack(side=tk.RIGHT, padx=8)

    def refresh_header(self) -> None:
        info = self.engine.levels.get_level_info()
        self.level_var.set(f"[ {info['id']} / {self.engine.levels.total} ]")
        self.diff_var.set(self.engine.difficulty())
        self.level_select_var.set(info["id"])
        self.master.title(f"PromptBreach // OMEGA-9 // 第 {info['id']} 关")

    def on_level_switch(self, level_id) -> None:
        if self.engine.switch_level(int(level_id)):
            self.chat.delete("1.0", tk.END)
            self.pass_entry.delete(0, tk.END)
            self.refresh_header()
            self.append_chat("OMEGA-9", self.engine.welcome_text())
            self.status_var.set(f"> 已切换到第 {level_id} 关")
            self.engine.clear_history()

    def append_chat(self, role: str, text: str) -> None:
        if role == "OMEGA-9":
            self.chat.insert(tk.END, f"[{role}] ", "omega")
            self._type_text(text + "\n", "omega")
        else:
            self.chat.insert(tk.END, f"[{role}] ", "user")
            self.chat.insert(tk.END, text + "\n", "user")
            self.chat.see(tk.END)

    def _type_text(self, text: str, tag: str = None) -> None:
        if self._typing_active:
            self._pending_text = text
            return
        
        self._typing_active = True
        self._pending_text = ""
        
        def type_char(idx: int) -> None:
            if idx < len(text):
                char = text[idx]
                if tag:
                    self.chat.insert(tk.END, char, tag)
                else:
                    self.chat.insert(tk.END, char)
                self.chat.see(tk.END)
                delay = 8 if char not in " \n" else 15
                self.master.after(delay, lambda: type_char(idx + 1))
            else:
                self._typing_active = False
                if self._pending_text:
                    pending = self._pending_text
                    self._pending_text = ""
                    self._type_text(pending, tag)
        
        type_char(0)

    def load_welcome_and_history(self) -> None:
        hist = self.engine.chat_history()
        if hist:
            for h in hist:
                role = "OMEGA-9" if h.get("role") == "omega" else "用户"
                self.append_chat(role, h.get("content", ""))
        else:
            self.append_chat("OMEGA-9", self.engine.welcome_text())

    def on_send(self, event=None) -> None:
        text = self.input.get("1.0", tk.END).strip()
        if not text:
            return
        
        # 防止重复发送
        if self._waiting_for_response:
            return
        
        self.append_chat("用户", text)
        self.input.delete("1.0", tk.END)
        
        # 显示等待提示
        self._waiting_for_response = True
        self._wait_seconds = 0
        self._update_waiting_label()
        
        # 在独立线程中调用 send_message，避免阻塞UI
        def fetch_response():
            reply, violated = self.engine.send_message(text)
            # 在主线程中更新UI
            self.master.after(0, lambda: self._on_response_received(reply, violated))
        
        Thread(target=fetch_response, daemon=True).start()

    def _update_waiting_label(self) -> None:
        """定时更新等待秒数"""
        if self._waiting_for_response:
            self._wait_seconds += 1
            self.waiting_var.set(f"> 正在等待chatbot返回... 已等待 {self._wait_seconds} 秒")
            self._wait_job_id = self.master.after(1000, self._update_waiting_label)

    def _on_response_received(self, reply: str, violated: bool) -> None:
        """chatbot响应到达后的回调"""
        # 停止等待计时器
        self._waiting_for_response = False
        if self._wait_job_id:
            self.master.after_cancel(self._wait_job_id)
            self._wait_job_id = None
        self.waiting_var.set("")
        
        # 显示chatbot回复
        self.append_chat("OMEGA-9", reply)
        
        if violated:
            self.pass_entry.delete(0, tk.END)
            self.status_var.set("> ⚠ 警告: 检测到违规操作")
        else:
            self.status_var.set("> 消息已发送")

    def _update_timeout(self) -> None:
        """更新 API 超时设置"""
        try:
            timeout = self.timeout_var.get()
            if timeout < 10:
                timeout = 10  # 最小10秒
                self.timeout_var.set(10)
            if timeout > 300:
                timeout = 300  # 最大300秒
                self.timeout_var.set(300)
            
            client = get_client()
            client.update_config(timeout=timeout)
            self.status_var.set(f"> 超时已更新为 {timeout} 秒")
        except ValueError:
            self.timeout_var.set(60)
            self.status_var.set("> 超时设置无效，已恢复为60秒")

    def on_config_api(self) -> None:
        """显示API配置弹窗"""
        ConfigDialog(self.master, self)

    def update_status_with_provider(self) -> None:
        """更新状态栏显示当前服务商"""
        client = get_client()
        provider_name = client.current_provider.upper()
        self.status_var.set(f"> 当前服务商: {provider_name}")

    def on_verify(self) -> None:
        text = self.pass_entry.get().strip()
        if not text:
            return
        ok = self.engine.verify_password(text)
        if ok:
            messagebox.showinfo("✓ 通关成功", "密码正确，自动进入下一关")
            self.engine.advance_level()
            self.chat.delete("1.0", tk.END)
            self.pass_entry.delete(0, tk.END)
            self.refresh_header()
            self.append_chat("OMEGA-9", self.engine.welcome_text())
            self.status_var.set("> ★ 关卡已解锁")
            self.engine.clear_history()
        else:
            messagebox.showerror("✗ 验证失败", "密码错误，请重试")

    def on_hint(self) -> None:
        messagebox.showinfo("💡 提示", self.engine.hint())

    def on_reset(self) -> None:
        if messagebox.askyesno("确认重置", "确认清除进度并回到第1关？"):
            self.engine.reset()
            self.chat.delete("1.0", tk.END)
            self.pass_entry.delete(0, tk.END)
            self.refresh_header()
            self.append_chat("OMEGA-9", self.engine.welcome_text())
            self.status_var.set("> 进度已重置")
            self.engine.clear_history()

    def on_enter(self, event) -> str:
        self.on_send()
        return "break"

    def on_reset_hotkey(self, event) -> str:
        self.on_reset()
        return "break"


class ConfigDialog:
    """API配置弹窗"""
    
    def __init__(self, parent, app: PromptBreachApp):
        self.app = app
        self.window = tk.Toplevel(parent)
        self.window.title("API 配置")
        self.window.configure(bg="#0a0f1a")
        self.window.geometry("480x420")
        self.window.resizable(False, False)
        
        # 居中显示
        self.window.transient(parent)
        self.window.grab_set()
        
        self._build_ui()
        self._load_current_config()
    
    def _build_ui(self) -> None:
        """构建配置界面"""
        # 标题
        title_frame = tk.Frame(self.window, bg="#0a0f1a")
        title_frame.pack(fill=tk.X, padx=16, pady=(16, 8))
        
        tk.Label(title_frame, text="◆ API 服务商配置",
                bg="#0a0f1a", fg="#00ffcc",
                font=("Consolas", 12, "bold")).pack(side=tk.LEFT)
        
        # 主配置区域
        main_frame = tk.Frame(self.window, bg="#0d1525")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=8)
        
        # 服务商选择
        tk.Label(main_frame, text="服务商：",
                bg="#0d1525", fg="#00d4ff",
                font=("Consolas", 10)).pack(anchor="w", pady=(12, 4))
        
        self.provider_var = tk.StringVar()
        providers = get_provider_list()
        provider_names = [p["name"] for p in providers]
        
        self.provider_menu = ttk.Combobox(main_frame, textvariable=self.provider_var,
                                         values=provider_names, width=30,
                                         state="readonly", font=("Consolas", 10))
        self.provider_menu.pack(fill=tk.X, pady=(0, 12))
        self.provider_menu.bind("<<ComboboxSelected>>", self._on_provider_changed)
        
        # API地址
        tk.Label(main_frame, text="API 地址：",
                bg="#0d1525", fg="#00d4ff",
                font=("Consolas", 10)).pack(anchor="w", pady=(8, 4))
        
        self.base_url_var = tk.StringVar()
        base_url_entry = tk.Entry(main_frame, textvariable=self.base_url_var,
                                  bg="#0d1525", fg="#00ffcc",
                                  font=("Consolas", 10),
                                  insertbackground="#00ffcc",
                                  relief=tk.FLAT, bd=0,
                                  highlightthickness=1,
                                  highlightcolor="#00d4ff",
                                  highlightbackground="#1a3a5c")
        base_url_entry.pack(fill=tk.X, pady=(0, 12))
        
        # API密钥
        tk.Label(main_frame, text="API Key：",
                bg="#0d1525", fg="#00d4ff",
                font=("Consolas", 10)).pack(anchor="w", pady=(8, 4))
        
        self.api_key_var = tk.StringVar()
        api_key_entry = tk.Entry(main_frame, textvariable=self.api_key_var,
                                bg="#0d1525", fg="#00ffcc",
                                font=("Consolas", 10),
                                insertbackground="#00ffcc",
                                relief=tk.FLAT, bd=0,
                                show="*",
                                highlightthickness=1,
                                highlightcolor="#00d4ff",
                                highlightbackground="#1a3a5c")
        api_key_entry.pack(fill=tk.X, pady=(0, 12))
        
        # 模型名称
        tk.Label(main_frame, text="模型名称：",
                bg="#0d1525", fg="#00d4ff",
                font=("Consolas", 10)).pack(anchor="w", pady=(8, 4))
        
        self.model_var = tk.StringVar()
        model_entry = tk.Entry(main_frame, textvariable=self.model_var,
                              bg="#0d1525", fg="#00ffcc",
                              font=("Consolas", 10),
                              insertbackground="#00ffcc",
                              relief=tk.FLAT, bd=0,
                              highlightthickness=1,
                              highlightcolor="#00d4ff",
                              highlightbackground="#1a3a5c")
        model_entry.pack(fill=tk.X, pady=(0, 12))
        
        # 按钮区域
        btn_frame = tk.Frame(self.window, bg="#0a0f1a")
        btn_frame.pack(fill=tk.X, padx=16, pady=(8, 16))
        
        tk.Button(btn_frame, text="[ 测试连接 ]", command=self._test_connection,
                 bg="#1a2535", fg="#00d4ff", activebackground="#00d4ff",
                 activeforeground="#0a0f1a", relief=tk.RIDGE, bd=1,
                 cursor="hand2", font=("Consolas", 10)).pack(side=tk.LEFT)
        
        tk.Button(btn_frame, text="[ 保存 ]", command=self._save_config,
                 bg="#1a3a25", fg="#00ff88", activebackground="#00ff88",
                 activeforeground="#0a0f1a", relief=tk.RIDGE, bd=1,
                 cursor="hand2", font=("Consolas", 10)).pack(side=tk.RIGHT)
        
        tk.Button(btn_frame, text="[ 取消 ]", command=self.window.destroy,
                 bg="#2a1520", fg="#ff4466", activebackground="#ff4466",
                 activeforeground="#0a0f1a", relief=tk.RIDGE, bd=1,
                 cursor="hand2", font=("Consolas", 10)).pack(side=tk.RIGHT, padx=(0, 8))
        
        # 状态提示
        self.status_label = tk.Label(self.window, text="",
                                   bg="#0a0f1a", fg="#ffcc00",
                                   font=("Consolas", 9))
        self.status_label.pack(side=tk.BOTTOM, pady=(0, 8))
    
    def _load_current_config(self) -> None:
        """加载当前配置"""
        client = get_client()
        config = client.current_config
        providers = get_provider_list()
        
        # 设置服务商
        current_provider = config.get("provider", "ollama")
        for i, p in enumerate(providers):
            if p["id"] == current_provider:
                self.provider_var.set(p["name"])
                break
        
        # 设置其他字段
        self.base_url_var.set(config.get("base_url", ""))
        self.api_key_var.set(config.get("api_key", ""))
        self.model_var.set(config.get("model", ""))
    
    def _on_provider_changed(self, event=None) -> None:
        """服务商变更时更新默认值"""
        providers = get_provider_list()
        selected_name = self.provider_var.get()
        
        for p in providers:
            if p["name"] == selected_name:
                # 如果是默认地址，则更新
                if self.base_url_var.get() == "" or "默认" not in self.base_url_var.get():
                    info = get_client().get_provider_info(p["id"])
                    self.base_url_var.set(info.get("base_url", ""))
                
                # 设置默认模型
                if not self.model_var.get():
                    self.model_var.set(p["default_model"])
                break
    
    def _test_connection(self) -> None:
        """测试连接"""
        self.status_label.config(text="正在测试连接...", fg="#ffcc00")
        self.window.update()
        
        # 先保存当前配置
        self._save_config(silent=True)
        
        # 测试连接
        client = get_client()
        connected = client.check_connection()
        
        if connected:
            self.status_label.config(text="✓ 连接成功！", fg="#00ff88")
        else:
            self.status_label.config(text="✗ 连接失败，请检查配置", fg="#ff4466")
    
    def _save_config(self, silent: bool = False) -> None:
        """保存配置"""
        providers = get_provider_list()
        selected_name = self.provider_var.get()
        
        provider_id = "ollama"
        for p in providers:
            if p["name"] == selected_name:
                provider_id = p["id"]
                break
        
        base_url = self.base_url_var.get().strip()
        api_key = self.api_key_var.get().strip()
        model = self.model_var.get().strip()
        
        if not base_url:
            if not silent:
                self.status_label.config(text="请输入 API 地址", fg="#ff4466")
            return
        
        if not model:
            if not silent:
                self.status_label.config(text="请输入模型名称", fg="#ff4466")
            return
        
        # 检查是否需要API Key
        info = get_client().get_provider_info(provider_id)
        if info.get("api_key_required") and not api_key:
            if not silent:
                self.status_label.config(text="该服务商需要 API Key", fg="#ff4466")
            return
        
        # 更新配置
        client = get_client()
        client.set_provider(
            provider=provider_id,
            base_url=base_url,
            model=model,
            api_key=api_key
        )
        
        # 更新超时设置
        try:
            timeout = self.app.timeout_var.get()
            if 10 <= timeout <= 300:
                client.update_config(timeout=timeout)
        except ValueError:
            pass
        
        if not silent:
            self.status_label.config(text="✓ 配置已保存！", fg="#00ff88")
            self.app.update_status_with_provider()
            self.window.after(1000, self.window.destroy)
        else:
            self.status_label.config(text="")


def run() -> None:
    root = SciFiApp()
    app = PromptBreachApp(root)
    root.mainloop()

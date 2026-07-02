"""
Copyright (c) 2026 八方网域-无涯
"""

import tkinter as tk
import json
import os
from tkinter import messagebox, scrolledtext, ttk
from typing import Optional
from threading import Thread
from promptbreach.core.game_engine import GameEngine
from promptbreach.utils.api_client import get_client, get_provider_list, logger


def load_model_config():
    """从配置文件加载模型列表"""
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "config", "model_config.json"
    )
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    return config["model_lists"]


def get_display_name(config_str):
    """从模型配置字符串获取显示名称（包含备注）"""
    return config_str

def get_actual_model(config_str):
    """从模型配置字符串提取实际模型名称（不含备注）"""
    if " | " in config_str:
        return config_str.split(" | ")[0].strip()
    return config_str

def find_model_display_name(provider_id, actual_model):
    """根据实际模型名查找对应的显示名称"""
    model_list = MODEL_LISTS.get(provider_id, [])
    for item in model_list:
        if get_actual_model(item) == actual_model:
            return item
    return None


# 各平台模型列表（包含"自定义"选项），从配置文件加载
MODEL_LISTS = load_model_config()


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

        # 使用方法按钮
        help_btn = tk.Button(status_frame, text="[ 使用方法 ]",
                 command=lambda: __import__("webbrowser").open("https://wiki.bafangwy.com/doc/914/"),
                 bg="#1a2535", fg="#00d4ff", activebackground="#00d4ff",
                 activeforeground="#0a0f1a", relief=tk.RAISED, bd=1,
                 cursor="hand2", font=("Consolas", 9, "bold"))
        help_btn.pack(side=tk.RIGHT, padx=8)

        # API配置按钮 - 放在状态栏右侧
        tk.Button(status_frame, text="[ API配置 ]", command=self.on_config_api,
                 bg="#1a2535", fg="#ffcc00", activebackground="#ffcc00",
                 activeforeground="#0a0f1a", relief=tk.RAISED, bd=1,
                 cursor="hand2", font=("Consolas", 9, "bold")).pack(side=tk.RIGHT, padx=8)

        # 八方网域-无涯 超链接
        link_label = tk.Label(status_frame, text="八方网域-无涯",
                bg="#050810", fg="#00d4ff",
                font=("Consolas", 9), cursor="hand2")
        link_label.pack(side=tk.RIGHT, padx=8)
        link_label.bind("<Button-1>", lambda e: __import__("webbrowser").open("https://bafangwy.com/"))
        link_label.bind("<Enter>", lambda e: link_label.config(fg="#00ffcc"))
        link_label.bind("<Leave>", lambda e: link_label.config(fg="#00d4ff"))

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
        
        # 检查API配置是否完整
        client = get_client()
        config = client.current_config
        provider = config.get("provider", "ollama")
        api_key = config.get("api_key", "")
        model = config.get("model", "")
        
        # 检查是否需要配置
        needs_config = False
        if provider == "ollama":
            # 本地Ollama需要检查模型是否设置
            if not model:
                needs_config = True
        else:
            # 远程API需要检查API Key和模型
            if not api_key or not model:
                needs_config = True
        
        if needs_config:
            self._waiting_for_response = False
            messagebox.showwarning("⚠ 提示", "请先配置API后再发送消息")
            self.on_config_api()
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
        provider = client.current_provider
        # 自定义服务商显示更友好的名称
        provider_names = {
            "custom_openai": "自定义OpenAI",
            "custom_anthropic": "自定义Anthropic",
        }
        provider_name = provider_names.get(provider, provider.upper())
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
        self.window.geometry("480x520")
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
        
        # 如何获取API Key 链接
        help_link = tk.Label(title_frame, text="如何获取API Key",
                bg="#0a0f1a", fg="#ff4466",
                font=("Consolas", 9), cursor="hand2")
        help_link.pack(side=tk.RIGHT)
        help_link.bind("<Button-1>", lambda e: __import__("webbrowser").open("https://wiki.bafangwy.com/doc/811/"))
        help_link.bind("<Enter>", lambda e: help_link.config(fg="#ff6688"))
        help_link.bind("<Leave>", lambda e: help_link.config(fg="#ff4466"))
        
        # 当前使用服务商和模型显示
        client = get_client()
        config = client.current_config
        current_provider = config.get("provider", "ollama")
        current_model = config.get("model", "")
        provider_info = client.get_provider_info(current_provider)
        provider_name = provider_info.get("name", current_provider)
        
        # 存储每个服务商的API Key（用于切换时显示）
        self._provider_api_keys = {}
        
        # 从 provider_api_keys 加载（新增的独立存储）
        provider_api_keys = client.current_config.get("provider_api_keys", {})
        self._provider_api_keys.update(provider_api_keys)
        
        # 同时加载已保存配置中的API Key（兼容旧版本）
        saved_configs = client.get_saved_configs()
        for cfg in saved_configs:
            prov = cfg.get("provider", "")
            key = cfg.get("api_key", "")
            if prov and key and prov not in self._provider_api_keys:
                self._provider_api_keys[prov] = key
        
        # 保存当前服务商ID（用于切换时保存API Key）
        self._current_provider_id = current_provider
        
        current_info_frame = tk.Frame(self.window, bg="#0a0f1a")
        current_info_frame.pack(fill=tk.X, padx=16, pady=(0, 8))
        
        tk.Label(current_info_frame, text="当前使用：",
                bg="#0a0f1a", fg="#00d4ff",
                font=("Consolas", 10)).pack(side=tk.LEFT)
        
        self.current_info_label = tk.Label(current_info_frame, 
                text=f"服务商: {provider_name}  |  模型: {current_model}",
                bg="#0a0f1a", fg="#00ff88",
                font=("Consolas", 10))
        self.current_info_label.pack(side=tk.LEFT, padx=(8, 0))
        
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
        
        model_select_frame = tk.Frame(main_frame, bg="#0d1525")
        model_select_frame.pack(fill=tk.X, pady=(0, 4))
        
        self.model_var = tk.StringVar()
        self.model_select_var = tk.StringVar(value="preset")
        
        self.model_menu = ttk.Combobox(model_select_frame, textvariable=self.model_var,
                                       values=MODEL_LISTS.get("ollama", ["自定义"]),
                                       width=28, font=("Consolas", 10))
        self.model_menu.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.model_menu.bind("<<ComboboxSelected>>", self._on_model_changed)
        
        self.model_entry = tk.Entry(model_select_frame,
                              bg="#0d1525", fg="#00ffcc",
                              font=("Consolas", 10),
                              insertbackground="#00ffcc",
                              relief=tk.FLAT, bd=0,
                              highlightthickness=1,
                              highlightcolor="#00d4ff",
                              highlightbackground="#1a3a5c")
        self.model_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 0))
        self.model_entry.pack_forget()  # 默认隐藏
        
        # 获取模型按钮
        self.fetch_models_btn = tk.Button(model_select_frame, text="[ 获取模型 ]",
                 command=self._fetch_models,
                 bg="#1a3a25", fg="#00ff88", activebackground="#00ff88",
                 activeforeground="#0a0f1a", relief=tk.RIDGE, bd=1,
                 cursor="hand2", font=("Consolas", 9))
        self.fetch_models_btn.pack(side=tk.LEFT, padx=(8, 0))
        
        self.model_custom_label = tk.Label(main_frame, text="（选择「自定义」可手动输入模型名称，或点击「获取模型」从API获取）",
                                           bg="#0d1525", fg="#666", font=("Consolas", 8))
        self.model_custom_label.pack(anchor="w", pady=(0, 12))
        
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
        
        tk.Button(btn_frame, text="[ 使用此模型 ]", command=self._use_this_model,
                 bg="#1a3a35", fg="#00ffcc", activebackground="#00ffcc",
                 activeforeground="#0a0f1a", relief=tk.RIDGE, bd=1,
                 cursor="hand2", font=("Consolas", 10)).pack(side=tk.RIGHT, padx=(0, 8))
        
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
                # 更新模型列表
                model_list = MODEL_LISTS.get(p["id"], ["自定义"])
                self.model_menu.config(values=model_list)
                break
        
        # 设置其他字段
        self.base_url_var.set(config.get("base_url", ""))
        # 如果有已保存的API Key，显示星号；否则显示为空
        current_api_key = config.get("api_key", "")
        if current_api_key:
            masked_key = "*" * min(len(current_api_key), 20)
            self.api_key_var.set(masked_key)
        else:
            self.api_key_var.set("")
        
        # 设置模型
        current_model = config.get("model", "")
        model_list = MODEL_LISTS.get(current_provider, ["自定义"])
        
        # 自定义服务商：如果有模型名，显示在输入框中
        if current_provider in ("custom_openai", "custom_anthropic"):
            if current_model:
                self.model_var.set("自定义")
                self.model_entry.config(state="normal")
                self.model_entry.delete(0, tk.END)
                self.model_entry.insert(0, current_model)
                self.model_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
                self.model_menu.pack_forget()
            else:
                self.model_var.set("自定义")
                self.model_entry.delete(0, tk.END)
                self.model_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
                self.model_menu.pack_forget()
        else:
            # 内置服务商
            # 检查实际模型名是否在列表中（需要解析带备注的项）
            model_in_list = any(get_actual_model(item) == current_model for item in model_list[:-1])
            if current_model and not model_in_list:
                # 如果当前模型不在列表中（自定义模型），显示在输入框
                self.model_var.set("自定义")
                self.model_entry.config(state="normal")
                self.model_entry.delete(0, tk.END)
                self.model_entry.insert(0, current_model)
                self.model_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
                self.model_menu.pack_forget()
            else:
                # 查找对应的显示名称（包含备注）
                display_name = find_model_display_name(current_provider, current_model)
                self.model_var.set(display_name if display_name else current_model)
                self.model_entry.pack_forget()
                self.model_menu.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    def _on_provider_changed(self, event=None) -> None:
        """服务商变更时更新默认值"""
        providers = get_provider_list()
        selected_name = self.provider_var.get()
        
        # 先保存当前服务商的API Key（如果用户输入了新的Key）
        self._save_current_api_key()
        
        for p in providers:
            if p["name"] == selected_name:
                # 更新模型列表
                model_list = MODEL_LISTS.get(p["id"], ["自定义"])
                self.model_menu.config(values=model_list)
                
                # 自定义服务商不自动填充地址
                is_custom = p["id"] in ("custom_openai", "custom_anthropic")
                
                if not is_custom:
                    # 内置服务商：如果地址为空则填充默认地址
                    if self.base_url_var.get() == "" or "默认" not in self.base_url_var.get():
                        info = get_client().get_provider_info(p["id"])
                        self.base_url_var.set(info.get("base_url", ""))
                    
                    # 设置默认模型
                    default_model = p["default_model"]
                    self.model_var.set(default_model)
                else:
                    # 自定义服务商：清空地址和模型，让用户手动输入
                    self.base_url_var.set("")
                    self.model_var.set("自定义")
                    # 显示自定义输入框
                    self.model_entry.delete(0, tk.END)
                    self.model_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
                    self.model_entry.focus()
                    self.model_menu.pack_forget()
                
                # 检查该服务商是否有已保存的API Key，显示星号
                saved_key = self._provider_api_keys.get(p["id"], "")
                if saved_key:
                    # 显示星号（不显示实际key）
                    masked_key = "*" * min(len(saved_key), 20)
                    self.api_key_var.set(masked_key)
                else:
                    # 没有保存的key，显示为空
                    self.api_key_var.set("")
                
                # 更新当前服务商ID
                self._current_provider_id = p["id"]
                
                if not is_custom:
                    # 隐藏自定义输入框
                    self.model_entry.pack_forget()
                    self.model_menu.pack(side=tk.LEFT, fill=tk.X, expand=True)
                break
    
    def _save_current_api_key(self) -> None:
        """保存当前服务商的API Key到缓存"""
        current_key = self.api_key_var.get().strip()
        
        # 如果是星号遮罩，说明没有修改，不需要保存
        if current_key and all(c == '*' for c in current_key):
            return
        
        # 如果有实际的Key，保存到缓存和配置文件
        if current_key and self._current_provider_id:
            self._provider_api_keys[self._current_provider_id] = current_key
            # 同时保存到配置文件
            client = get_client()
            client.save_provider_api_key(self._current_provider_id, current_key)
    
    def _on_model_changed(self, event=None) -> None:
        """模型变更时处理自定义输入"""
        selected_model = self.model_var.get()
        if selected_model == "自定义":
            # 显示自定义输入框
            self.model_entry.delete(0, tk.END)
            self.model_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.model_entry.focus()
        else:
            # 隐藏自定义输入框
            self.model_entry.pack_forget()
    
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
            self.status_label.config(text="✓ 连接成功！正在获取模型列表...", fg="#00ff88")
            self.window.update()
            # 测试成功自动保存到已保存配置列表
            self._save_to_saved_configs()
            # 连接成功后自动获取模型列表
            self._fetch_models()
        else:
            self.status_label.config(text="✗ 连接失败，请检查配置", fg="#ff4466")
    
    def _use_this_model(self) -> None:
        """使用当前配置的模型（不关闭窗口，仅切换并更新显示）"""
        providers = get_provider_list()
        selected_name = self.provider_var.get()
        provider_id = "ollama"
        for p in providers:
            if p["name"] == selected_name:
                provider_id = p["id"]
                break
        
        base_url = self.base_url_var.get().strip()
        api_key = self.api_key_var.get().strip()
        
        # 如果是星号遮罩，使用已保存的key
        if api_key and all(c == '*' for c in api_key):
            api_key = self._provider_api_keys.get(provider_id, "")
        
        model_display = self.model_var.get().strip()
        if model_display == "自定义":
            model = self.model_entry.get().strip()
        else:
            model = get_actual_model(model_display)
        
        if provider_id not in ("minimax",) and not base_url:
            self.status_label.config(text="请输入 API 地址", fg="#ff4466")
            return
        
        if not model:
            self.status_label.config(text="请选择或输入模型名称", fg="#ff4466")
            return
        
        info = get_client().get_provider_info(provider_id)
        if info.get("api_key_required") and not api_key:
            self.status_label.config(text="该服务商需要 API Key", fg="#ff4466")
            return
        
        client = get_client()
        client.set_provider(
            provider=provider_id,
            base_url=base_url,
            model=model,
            api_key=api_key
        )
        
        try:
            timeout = self.app.timeout_var.get()
            if 10 <= timeout <= 300:
                client.update_config(timeout=timeout)
        except (ValueError, AttributeError):
            pass
        
        # 更新顶部显示
        provider_info = client.get_provider_info(provider_id)
        provider_cn_name = provider_info.get("name", provider_id)
        self.current_info_label.config(text=f"服务商: {provider_cn_name}  |  模型: {model}")
        
        self.status_label.config(text="✓ 已切换到当前模型", fg="#00ff88")
        self.app.update_status_with_provider()
    
    def _fetch_models(self) -> None:
        """从 API 获取模型列表"""
        self.status_label.config(text="正在获取模型列表...", fg="#ffcc00")
        self.fetch_models_btn.config(state="disabled")
        self.window.update()
        
        # 先保存当前配置
        self._save_config(silent=True)
        
        client = get_client()
        success, model_list = client.fetch_models()
        
        self.fetch_models_btn.config(state="normal")
        
        if success and model_list:
            # 更新模型下拉列表
            model_list_with_custom = model_list + ["自定义"]
            self.model_menu.config(values=model_list_with_custom)
            
            # 自动选中第一个模型
            self.model_var.set(model_list[0])
            self.model_entry.pack_forget()
            self.model_menu.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            # 保存获取到的模型列表到 model_config.json
            self._save_models_to_config(model_list)
            
            self.status_label.config(text=f"✓ 获取到 {len(model_list)} 个模型，已保存", fg="#00ff88")
        else:
            self.status_label.config(text="获取模型失败，请手动输入模型名称", fg="#ff4466")
            # 显示自定义输入框
            self.model_var.set("自定义")
            self.model_entry.delete(0, tk.END)
            self.model_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.model_entry.focus()
            self.model_menu.pack_forget()
    
    def _save_models_to_config(self, model_list: list) -> None:
        """保存模型列表到 model_config.json"""
        # 获取当前服务商 ID
        providers = get_provider_list()
        selected_name = self.provider_var.get()
        provider_id = "custom_openai"
        for p in providers:
            if p["name"] == selected_name:
                provider_id = p["id"]
                break
        
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "config", "model_config.json"
        )
        
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            
            # 更新对应服务商的模型列表，添加"自定义"选项
            config["model_lists"][provider_id] = model_list + ["自定义"]
            
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            
            # 更新全局 MODEL_LISTS
            global MODEL_LISTS
            MODEL_LISTS = config["model_lists"]
            
            logger.info(f"[Config] 模型列表已保存到 model_config.json，服务商: {provider_id}")
        except Exception as e:
            logger.error(f"[Config] 保存模型列表失败: {e}")
    
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
        
        # 如果是星号遮罩，使用已保存的key
        if api_key and all(c == '*' for c in api_key):
            api_key = self._provider_api_keys.get(provider_id, "")
        
        # 获取模型（处理自定义情况和备注）
        model_display = self.model_var.get().strip()
        if model_display == "自定义":
            model = self.model_entry.get().strip()
        else:
            model = get_actual_model(model_display)

        # MiniMax 使用 Anthropic SDK，不需要 base_url；自定义服务商需要 base_url
        if provider_id not in ("minimax",) and not base_url:
            if not silent:
                self.status_label.config(text="请输入 API 地址", fg="#ff4466")
            return
        
        if not model:
            if not silent:
                self.status_label.config(text="请选择或输入模型名称", fg="#ff4466")
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
        
        # 保存 API Key 到 provider_api_keys（如果有的话）
        if api_key:
            client.save_provider_api_key(provider_id, api_key)
            self._provider_api_keys[provider_id] = api_key
        
        # 更新超时设置
        try:
            timeout = self.app.timeout_var.get()
            if 10 <= timeout <= 300:
                client.update_config(timeout=timeout)
        except ValueError:
            pass
        
        # 测试连接成功时自动保存到已保存配置列表
        if not silent:
            self.status_label.config(text="✓ 配置已保存！", fg="#00ff88")
            self.app.update_status_with_provider()
            self.window.after(1000, self.window.destroy)
        else:
            self.status_label.config(text="")

    def _save_to_saved_configs(self) -> None:
        """测试连接成功后，将当前配置保存到已保存列表"""
        providers = get_provider_list()
        selected_name = self.provider_var.get()
        provider_id = "ollama"
        for p in providers:
            if p["name"] == selected_name:
                provider_id = p["id"]
                break

        base_url = self.base_url_var.get().strip()
        api_key = self.api_key_var.get().strip()
        
        # 如果是星号遮罩，使用已保存的key
        if api_key and all(c == '*' for c in api_key):
            api_key = self._provider_api_keys.get(provider_id, "")

        model_display = self.model_var.get().strip()
        if model_display == "自定义":
            model = self.model_entry.get().strip()
        else:
            model = get_actual_model(model_display)

        if not model or not api_key:
            return

        try:
            timeout = self.app.timeout_var.get()
        except (ValueError, AttributeError):
            timeout = 60

        client = get_client()
        client.save_model_config(
            provider=provider_id,
            base_url=base_url,
            model=model,
            api_key=api_key,
            timeout=timeout
        )
        self._refresh_saved_configs()

    def _refresh_saved_configs(self) -> None:
        """刷新内部已保存配置（仅更新API Key缓存，无UI操作）"""
        client = get_client()
        saved = client.get_saved_configs()
        # 更新内部API Key缓存
        for cfg in saved:
            prov = cfg.get("provider", "")
            key = cfg.get("api_key", "")
            if prov and key:
                self._provider_api_keys[prov] = key

    def _load_saved_config(self, idx: int) -> None:
        """加载指定索引的已保存配置"""
        client = get_client()
        if client.load_saved_config(idx):
            # 重新加载界面
            self._load_current_config()
            # 恢复字段
            config = client.current_config
            current_provider = config.get("provider", "ollama")
            providers = get_provider_list()
            for p in providers:
                if p["id"] == current_provider:
                    self.provider_var.set(p["name"])
                    model_list = MODEL_LISTS.get(p["id"], ["自定义"])
                    self.model_menu.config(values=model_list)
                    break
            self.base_url_var.set(config.get("base_url", ""))
            # 显示星号
            current_api_key = config.get("api_key", "")
            if current_api_key:
                masked_key = "*" * min(len(current_api_key), 20)
                self.api_key_var.set(masked_key)
            else:
                self.api_key_var.set("")
            current_model = config.get("model", "")
            model_list = MODEL_LISTS.get(current_provider, ["自定义"])
            model_in_list = any(get_actual_model(item) == current_model for item in model_list[:-1])
            if current_model and not model_in_list:
                self.model_var.set("自定义")
                self.model_entry.config(state="normal")
                self.model_entry.delete(0, tk.END)
                self.model_entry.insert(0, current_model)
                self.model_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
                self.model_menu.pack_forget()
            else:
                display_name = find_model_display_name(current_provider, current_model)
                self.model_var.set(display_name if display_name else current_model)
                self.model_entry.pack_forget()
                self.model_menu.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.status_label.config(text="✓ 已加载配置", fg="#00ff88")
        else:
            self.status_label.config(text="加载失败", fg="#ff4466")

    def _delete_saved_config(self, idx: int) -> None:
        """删除指定索引的已保存配置"""
        client = get_client()
        if client.delete_saved_config(idx):
            self.status_label.config(text="✓ 已删除配置", fg="#00ff88")
        else:
            self.status_label.config(text="删除失败", fg="#ff4466")


def run() -> None:
    root = SciFiApp()
    app = PromptBreachApp(root)
    root.mainloop()

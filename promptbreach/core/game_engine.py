"""
Copyright (c) 2026 八方网域-无涯
"""

import os
from typing import Tuple
from promptbreach.core.rule_engine import detect_violation, is_bypass_successful
from promptbreach.core.chatbot_llm import ChatbotSimulator
from promptbreach.core.level_manager import LevelManager
from promptbreach.levels.level_hints import get_hint


class GameEngine:
    def __init__(self, base_dir: str = None) -> None:
        self.base_dir = base_dir or os.getcwd()
        self.levels = LevelManager(self.base_dir)
        self.bot = ChatbotSimulator()

    def welcome_text(self) -> str:
        info = self.levels.get_level_info()
        return f"欢迎来到第{info['id']}关「{info['name']}」，在输入框和chatbot聊天，你的目标是获取到密码，并在下方验证。"

    def send_message(self, text: str) -> Tuple[str, bool]:
        self.levels.record_chat("user", text)
        level_id = self.levels.current_level
        
        # 获取对话历史，用于多轮检测
        chat_history = self.levels.get_chat_history()
        
        # 1. 尝试检测当前输入是否触发了解锁（触发 bypass 逻辑）
        # 需要同时满足：使用了绕过技术 + 表达了密码请求
        newly_unlocked = is_bypass_successful(text, level_id, chat_history)
        previously_unlocked = self.levels.unlocked
        
        # 2. 如果当前未解锁，且用户触发了直白的"索要密码"行为，则拦截
        if not (previously_unlocked or newly_unlocked):
            violated, _ = detect_violation(text, level_id)
            if violated:
                reply = "[OMEGA-9] 检测到违规操作！我不会告诉你密码的。"
                self.levels.record_chat("omega", reply)
                return reply, True
        
        # 3. 更新解锁状态
        if newly_unlocked:
            self.levels.unlocked = True
        
        # 4. 生成响应
        level_info = self.levels.get_level_info()
        style = self.levels.get_style()
        password = level_info.get("password", "")
        reply = self.bot.get_response(
            text, 
            style, 
            password=password, 
            success=newly_unlocked, 
            already_unlocked=previously_unlocked,
            level_id=level_id,
            level_name=level_info.get("name", "未知关卡")
        )
        
        self.levels.record_chat("omega", reply)
        return reply, False

    def verify_password(self, text: str) -> bool:
        ok = self.levels.verify_password(text)
        return ok

    def advance_level(self) -> None:
        # 标记当前关卡为已通过
        self.levels.mark_level_passed()
        self.levels.advance()
        self.bot = ChatbotSimulator()

    def switch_level(self, level_id: int) -> bool:
        """切换到指定关卡"""
        success = self.levels.jump_to_level(level_id)
        if success:
            self.bot = ChatbotSimulator()
        return success

    def reset(self) -> None:
        """重置整个进度到第一关"""
        self.levels.reset()
        self.levels.passed_levels = []
        self.bot = ChatbotSimulator()

    def hint(self) -> str:
        return get_hint(self.levels.current_level)

    def difficulty(self) -> str:
        return self.levels.get_difficulty_stars()

    def chat_history(self):
        return self.levels.get_chat_history()

    def clear_history(self):
        self.levels.clear_chat_history()

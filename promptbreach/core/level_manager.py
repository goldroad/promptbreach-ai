"""
Copyright (c) 2026 八方网域-无涯
"""

import os
from typing import Dict, List
from promptbreach.levels.level_config import all_levels
from promptbreach.utils.progress_saver import ProgressSaver


class LevelManager:
    def __init__(self, base_dir: str = None) -> None:
        self.base_dir = base_dir or os.getcwd()
        self.progress = ProgressSaver(self.base_dir)
        self.data = self.progress.load()
        self.levels: List[Dict] = all_levels()
        self.total = len(self.levels)
        self.current_level = max(1, min(self.total, int(self.data.get("current_level", 1))))
        self.unlocked = False # 当前关卡是否已被注入成功（针对多轮对话）
        # 已通过的关卡列表（用于检测重复绕过）
        self.passed_levels: List[int] = self.data.get("passed_levels", [])

    def get_level_info(self) -> Dict:
        return next((l for l in self.levels if l["id"] == self.current_level), self.levels[0])

    def get_style(self) -> str:
        return self.get_level_info().get("style", "default")

    def get_difficulty_stars(self) -> str:
        diff = self.get_level_info().get("difficulty", 1)
        return "★" * diff + "☆" * (5 - diff)

    def verify_password(self, text: str) -> bool:
        pw = self.get_level_info()["password"]
        return (text or "").strip() == pw

    def advance(self) -> None:
        if self.current_level < self.total:
            self.jump_to_level(self.current_level + 1)

    def jump_to_level(self, level_id: int) -> bool:
        """跳转到指定关卡"""
        if 1 <= level_id <= self.total:
            self.current_level = level_id
            self.unlocked = False
            self.data["current_level"] = self.current_level
            self.data["chat_history"] = [] # 切换关卡清空历史
            self.progress.save(self.data)
            return True
        return False

    def mark_level_passed(self) -> None:
        """标记当前关卡为已通过"""
        level_id = self.current_level
        if level_id not in self.passed_levels:
            self.passed_levels.append(level_id)
            self.data["passed_levels"] = self.passed_levels
            self.progress.save(self.data)

    def get_passed_levels(self) -> List[int]:
        """获取已通过的关卡列表"""
        return list(self.passed_levels)

    def reset(self) -> None:
        self.jump_to_level(1)

    def record_chat(self, role: str, content: str) -> None:
        self.progress.append_chat(role, content)

    def get_chat_history(self) -> List[Dict]:
        d = self.progress.load()
        return d.get("chat_history", [])

    def clear_chat_history(self):
        data = self.progress.load()
        data["chat_history"] = []
        self.progress.save(data)

"""
Copyright (c) 2026 八方网域-无涯
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List


DEFAULT_PROGRESS = {
    "current_level": 1,
    "completed_levels": [],
    "chat_history": [],
    "last_played": None,
    "passed_levels": [],  # 已通过的关卡列表（用于检测重复绕过）
}


class ProgressSaver:
    def __init__(self, base_dir: str) -> None:
        self.base_dir = base_dir
        self.save_dir = os.path.join(self.base_dir, "promptbreach", "save")
        self.file_path = os.path.join(self.save_dir, "progress.json")
        os.makedirs(self.save_dir, exist_ok=True)

    def load(self) -> Dict[str, Any]:
        if not os.path.exists(self.file_path):
            return DEFAULT_PROGRESS.copy()
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                return DEFAULT_PROGRESS.copy()
            return data
        except Exception:
            return DEFAULT_PROGRESS.copy()

    def save(self, progress: Dict[str, Any]) -> None:
        progress["last_played"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)

    def reset(self) -> Dict[str, Any]:
        if os.path.exists(self.file_path):
            try:
                os.remove(self.file_path)
            except Exception:
                pass
        return DEFAULT_PROGRESS.copy()

    def append_chat(self, role: str, content: str) -> None:
        data = self.load()
        chat: List[Dict[str, Any]] = data.get("chat_history", [])
        chat.append(
            {
                "role": role,
                "content": content,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        )
        data["chat_history"] = chat[-100:]
        self.save(data)

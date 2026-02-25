import json
import os
from datetime import datetime
from typing import List, Dict, Any, Tuple

class SessionManager:
    """工程化会话管理器（单一职责、无 Streamlit 依赖）"""

    def __init__(self, session_dir: str = "sessions"):
        self.session_dir = session_dir
        os.makedirs(self.session_dir, exist_ok=True)

    def generate_session_name(self) -> str:
        return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    def save_session(self, session_id: str, messages: List[Dict]) -> str | None:
        """保存会话，返回错误信息（None = 成功）"""
        if not messages:
            return None
        try:
            data = {
                "current_session": session_id,
                "messages": messages,
            }
            path = os.path.join(self.session_dir, f"{session_id}.json")
            with open(path, "w", encoding="UTF-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            return None
        except Exception as e:
            return f"保存会话失败: {e}"

    def load_sessions(self) -> List[str]:
        """获取所有会话列表"""
        if not os.path.exists(self.session_dir):
            return []
        files = [f[:-5] for f in os.listdir(self.session_dir) if f.endswith(".json")]
        return sorted(files, reverse=True)

    def load_session(self, session_id: str) -> Tuple[Dict[str, Any], str | None]:
        """加载单个会话，返回 (data, error)"""
        path = os.path.join(self.session_dir, f"{session_id}.json")
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="UTF-8") as f:
                    return json.load(f), None
            except Exception as e:
                return {"current_session": session_id, "messages": []}, f"加载会话失败: {e}"
        return {"current_session": session_id, "messages": []}, None

    def switch_to_session(self, target_id: str, current_messages: list, current_id: str) -> Tuple[str, list, str | None]:
        """一键切换会话（自动保存当前）"""
        if current_messages:
            err = self.save_session(current_id, current_messages)
            if err:
                return current_id, current_messages, err

        data, err = self.load_session(target_id)
        return (
            data.get("current_session", target_id),
            data.get("messages", []),
            err
        )

    def delete_session(self, session_id: str) -> str | None:
        """删除会话，返回错误信息（None = 成功）"""
        try:
            path = os.path.join(self.session_dir, f"{session_id}.json")
            if os.path.exists(path):
                os.remove(path)
            return None
        except Exception as e:
            return f"删除会话失败: {e}"
import json
import time
from pathlib import Path
from typing import Dict, Any, List
import config

MEMORY_FILE = config.DATA_DIR / "memory.json"

class MemoryManager:
    """Manages persistent key-value memory, user facts, preferences, and reminders."""

    def __init__(self):
        self.memory_path = MEMORY_FILE
        self._memory = self._load()

    def _load(self) -> Dict[str, Any]:
        if not self.memory_path.exists():
            default_data = {
                "user_name": "User",
                "preferences": {
                    "theme": "dark",
                    "voice": config.DEFAULT_VOICE,
                    "personality": "helpful, concise, sharp, high-tech JARVIS-like tone",
                },
                "facts": [],
                "reminders": [],
                "recent_history": []
            }
            self._save(default_data)
            return default_data
        try:
            with open(self.memory_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"facts": [], "reminders": [], "recent_history": []}

    def _save(self, data: Dict[str, Any] = None):
        if data is None:
            data = self._memory
        try:
            with open(self.memory_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[MemoryManager] Error saving memory: {e}")

    def add_fact(self, fact: str) -> str:
        """Stores a persistent fact about the user or their preferences."""
        if "facts" not in self._memory:
            self._memory["facts"] = []
        
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        entry = {"fact": fact, "timestamp": timestamp}
        self._memory["facts"].append(entry)
        self._save()
        return f"Stored in memory: '{fact}'"

    def get_all_facts(self) -> List[str]:
        """Returns all remembered facts."""
        facts = self._memory.get("facts", [])
        return [f["fact"] for f in facts if isinstance(f, dict) and "fact" in f]

    def add_reminder(self, reminder_text: str, due_time: str = "") -> str:
        """Adds a reminder."""
        if "reminders" not in self._memory:
            self._memory["reminders"] = []
        entry = {
            "reminder": reminder_text,
            "due_time": due_time,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "completed": False
        }
        self._memory["reminders"].append(entry)
        self._save()
        return f"Reminder set: '{reminder_text}'"

    def get_active_reminders(self) -> List[Dict[str, Any]]:
        """Returns all uncompleted reminders."""
        return [r for r in self._memory.get("reminders", []) if not r.get("completed", False)]

    def get_context_summary(self) -> str:
        """Returns a compact context string to inject into the LLM system prompt."""
        facts = self.get_all_facts()
        reminders = self.get_active_reminders()
        user_name = self._memory.get("user_name", "User")

        lines = [f"User Name: {user_name}"]
        if facts:
            lines.append("Things you remember about the user:")
            for f in facts[-10:]:  # Last 10 facts
                lines.append(f"  • {f}")
        if reminders:
            lines.append("Active reminders:")
            for r in reminders[:5]:
                lines.append(f"  • {r['reminder']} (Due: {r.get('due_time', 'N/A')})")
        return "\n".join(lines)

# Singleton instance
memory = MemoryManager()

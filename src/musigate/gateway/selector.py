import re
from difflib import SequenceMatcher

class Selector:
    def select(self, buttons: list, strategy: str, query: str = None, response_text: str = None):
        flat = [btn for row in buttons for btn in row]

        if not flat:
            raise ValueError("按钮列表为空")

        if strategy == "first":
            return flat[0]

        elif strategy == "last":
            return flat[-1]

        elif strategy == "match_title":
            if not query:
                raise ValueError("match_title 策略需要提供 query")
            return max(flat, key=lambda b: self._similarity(b["text"], query))

        elif strategy == "match_text_index":
            if not query or not response_text:
                raise ValueError("match_text_index 策略需要提供 query 和 response_text")
            return self._select_by_numbered_text(flat, response_text, query)

        elif strategy.startswith("match_index"):
            try:
                index = int(strategy.split()[-1])
                return flat[index]
            except (ValueError, IndexError):
                raise ValueError(f"无效的索引: {strategy}")

        raise ValueError(f"未知策略: {strategy}")

    def _similarity(self, a: str, b: str) -> float:
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()

    def _select_by_numbered_text(self, buttons: list, response_text: str, query: str):
        numbered_items = []
        for line in response_text.splitlines():
            match = re.match(r"^\s*(\d+)[\.\、]\s*(.+?)\s*$", line)
            if match:
                numbered_items.append((int(match.group(1)), match.group(2)))

        if not numbered_items:
            raise ValueError("未能从文本响应中解析编号列表")

        best_number, _ = max(
            numbered_items,
            key=lambda item: self._similarity(item[1], query),
        )

        target_text = str(best_number)
        for button in buttons:
            if button.get("text") == target_text:
                return button

        index = best_number - 1
        if 0 <= index < len(buttons):
            return buttons[index]

        raise ValueError(f"未找到编号为 {best_number} 的按钮")

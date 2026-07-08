"""
Audio Converter Pro
Queue state (single source of truth for files awaiting conversion)
"""


class QueueManager:

    def __init__(self):
        self.items = []

    def add(self, path):
        item = {"path": path, "status": "Waiting"}
        self.items.append(item)
        return item

    def contains(self, path):
        return any(item["path"] == path for item in self.items)

    def set_status(self, path, status):
        for item in self.items:
            if item["path"] == path:
                item["status"] = status
                return

    def clear(self):
        self.items.clear()

    def __len__(self):
        return len(self.items)

    def __iter__(self):
        return iter(self.items)

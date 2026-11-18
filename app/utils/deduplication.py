"""In-memory duplicate Telegram update protection."""

from __future__ import annotations

from collections import OrderedDict


class UpdateDeduplicator:
    """Bounded in-memory tracker to ignore duplicate Telegram update_id deliveries."""

    def __init__(self, max_size: int = 1000) -> None:
        if max_size < 1:
            raise ValueError("max_size must be at least 1.")
        self._max_size = max_size
        self._seen: OrderedDict[int, None] = OrderedDict()

    def is_duplicate(self, update_id: int) -> bool:
        """Return True if update_id was already seen recently; otherwise record it."""
        if update_id in self._seen:
            self._seen.move_to_end(update_id)
            return True

        self._seen[update_id] = None
        if len(self._seen) > self._max_size:
            self._seen.popitem(last=False)
        return False

    def __len__(self) -> int:
        return len(self._seen)

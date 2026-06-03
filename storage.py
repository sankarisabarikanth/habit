import threading

class InMemoryStorage:
    """
    A thread-safe, in-memory data store for habits.
    """
    def __init__(self):
        self._lock = threading.Lock()
        self._habits = {}

    def get_all(self):
        with self._lock:
            # Return a copy to avoid external modification issues
            return list(self._habits.values())

    def get_by_id(self, habit_id):
        with self._lock:
            habit = self._habits.get(habit_id)
            return dict(habit) if habit else None

    def save(self, habit):
        with self._lock:
            self._habits[habit["id"]] = dict(habit)
            return dict(habit)

    def delete(self, habit_id):
        with self._lock:
            if habit_id in self._habits:
                del self._habits[habit_id]
                return True
            return False

    def clear(self):
        with self._lock:
            self._habits.clear()

# Global storage instance
db = InMemoryStorage()

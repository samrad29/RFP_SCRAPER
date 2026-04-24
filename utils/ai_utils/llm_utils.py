import time
import random
class TokenTracker:
    def __init__(self):
        self.usage = {
            "groq": {"prompt": 0, "completion": 0},
            "openai": {"prompt": 0, "completion": 0},
        }

    def add(self, provider: str, prompt: int, completion: int):
        self.usage[provider]["prompt"] += prompt
        self.usage[provider]["completion"] += completion

    def total(self):
        return self.usage

def with_backoff(fn, max_retries=5, base_delay=1.0):
    def wrapper(*args, **kwargs):
        last = None

        for i in range(max_retries + 1):
            try:
                return fn(*args, **kwargs)
            except Exception as e:
                last = e

                if i == max_retries:
                    raise

                delay = base_delay * (2 ** i)
                delay *= 1 + random.uniform(-0.2, 0.2)

                time.sleep(delay)

        raise last

    return wrapper
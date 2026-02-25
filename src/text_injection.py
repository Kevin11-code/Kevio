import logging
import time
from pynput.keyboard import Controller
from typing import Optional

logger = logging.getLogger(__name__)


class TextInjector:
    def __init__(self, typing_delay: float = 0.01):
        self.keyboard = Controller()
        self.typing_delay = typing_delay
        self.enabled = True

    def type_text(self, text: str) -> bool:
        if not self.enabled or not text:
            return False

        try:
            logger.info(f"Injecting text: {text}")
            for char in text:
                self.keyboard.type(char)
                time.sleep(self.typing_delay)
            logger.info(f"Typed text: {text[:50]}...")
            return True
        except Exception as e:
            logger.error(f"Error typing text: {e}")
            return False

    def type_text_fast(self, text: str) -> bool:
        if not self.enabled or not text:
            return False

        try:
            self.keyboard.type(text)
            logger.info(f"Typed text (fast): {text[:50]}...")
            return True
        except Exception as e:
            logger.error(f"Error typing text: {e}")
            return False

    def press_key(self, key) -> bool:
        if not self.enabled:
            return False

        try:
            self.keyboard.press(key)
            self.keyboard.release(key)
            return True
        except Exception as e:
            logger.error(f"Error pressing key: {e}")
            return False

    def press_enter(self) -> bool:
        from pynput.keyboard import Key
        return self.press_key(Key.enter)

    def press_space(self) -> bool:
        from pynput.keyboard import Key
        return self.press_key(Key.space)

    def set_enabled(self, enabled: bool):
        self.enabled = enabled
        logger.info(f"Text injection {'enabled' if enabled else 'disabled'}")

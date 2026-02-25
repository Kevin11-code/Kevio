import logging
import sys
import threading
from typing import Optional

from src import SpeechToTextAgent, ConfigManager
from src.system_tray import SystemTray
from src.ui import KevioUI

# pynput for global hotkey
from pynput import keyboard as pynput_kb

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

TOGGLE_KEY = pynput_kb.Key.f9


class KevioApp:
    def __init__(self):
        self.config  = ConfigManager()
        self.agent   = SpeechToTextAgent(self.config)
        self.ui:   Optional[KevioUI]    = None
        self.tray: Optional[SystemTray] = None
        self._hotkey_listener: Optional[pynput_kb.Listener] = None

    # ── Lifecycle ──────────────────────────────────────────────────────────────

    def start(self):
        logger.info("Starting Kevio")

        # Callbacks
        self.agent.on_status_change = self._on_status_change
        self.agent.on_transcription = self._on_transcription

        # System tray (runs in its own daemon thread)
        self.tray = SystemTray(
            on_toggle=self._on_toggle,
            on_exit=self._on_exit,
            on_show_settings=self._on_show_settings,
        )
        self.tray.start()

        # Build UI
        self.ui = KevioUI(on_toggle=self._on_toggle, on_exit=self._on_exit)

        # Start the speech agent in a background thread
        agent_thread = threading.Thread(target=self._run_agent, daemon=True)
        agent_thread.start()

        # Global hotkey listener (daemon thread)
        self._start_hotkey_listener()

        # Run the UI — this blocks until the window is closed
        logger.info("Application started successfully")
        self.ui.run()

    def stop(self):
        logger.info("Stopping Kevio")
        if self.agent:
            self.agent.stop()
        if self.tray:
            self.tray.stop()
        if self._hotkey_listener:
            self._hotkey_listener.stop()
        if self.ui:
            self.ui.quit()
        logger.info("Application stopped")

    def _run_agent(self):
        try:
            self.agent.start()
        except Exception as e:
            logger.error(f"Agent error: {e}")

    # ── Hotkey ─────────────────────────────────────────────────────────────────

    def _start_hotkey_listener(self):
        def on_press(key):
            if key == TOGGLE_KEY:
                self._on_toggle()

        self._hotkey_listener = pynput_kb.Listener(on_press=on_press, daemon=True)
        self._hotkey_listener.start()
        logger.info(f"Global hotkey registered: {TOGGLE_KEY}")

    # ── Callbacks ──────────────────────────────────────────────────────────────

    def _on_status_change(self, status: str):
        logger.info(f"Status changed: {status}")
        if self.tray:
            self.tray.update_status(status)
        if self.ui:
            self.ui.update_status(status)

    def _on_transcription(self, text: str):
        logger.info(f"Transcription received: {text}")
        if self.ui:
            self.ui.add_transcription(text)

    def _on_toggle(self):
        self.agent.toggle()

    def _on_exit(self):
        self.stop()
        sys.exit(0)

    def _on_show_settings(self):
        logger.info("Settings requested (not yet implemented)")


def main():
    print("=" * 50)
    print("Kevio  –  Speech-to-Text Agent")
    print("=" * 50)
    print()
    print("Controls:")
    print("  • F9          – toggle listening on/off")
    print("  • UI button   – click mic or press 'Start Listening'")
    print("  • System tray – right-click for menu")
    print()
    print("Starting…")
    print()

    app = KevioApp()
    app.start()


if __name__ == "__main__":
    main()

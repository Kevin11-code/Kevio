import json
import logging
import os
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    "language": "en",
    "model_path": "models/vosk-model-en-in-0.5",
    "vad_aggressiveness": 1,
    "typing_delay": 0.01,
    "hotkey": "F9",
    "auto_start": False,
    "show_notifications": True,
    "silence_timeout_ms": 2000,
    "chunk_size": 1024,
    "sample_rate": 16000,
}


class ConfigManager:
    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            config_dir = Path.home() / ".kevio"
            config_dir.mkdir(exist_ok=True)
            config_path = str(config_dir / "config.json")
        
        self.config_path = config_path
        self.config: Dict[str, Any] = DEFAULT_CONFIG.copy()
        self.load()

    def load(self):
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    loaded = json.load(f)
                    self.config.update(loaded)
                logger.info(f"Configuration loaded from {self.config_path}")
            else:
                self.save()
                logger.info(f"Default configuration created at {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")

    def save(self):
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"Configuration saved to {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)

    def set(self, key: str, value: Any):
        self.config[key] = value
        self.save()

    def reset(self):
        self.config = DEFAULT_CONFIG.copy()
        self.save()

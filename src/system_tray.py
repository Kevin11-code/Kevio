import logging
import threading
from typing import Optional
from pystray import Icon, Menu, MenuItem
from PIL import Image, ImageDraw

logger = logging.getLogger(__name__)


class SystemTray:
    def __init__(self, on_toggle, on_exit, on_show_settings):
        self.on_toggle = on_toggle
        self.on_exit = on_exit
        self.on_show_settings = on_show_settings
        self.icon: Optional[Icon] = None
        self.status = "stopped"
        
    def _create_icon_image(self, status: str) -> Image.Image:
        width = 64
        height = 64
        image = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(image)
        
        if status == "listening":
            draw.ellipse([8, 8, 56, 56], fill='green', outline='darkgreen', width=2)
            draw.ellipse([24, 24, 40, 40], fill='white')
        elif status == "paused":
            draw.ellipse([8, 8, 56, 56], fill='orange', outline='darkorange', width=2)
            draw.polygon([(24, 20), (24, 44), (44, 32)], fill='white')
        else:
            draw.ellipse([8, 8, 56, 56], fill='gray', outline='darkgray', width=2)
        
        return image

    def _create_menu(self) -> Menu:
        return Menu(
            MenuItem("Toggle (F9)", self.on_toggle),
            MenuItem("Settings", self.on_show_settings),
            Menu.SEPARATOR,
            MenuItem("Exit", self.on_exit)
        )

    def start(self):
        if self.icon:
            return
        
        self.icon = Icon(
            "kevio_speech_to_text",
            self._create_icon_image(self.status),
            "Kevio Speech-to-Text",
            self._create_menu()
        )
        
        thread = threading.Thread(target=self.icon.run, daemon=True)
        thread.start()
        logger.info("System tray started")

    def stop(self):
        if self.icon:
            self.icon.stop()
            self.icon = None
            logger.info("System tray stopped")

    def update_status(self, status: str):
        self.status = status
        if self.icon:
            self.icon.icon = self._create_icon_image(status)
            self.icon.update_menu()
            
    def notify(self, title: str, message: str):
        if self.icon:
            self.icon.notify(message, title)

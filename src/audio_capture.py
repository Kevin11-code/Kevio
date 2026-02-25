import logging
import sounddevice as sd
import threading
from typing import Generator, Optional
import numpy as np

logger = logging.getLogger(__name__)

CHUNK = 1024
SAMPLE_RATE = 16000
CHANNELS = 1


class AudioCapture:
    def __init__(self, chunk_size: int = CHUNK, sample_rate: int = SAMPLE_RATE, channels: int = CHANNELS):
        self.chunk_size = chunk_size
        self.sample_rate = sample_rate
        self.channels = channels
        self.stream = None
        self.is_recording = False
        self._lock = threading.Lock()
        self._audio_buffer = []
        self._buffer_lock = threading.Lock()

    def start(self):
        with self._lock:
            if self.is_recording:
                logger.warning("Audio capture already started")
                return

            try:
                self.stream = sd.InputStream(
                    samplerate=self.sample_rate,
                    channels=self.channels,
                    blocksize=self.chunk_size,
                    callback=self._audio_callback,
                    dtype='int16'
                )
                self.stream.start()
                self.is_recording = True
                logger.info("Audio capture started")
            except Exception as e:
                logger.error(f"Failed to start audio capture: {e}")
                raise

    def stop(self):
        with self._lock:
            if not self.is_recording:
                return

            if self.stream:
                self.stream.stop()
                self.stream.close()
                self.stream = None

            self.is_recording = False
            logger.info("Audio capture stopped")

    def _audio_callback(self, indata, frames, time_info, status):
        if status:
            logger.warning(f"Audio callback status: {status}")
        with self._buffer_lock:
            self._audio_buffer.append(bytes(indata))

    def read_chunk(self) -> Optional[bytes]:
        with self._buffer_lock:
            if self._audio_buffer:
                return self._audio_buffer.pop(0)
        return None

    def audio_generator(self) -> Generator[bytes, None, None]:
        while self.is_recording:
            chunk = self.read_chunk()
            if chunk:
                yield chunk

    def get_available_devices(self) -> list:
        try:
            devices = sd.query_devices()
            return [{'name': devices['name'], 'channels': devices['max_input_channels']}]
        except Exception as e:
            logger.error(f"Error getting devices: {e}")
            return []

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

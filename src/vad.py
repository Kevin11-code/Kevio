import logging
import numpy as np
from typing import Optional

logger = logging.getLogger(__name__)


class VoiceActivityDetector:
    def __init__(self, aggressiveness: int = 2, sample_rate: int = 16000, threshold: float = 0.01):
        self.aggressiveness = aggressiveness
        self.sample_rate = sample_rate
        self.threshold = threshold
        self.frame_duration = 30
        self.frame_size = int(sample_rate * self.frame_duration / 1000)
        
        self._adjust_threshold()
        logger.info(f"VAD initialized with threshold={threshold}, sample_rate={sample_rate}")

    def _adjust_threshold(self):
        if self.aggressiveness == 0:
            self.threshold = 0.002
        elif self.aggressiveness == 1:
            self.threshold = 0.005
        elif self.aggressiveness == 2:
            self.threshold = 0.008
        else:
            self.threshold = 0.01

    def is_speech(self, audio_chunk: bytes) -> bool:
        try:
            audio_data = np.frombuffer(audio_chunk, dtype=np.int16)
            if len(audio_data) == 0:
                return False
            
            rms = np.sqrt(np.mean(audio_data.astype(np.float32) ** 2))
            return rms > (self.threshold * 32768)
        except Exception as e:
            logger.error(f"VAD error: {e}")
            return False

    def is_speech_from_numpy(self, audio_data: np.ndarray) -> bool:
        audio_bytes = audio_data.astype(np.int16).tobytes()
        return self.is_speech(audio_bytes)

    def process_audio_buffer(self, audio_buffer: list) -> list:
        speech_segments = []
        current_segment = []
        
        for chunk in audio_buffer:
            if self.is_speech(chunk):
                current_segment.append(chunk)
            else:
                if current_segment:
                    speech_segments.append(b''.join(current_segment))
                    current_segment = []
        
        if current_segment:
            speech_segments.append(b''.join(current_segment))
        
        return speech_segments


class AudioBuffer:
    def __init__(self, max_duration_ms: int = 10000):
        self.max_duration_ms = max_duration_ms
        self.buffer = []
        self.max_frames = max_duration_ms // 30

    def add(self, audio_chunk: bytes):
        self.buffer.append(audio_chunk)
        if len(self.buffer) > self.max_frames:
            self.buffer.pop(0)

    def get_audio(self) -> bytes:
        return b''.join(self.buffer)

    def clear(self):
        self.buffer = []

    def get_duration_ms(self) -> int:
        return len(self.buffer) * 30

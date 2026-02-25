import logging
from typing import Optional, Generator
import json
import threading
from vosk import Model, KaldiRecognizer

logger = logging.getLogger(__name__)


class SpeechRecognizer:
    def __init__(self, model_path: str = "model", sample_rate: int = 16000):
        self.model_path = model_path
        self.sample_rate = sample_rate
        self.model: Optional[Model] = None
        self.recognizer: Optional[KaldiRecognizer] = None
        self._lock = threading.Lock()
        self._init_model()

    def _init_model(self):
        try:
            logger.info(f"Loading Vosk model from: {self.model_path}")
            self.model = Model(self.model_path)
            self.recognizer = KaldiRecognizer(self.model, self.sample_rate)
            logger.info("Vosk model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Vosk model: {e}")
            raise

    def accept_chunk(self, audio_chunk: bytes) -> Optional[str]:
        """
        Feed an audio chunk into the recognizer.

        When Vosk completes an internal segment (AcceptWaveform returns True),
        it makes the result available via Result(). We return that text here so
        the caller can accumulate it.

        Returns the completed-segment text if one is ready, otherwise None.
        """
        with self._lock:
            if not self.recognizer:
                return None
            try:
                if self.recognizer.AcceptWaveform(audio_chunk):
                    result = json.loads(self.recognizer.Result())
                    text = result.get('text', '')
                    if text:
                        logger.info(f"Segment complete: '{text}'")
                    return text or None
                return None
            except Exception as e:
                logger.error(f"Recognition error: {e}")
                return None

    def flush_final(self) -> Optional[str]:
        """
        Flush any remaining partial audio after silence.
        Resets the recognizer state for the next utterance.
        Returns any leftover text (may be empty).
        """
        with self._lock:
            if not self.recognizer:
                return None
            try:
                result = json.loads(self.recognizer.FinalResult())
                text = result.get('text', '')
                if text:
                    logger.info(f"Flush remainder: '{text}'")
                # Reset for next utterance
                self.recognizer = KaldiRecognizer(self.model, self.sample_rate)
                return text or None
            except Exception as e:
                logger.error(f"Final recognition error: {e}")
                return None

    def recognize_stream(self, audio_generator: Generator[bytes, None, None]) -> Generator[str, None, None]:
        for audio_chunk in audio_generator:
            text = self.accept_chunk(audio_chunk)
            if text:
                yield text

    def reset(self):
        with self._lock:
            if self.model:
                self.recognizer = KaldiRecognizer(self.model, self.sample_rate)

    def __del__(self):
        self.model = None
        self.recognizer = None

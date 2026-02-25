import logging
import threading
import time
from typing import Optional, Callable
from src.audio_capture import AudioCapture
from src.vad import VoiceActivityDetector, AudioBuffer
from src.speech_recognition import SpeechRecognizer
from src.text_injection import TextInjector
from src.config import ConfigManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SpeechToTextAgent:
    def __init__(self, config: Optional[ConfigManager] = None):
        self.config = config or ConfigManager()
        self.audio_capture: Optional[AudioCapture] = None
        self.vad: Optional[VoiceActivityDetector] = None
        self.recognizer: Optional[SpeechRecognizer] = None
        self.text_injector: Optional[TextInjector] = None
        
        self.is_running = False
        self.is_listening = False
        self._processing_thread: Optional[threading.Thread] = None
        self._audio_buffer = AudioBuffer(
            max_duration_ms=self.config.get('silence_timeout_ms', 2000)
        )
        
        self.on_status_change: Optional[Callable[[str], None]] = None
        self.on_transcription: Optional[Callable[[str], None]] = None

    def start(self):
        if self.is_running:
            logger.warning("Agent already running")
            return

        try:
            self._init_components()
            self.audio_capture.start()
            self.is_running = True
            self.is_listening = True
            
            self._processing_thread = threading.Thread(target=self._process_audio)
            self._processing_thread.daemon = True
            self._processing_thread.start()
            
            self._notify_status("listening")
            logger.info("Speech-to-Text agent started")
        except Exception as e:
            logger.error(f"Failed to start agent: {e}")
            self.stop()
            raise

    def stop(self):
        self.is_running = False
        self.is_listening = False
        
        if self._processing_thread:
            self._processing_thread.join(timeout=2)
        
        if self.audio_capture:
            self.audio_capture.stop()
        
        self._notify_status("stopped")
        logger.info("Speech-to-Text agent stopped")

    def toggle(self):
        if self.is_running:
            if self.is_listening:
                self.pause()
            else:
                self.resume()
        else:
            self.start()

    def pause(self):
        self.is_listening = False
        self._notify_status("paused")
        logger.info("Agent paused")

    def resume(self):
        self.is_listening = True
        self._notify_status("listening")
        logger.info("Agent resumed")

    def _init_components(self):
        self.audio_capture = AudioCapture(
            chunk_size=self.config.get('chunk_size', 1024),
            sample_rate=self.config.get('sample_rate', 16000)
        )
        
        self.vad = VoiceActivityDetector(
            aggressiveness=self.config.get('vad_aggressiveness', 2),
            sample_rate=self.config.get('sample_rate', 16000)
        )
        
        self.recognizer = SpeechRecognizer(
            model_path=self.config.get('model_path', 'model'),
            sample_rate=self.config.get('sample_rate', 16000)
        )
        
        self.text_injector = TextInjector(
            typing_delay=self.config.get('typing_delay', 0.01)
        )

    def _process_audio(self):
        # Number of consecutive silent chunks that mark end-of-utterance.
        # chunk_size=1024 samples at 16000 Hz ≈ 64 ms per chunk.
        silence_threshold = self.config.get('silence_timeout_ms', 2000) // 64
        silence_count = 0
        in_utterance = False
        # Accumulate completed Vosk segments here across the whole utterance.
        accumulated_segments = []

        while self.is_running:
            if not self.is_listening:
                time.sleep(0.1)
                continue

            chunk = self.audio_capture.read_chunk()
            if not chunk:
                time.sleep(0.01)
                continue

            is_speech = self.vad.is_speech(chunk)

            # Always feed every chunk into Vosk — it maintains its own audio context.
            # accept_chunk() returns text only when Vosk finishes a complete segment.
            segment_text = self.recognizer.accept_chunk(chunk)
            if segment_text:
                accumulated_segments.append(segment_text)
                logger.info(f"Segment accumulated: '{segment_text}'")

            if is_speech:
                silence_count = 0
                in_utterance = True
                self._notify_status("listening")
            else:
                if in_utterance:
                    silence_count += 1
                    if silence_count >= silence_threshold:
                        # Flush any remaining partial audio from Vosk.
                        remainder = self.recognizer.flush_final()
                        if remainder:
                            accumulated_segments.append(remainder)

                        # Join all segments into one transcription.
                        full_text = ' '.join(accumulated_segments).strip()
                        logger.info(f"Recognized: '{full_text}'")
                        if full_text:
                            self._handle_transcription(full_text)

                        accumulated_segments = []
                        in_utterance = False
                        silence_count = 0

    def _handle_transcription(self, text: str):
        if not text:
            return
        
        logger.info(f"Transcription: {text}")
        
        if self.on_transcription:
            self.on_transcription(text)
        
        if self.text_injector:
            self.text_injector.type_text(text + " ")

    def _notify_status(self, status: str):
        if self.on_status_change:
            self.on_status_change(status)


def main():
    agent = SpeechToTextAgent()
    
    def on_status(status):
        print(f"Status: {status}")
    
    def on_transcription(text):
        print(f"Transcribed: {text}")
    
    agent.on_status_change = on_status
    agent.on_transcription = on_transcription
    
    print("Starting Speech-to-Text Agent...")
    print("Make sure you have downloaded a Vosk model to the 'model' folder")
    print("Download models from: https://alphacephei.com/vosk/models")
    print("Press Ctrl+C to stop")
    
    try:
        agent.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping...")
        agent.stop()


if __name__ == "__main__":
    main()

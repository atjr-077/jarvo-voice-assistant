import speech_recognition as sr
import pyttsx3
import threading
import time
import os
import json
from typing import Optional, List, Dict, Any, Callable
from pathlib import Path
import logging

# Import configuration
from config import (
    get_stt_engine, get_wake_word_enabled, 
    get_listening_timeout, get_phrase_time_limit
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global state
_engine_lock = threading.Lock()
_engine_singleton = None
_selected_mic_index = None
_mic_quality_scores = {}
_recognition_models = {}
_status_callback = None


# STT Engine implementations
class STTEngine:
    """Base class for Speech-to-Text engines"""
    
    def __init__(self, name: str):
        self.name = name
        self.model = None
        
    def load_model(self):
        """Load the recognition model"""
        pass
        
    def recognize(self, audio_data) -> Optional[str]:
        """Recognize speech from audio data"""
        pass
        
    def is_available(self) -> bool:
        """Check if the engine is available"""
        return True


class GoogleSTT(STTEngine):
    """Google Speech Recognition engine"""
    
    def __init__(self):
        super().__init__("google")
        self.recognizer = sr.Recognizer()
        
    def recognize(self, audio_data) -> Optional[str]:
        try:
            return self.recognizer.recognize_google(audio_data)
        except sr.UnknownValueError:
            return None
        except sr.RequestError as e:
            logger.error(f"Google STT error: {e}")
            return None


class VoskSTT(STTEngine):
    """Vosk offline Speech Recognition engine"""
    
    def __init__(self):
        super().__init__("vosk")
        self.model = None
        self.recognizer = None
        
    def load_model(self):
        try:
            import vosk
            # Try to find Vosk model
            model_paths = [
                "models/vosk-model-en-us-0.22",
                "vosk-model-en-us-0.22",
                os.path.expanduser("~/vosk-model-en-us-0.22")
            ]
            
            model_path = None
            for path in model_paths:
                if os.path.exists(path):
                    model_path = path
                    break
                    
            if not model_path:
                logger.warning("Vosk model not found. Please download from https://alphacephei.com/vosk/models")
                return False
                
            self.model = vosk.Model(model_path)
            self.recognizer = vosk.KaldiRecognizer(self.model, 16000)
            logger.info("Vosk model loaded successfully")
            return True
            
        except ImportError:
            logger.error("Vosk not installed. Install with: pip install vosk")
            return False
        except Exception as e:
            logger.error(f"Error loading Vosk model: {e}")
            return False
            
    def recognize(self, audio_data) -> Optional[str]:
        if not self.recognizer:
            return None
            
        try:
            # Convert audio data for Vosk
            import wave
            import io
            
            # Create a temporary WAV file in memory
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(16000)
                wav_file.writeframes(audio_data.get_wav_data())
                
            wav_buffer.seek(0)
            audio_bytes = wav_buffer.read()
            
            if self.recognizer.AcceptWaveform(audio_bytes):
                result = json.loads(self.recognizer.Result())
                return result.get('text', '').strip()
            else:
                partial = json.loads(self.recognizer.PartialResult())
                return partial.get('partial', '').strip()
                
        except Exception as e:
            logger.error(f"Vosk recognition error: {e}")
            return None
            
    def is_available(self) -> bool:
        try:
            import vosk
            return True
        except ImportError:
            return False


class WhisperSTT(STTEngine):
    """Whisper offline Speech Recognition engine"""
    
    def __init__(self):
        super().__init__("whisper")
        self.model = None
        
    def load_model(self):
        try:
            import whisper
            # Load base model (smaller, faster)
            self.model = whisper.load_model("base")
            logger.info("Whisper model loaded successfully")
            return True
            
        except ImportError:
            logger.error("Whisper not installed. Install with: pip install openai-whisper")
            return False
        except Exception as e:
            logger.error(f"Error loading Whisper model: {e}")
            return False
            
    def recognize(self, audio_data) -> Optional[str]:
        if not self.model:
            return None
            
        try:
            import whisper
            import tempfile
            import wave
            
            # Save audio to temporary file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                with wave.open(temp_file.name, 'wb') as wav_file:
                    wav_file.setnchannels(1)
                    wav_file.setsampwidth(2)
                    wav_file.setframerate(16000)
                    wav_file.writeframes(audio_data.get_wav_data())
                
                # Transcribe with Whisper
                result = self.model.transcribe(temp_file.name)
                os.unlink(temp_file.name)
                
                return result["text"].strip()
                
        except Exception as e:
            logger.error(f"Whisper recognition error: {e}")
            return None
            
    def is_available(self) -> bool:
        try:
            import whisper
            return True
        except ImportError:
            return False


def _get_tts_engine():
    """Get thread-safe TTS engine singleton"""
    global _engine_singleton
    with _engine_lock:
        if _engine_singleton is None:
            _engine_singleton = pyttsx3.init()
            # Configure TTS settings
            voices = _engine_singleton.getProperty('voices')
            if voices:
                _engine_singleton.setProperty('voice', voices[0].id)
            _engine_singleton.setProperty('rate', 200)
            _engine_singleton.setProperty('volume', 0.8)
        return _engine_singleton


class MicrophoneManager:
    """Manages microphone selection and quality assessment"""
    
    def __init__(self):
        self.microphones = []
        self.quality_scores = {}
        self.selected_index = None
        
    def discover_microphones(self) -> List[str]:
        """Discover and assess available microphones"""
        try:
            # Try using sounddevice first (compatible with Python 3.14)
            try:
                import sounddevice as sd
                devices = sd.query_devices()
                self.microphones = []
                
                for i, device in enumerate(devices):
                    # Only include input devices (microphones)
                    if device['max_input_channels'] > 0:
                        self.microphones.append(device['name'])
                
                logger.info(f"Found {len(self.microphones)} microphones using sounddevice")
                return self.microphones
                
            except ImportError:
                logger.warning("sounddevice not available, falling back to PyAudio")
                # Fallback to PyAudio if sounddevice is not available
                self.microphones = sr.Microphone.list_microphone_names()
                logger.info(f"Found {len(self.microphones)} microphones using PyAudio")
                return self.microphones
                
        except Exception as e:
            logger.error(f"Error discovering microphones: {e}")
            return []
            
    def assess_microphone_quality(self, index: int) -> float:
        """Assess microphone quality by testing audio levels"""
        try:
            # Simplified: just check if microphone exists
            mic = sr.Microphone(device_index=index)
            # Return default score without testing
            return 0.5
        except Exception as e:
            logger.error(f"Error assessing microphone {index}: {e}")
            return 0.0
            
    def get_best_microphone(self) -> int:
        """Get the index of the best available microphone"""
        if not self.microphones:
            self.discover_microphones()
            
        if not self.microphones:
            return None
            
        best_index = 0
        best_score = 0
        
        for i, mic_name in enumerate(self.microphones):
            # Skip output devices (they usually contain "output" in the name)
            if "output" in mic_name.lower() or "speaker" in mic_name.lower():
                continue
                
            score = self.assess_microphone_quality(i)
            if score > best_score:
                best_score = score
                best_index = i
                
        logger.info(f"Selected microphone {best_index}: {self.microphones[best_index]} (score: {best_score:.2f})")
        return best_index
        
    def set_microphone(self, index: int):
        """Set the selected microphone"""
        if 0 <= index < len(self.microphones):
            self.selected_index = index
            global _selected_mic_index
            _selected_mic_index = index
            logger.info(f"Microphone set to index {index}: {self.microphones[index]}")


class SpeechRecognizer:
    """Main speech recognition class with wake word integration"""
    
    def __init__(self):
        self.mic_manager = MicrophoneManager()
        self.stt_engine = None
        self.wake_word_detector = None
        self.is_listening = False
        self.status_callback = None
        
        # Load STT engine
        self._load_stt_engine()
        
        # Initialize wake word detection if enabled
        if get_wake_word_enabled():
            self._init_wake_word_detection()
            
    def _load_stt_engine(self):
        """Load the configured STT engine"""
        engine_name = get_stt_engine().lower()
        
        if engine_name == "google":
            self.stt_engine = GoogleSTT()
        elif engine_name == "vosk":
            self.stt_engine = VoskSTT()
        elif engine_name == "whisper":
            self.stt_engine = WhisperSTT()
        else:
            logger.warning(f"Unknown STT engine: {engine_name}, falling back to Google")
            self.stt_engine = GoogleSTT()
            
        # Load model if needed
        if hasattr(self.stt_engine, 'load_model'):
            self.stt_engine.load_model()
            
        logger.info(f"STT engine loaded: {self.stt_engine.name}")
        
    def _init_wake_word_detection(self):
        """Initialize wake word detection"""
        try:
            from wake_word import WakeWordDetector
            self.wake_word_detector = WakeWordDetector(
                keyword="jarvis",
                sensitivity=0.7,
                callback=self._on_wake_word_detected
            )
            logger.info("Wake word detection initialized")
        except Exception as e:
            logger.error(f"Error initializing wake word detection: {e}")
            self.wake_word_detector = None
            
    def _on_wake_word_detected(self):
        """Handle wake word detection"""
        logger.info("Wake word detected! Starting listening...")
        self._update_status("Wake word detected! Listening...")
        
        # Start listening for command
        command = self.listen_for_command()
        if command:
            self._update_status("Command received")
            return command
        else:
            self._update_status("No command detected")
            return None
            
    def _update_status(self, status: str):
        """Update status and notify callback"""
        logger.info(f"Status: {status}")
        if self.status_callback:
            self.status_callback(status)
            
    def set_status_callback(self, callback: Callable[[str], None]):
        """Set status update callback"""
        self.status_callback = callback
        
    def listen_for_command(self, timeout: Optional[int] = None, phrase_time_limit: Optional[int] = None) -> Optional[str]:
        """Listen for a voice command and return transcribed text"""
        if timeout is None:
            timeout = get_listening_timeout()
        if phrase_time_limit is None:
            phrase_time_limit = get_phrase_time_limit()
            
        # Get microphone
        mic_index = self.mic_manager.selected_index or self.mic_manager.get_best_microphone()
        if mic_index is None:
            self._update_status("No microphone available")
            return None
            
        try:
            mic = sr.Microphone(device_index=mic_index)
        except Exception as e:
            logger.error(f"Error accessing microphone {mic_index}: {e}")
            self._update_status("Microphone error")
            return None
            
        # Use appropriate recognizer based on engine
        if isinstance(self.stt_engine, GoogleSTT):
            recognizer = self.stt_engine.recognizer
        else:
            recognizer = sr.Recognizer()
            
        with mic as source:
            try:
                # Dynamic threshold adjustment
                self._adjust_thresholds(recognizer, source)
                
                self._update_status("Listening...")
                self.is_listening = True
                
                # Listen for audio
                audio = recognizer.listen(
                    source, 
                    timeout=timeout, 
                    phrase_time_limit=phrase_time_limit
                )
                
                self._update_status("Processing...")
                self.is_listening = False
                
                # Recognize speech
                if isinstance(self.stt_engine, GoogleSTT):
                    command = recognizer.recognize_google(audio)
                else:
                    command = self.stt_engine.recognize(audio)
                    
                if command:
                    command = command.lower().strip()
                    logger.info(f"Recognized: {command}")
                    self._update_status("Command recognized")
                    return command
                else:
                    self._update_status("No speech detected")
                    return None
                    
            except sr.WaitTimeoutError:
                self.is_listening = False
                self._update_status("Listening timeout")
                return None
            except sr.UnknownValueError:
                self.is_listening = False
                self._update_status("Speech not understood")
                return None
            except sr.RequestError as e:
                self.is_listening = False
                logger.error(f"STT service error: {e}")
                self._update_status("STT service unavailable")
                return None
            except Exception as e:
                self.is_listening = False
                logger.error(f"Recognition error: {e}")
                self._update_status("Recognition error")
                return None
                
    def _adjust_thresholds(self, recognizer: sr.Recognizer, source: sr.Microphone):
        """Dynamically adjust recognition thresholds based on ambient noise"""
        try:
            # Adjust for ambient noise
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            
            # Set dynamic thresholds
            recognizer.energy_threshold = max(300, recognizer.energy_threshold * 0.8)
            recognizer.dynamic_energy_threshold = True
            recognizer.dynamic_energy_adjustment_damping = 0.15
            recognizer.dynamic_energy_ratio = 1.5
            recognizer.pause_threshold = 0.8
            
            logger.debug(f"Adjusted thresholds - Energy: {recognizer.energy_threshold}, Pause: {recognizer.pause_threshold}")
            
        except Exception as e:
            logger.error(f"Error adjusting thresholds: {e}")
            
    def start_wake_word_listening(self):
        """Start listening for wake word"""
        if self.wake_word_detector:
            self._update_status("Listening for wake word 'Jarvis'...")
            self.wake_word_detector.listen()
        else:
            logger.warning("Wake word detection not available")
            
    def stop_wake_word_listening(self):
        """Stop wake word listening"""
        if self.wake_word_detector:
            self.wake_word_detector.stop()
            self._update_status("Wake word listening stopped")


# Global recognizer instance
_recognizer_instance = None
_recognizer_lock = threading.Lock()


def _get_recognizer():
    """Get or create the global recognizer instance"""
    global _recognizer_instance
    with _recognizer_lock:
        if _recognizer_instance is None:
            _recognizer_instance = SpeechRecognizer()
        return _recognizer_instance


def list_microphones() -> List[str]:
    """List available microphones"""
    recognizer = _get_recognizer()
    return recognizer.mic_manager.discover_microphones()


def set_mic_index(index: int):
    """Set microphone index"""
    recognizer = _get_recognizer()
    recognizer.mic_manager.set_microphone(index)


def listen() -> Optional[str]:
    """Listen for a voice command (legacy function for compatibility)"""
    recognizer = _get_recognizer()
    
    if get_wake_word_enabled():
        # Use wake word mode
        return recognizer.start_wake_word_listening()
    else:
        # Direct listening mode
        return recognizer.listen_for_command()


def listen_with_wake_word() -> Optional[str]:
    """Listen with wake word detection"""
    recognizer = _get_recognizer()
    return recognizer.start_wake_word_listening()


def listen_direct() -> Optional[str]:
    """Listen directly without wake word"""
    recognizer = _get_recognizer()
    return recognizer.listen_for_command()


def speak(text: str):
    """Speak text using TTS"""
    if not text:
        return
        
    def _speak_thread():
        try:
            engine = _get_tts_engine()
            with _engine_lock:
                engine.say(text)
                engine.runAndWait()
        except Exception as e:
            logger.error(f"TTS error: {e}")
            
    # Run TTS in background thread to avoid blocking
    threading.Thread(target=_speak_thread, daemon=True).start()


def set_status_callback(callback: Callable[[str], None]):
    """Set status update callback"""
    recognizer = _get_recognizer()
    recognizer.set_status_callback(callback)


def get_microphone_quality_scores() -> Dict[int, float]:
    """Get microphone quality scores"""
    recognizer = _get_recognizer()
    return recognizer.mic_manager.quality_scores


def get_current_stt_engine() -> str:
    """Get current STT engine name"""
    recognizer = _get_recognizer()
    return recognizer.stt_engine.name if recognizer.stt_engine else "unknown"


def is_listening() -> bool:
    """Check if currently listening"""
    recognizer = _get_recognizer()
    return recognizer.is_listening


def stop_listening():
    """Stop current listening operation"""
    recognizer = _get_recognizer()
    recognizer.stop_wake_word_listening()
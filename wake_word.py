try:
    import pvporcupine
    import pyaudio
    import struct
    PORCUPINE_AVAILABLE = True
except ImportError:
    PORCUPINE_AVAILABLE = False

class WakeWordDetector:
    def __init__(self, keyword="jarvis", sensitivity=0.7, callback=None):
        if not PORCUPINE_AVAILABLE:
            raise ImportError("pvporcupine is not installed. Install it with: pip install pvporcupine")
        
        self.keyword = keyword
        self.sensitivity = sensitivity
        self.callback = callback
        self.porcupine = pvporcupine.create(keywords=[self.keyword], sensitivities=[self.sensitivity])
        self.pa = pyaudio.PyAudio()
        self.stream = self.pa.open(
            rate=self.porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=self.porcupine.frame_length
        )
        self.running = False

    def listen(self):
        self.running = True
        print(f"[WakeWord] Listening for '{self.keyword}'...")
        while self.running:
            pcm = self.stream.read(self.porcupine.frame_length, exception_on_overflow=False)
            pcm = struct.unpack_from("h" * self.porcupine.frame_length, pcm)
            result = self.porcupine.process(pcm)
            if result >= 0:
                print(f"[WakeWord] Detected '{self.keyword}'!")
                if self.callback:
                    self.callback()

    def stop(self):
        self.running = False
        self.stream.stop_stream()
        self.stream.close()
        self.pa.terminate()
        self.porcupine.delete()

if __name__ == "__main__":
    def on_wake():
        print("Wake word detected! Ready for command...")
    detector = WakeWordDetector(callback=on_wake)
    try:
        detector.listen()
    except KeyboardInterrupt:
        detector.stop()
        print("Stopped.")
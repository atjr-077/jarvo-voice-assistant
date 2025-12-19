"""
Test microphone listing with sounddevice
"""
import sounddevice as sd

print("Testing microphone discovery with sounddevice:\n")
print("=" * 60)

devices = sd.query_devices()
microphones = []

for i, device in enumerate(devices):
    if device['max_input_channels'] > 0:
        microphones.append((i, device['name']))
        print(f"[{len(microphones)-1}] {device['name']}")
        print(f"    Device Index: {i}")
        print(f"    Input Channels: {device['max_input_channels']}")
        print(f"    Sample Rate: {device['default_samplerate']}")
        print()

print("=" * 60)
print(f"\nTotal microphones found: {len(microphones)}")

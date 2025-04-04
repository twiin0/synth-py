import pyaudio
import numpy as np
from synthesizer.limiter import Limiter

class AudioStreamManager:
    """Handles the PyAudio stream initialization and management."""
    def __init__(self, sample_rate=44100, buffer_size=1024):
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size
        self.p = pyaudio.PyAudio()
        self.stream = None

    def start_stream(self, audio_callback):
        """Start the PyAudio stream."""
        self.stream = self.p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.sample_rate,
            output=True,
            frames_per_buffer=self.buffer_size,
            stream_callback=audio_callback
        )
        self.stream.start_stream()
        print("Audio stream started.")

    def stop_stream(self):
        """Stop the PyAudio stream."""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        print("Audio stream stopped.")

class ModuleChainManager:
    """Manages the audio module chain and processes audio through the chain."""
    def __init__(self):
        self.module_chain = []

    def add_module(self, module):
        """Add a module to the chain."""
        self.module_chain.append(module)

    def process_audio(self, frame_count, current_audio=None):
        """Process the audio through the module chain."""
        for module in self.module_chain:
            current_audio = module.generate(frame_count, current_audio)
        if current_audio is None:
            current_audio = np.zeros(frame_count, dtype=np.float32)
        return current_audio

class GlobalControls:
    """Handles the global parameters such as volume, gain, waveform, etc."""
    def __init__(self):
        self.global_volume = 1.0
        self.global_gain = 1.0

    def set_global_volume(self, vol):
        self.global_volume = vol

    def set_global_gain(self, gain):
        self.global_gain = gain

    def apply_global_params(self, audio):
        """Apply global volume and gain adjustments."""
        audio *= self.global_volume
        return audio * self.global_gain

class KeyboardHandler:
    """Handles note on/off via keyboard input."""
    def __init__(self, module_chain):
        self.arpeggiator = None
        self.module_chain = module_chain

    def set_arpeggiator(self, arpeggiator):
        self.arpeggiator = arpeggiator

    def handle_note(self, midi_note, is_press):
        """Handles keyboard events and sends notes to the appropriate modules."""
        if self.arpeggiator:
            if is_press:
                self.arpeggiator.note_on(midi_note)
            else:
                self.arpeggiator.note_off(midi_note)
        else:
            for module in self.module_chain:
                if hasattr(module, 'note_on') and hasattr(module, 'note_off'):
                    if is_press:
                        module.note_on(midi_note)
                    else:
                        module.note_off(midi_note)

class AudioManager:
    def __init__(self, sample_rate=44100, buffer_size=2048):
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size
        self.audio_stream_manager = AudioStreamManager(sample_rate, buffer_size)
        self.module_chain_manager = ModuleChainManager()
        self.global_controls = GlobalControls()
        self.keyboard_handler = KeyboardHandler(self.module_chain_manager.module_chain)
        self.limiter = Limiter(sample_rate=self.sample_rate, threshold=0.95)

    def audio_callback(self, in_data, frame_count, time_info, status):
        """The callback for audio streaming."""
        current_audio = self.module_chain_manager.process_audio(frame_count)
        current_audio = self.global_controls.apply_global_params(current_audio)
        processed = self.limiter.process_block(current_audio)
        np.clip(processed, -1.0, 1.0, out=processed)

        # Convert to int16 for PyAudio
        out_int16 = (processed * 32767).astype(np.int16)
        return (out_int16.tobytes(), pyaudio.paContinue)

    def start_stream(self):
        """Start the audio stream and begin playback."""
        self.audio_stream_manager.start_stream(self.audio_callback)

    def stop_stream(self):
        """Stop the audio stream gracefully."""
        self.audio_stream_manager.stop_stream()

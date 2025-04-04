from synthesizer.audio2 import AudioManager
from gui.synth_gui import SynthGUI
from synthesizer.keyboard_input import KeyboardInput
def main():
    audio_manager = AudioManager(sample_rate=44100, buffer_size=2048)
    
    app = SynthGUI(audio_manager)
    keyboard_input = KeyboardInput(audio_manager=audio_manager)
    keyboard_input.start()
    app.mainloop()
    audio_manager.stop_stream()

if __name__ == "__main__":
    main()

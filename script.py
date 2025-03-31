import customtkinter
from synthesizer.audio import AudioManager
from gui.synth_gui import SynthGUI

def main():
    audio_manager = AudioManager(sample_rate=44100, buffer_size=2048)
    
    app = SynthGUI(audio_manager)
    from synthesizer.keyboard_input import KeyboardInput
    keyboard_input = KeyboardInput(audio_manager=audio_manager)
    keyboard_input.start()
    app.mainloop()
    audio_manager.stop_stream()

if __name__ == "__main__":
    main()

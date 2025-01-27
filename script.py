import customtkinter
from synthesizer.audio import AudioManager
from gui.synth_gui import SynthGUI

def main():
    audio_manager = AudioManager(sample_rate=44100, buffer_size=1024)
    customtkinter.set_appearance_mode("Dark")
    customtkinter.set_default_color_theme("blue")
    
    app = SynthGUI(audio_manager)
    # Optionally auto-start the stream or let user press "Start Synth"
    # audio_manager.start_stream()

    app.mainloop()
    audio_manager.stop_stream()

if __name__ == "__main__":
    main()

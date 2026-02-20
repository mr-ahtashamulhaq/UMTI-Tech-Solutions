from gtts import gTTS


def text_to_speech(text: str, output_path: str = "output.mp3") -> str:
    """Convert text to speech and save as mp3. Returns the output path."""
    tts = gTTS(text=text, lang="en")
    tts.save(output_path)
    return output_path

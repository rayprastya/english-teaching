import whisper
from Levenshtein import ratio

model = whisper.load_model("tiny")

def transcribe_audio(audio_path):
    """Transcribe audio file to text using Whisper."""
    try:
        result = model.transcribe(audio_path)
        return result["text"].strip()
    except Exception as e:
        print(f"Error transcribing audio: {str(e)}")
        return "Sorry, I couldn't understand that."

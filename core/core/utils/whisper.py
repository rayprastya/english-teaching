import whisper
import os
import subprocess
import tempfile
from Levenshtein import ratio

# Use a better model for improved accuracy
model = whisper.load_model("base")  # Changed from "tiny" to "base" for better accuracy

def convert_audio_to_wav(input_path, output_path):
    """Convert audio to WAV format using ffmpeg if available."""
    try:
        # Try to use ffmpeg for better audio conversion
        subprocess.run([
            'ffmpeg', '-i', input_path, 
            '-ar', '16000',  # 16kHz sample rate (Whisper's preferred)
            '-ac', '1',      # Mono channel
            '-c:a', 'pcm_s16le',  # 16-bit PCM
            output_path, '-y'
        ], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        # ffmpeg not available or failed, return False to use original file
        return False

def transcribe_audio(audio_path):
    """Transcribe audio file to text using Whisper with improved processing."""
    converted_file = None
    try:
        # Try to convert audio for better quality
        temp_dir = os.path.dirname(audio_path)
        converted_file = os.path.join(temp_dir, f"converted_{os.path.basename(audio_path)}.wav")
        
        if convert_audio_to_wav(audio_path, converted_file):
            # Use converted file if conversion was successful
            transcription_file = converted_file
        else:
            # Use original file if conversion failed
            transcription_file = audio_path
        
        # Enhanced transcription options
        result = model.transcribe(
            transcription_file,
            language="en",  # Force English language
            fp16=False,     # Use FP32 for better accuracy on CPU
            temperature=0.0,  # Deterministic output
            best_of=1,      # Use beam search
            beam_size=5,    # Better beam search
            word_timestamps=False,  # Don't need word-level timestamps
            condition_on_previous_text=False  # Don't condition on previous text
        )
        
        text = result["text"].strip()
        
        # Clean up the transcribed text
        if text:
            # Remove common Whisper artifacts
            text = text.replace(".", "").replace(",", "").replace("!", "").replace("?", "")
            text = " ".join(text.split())  # Normalize whitespace
            
            # Filter out very short or common whisper errors
            if len(text) < 2 or text.lower() in ["you", "thank you", "thanks", ""]:
                return "Sorry, I couldn't understand that clearly. Please try speaking again."
            
            return text
        else:
            return "Sorry, I couldn't understand that. Please try speaking more clearly."
            
    except Exception as e:
        print(f"Error transcribing audio: {str(e)}")
        return "Sorry, there was an error processing your speech. Please try again."
    finally:
        # Clean up converted file
        if converted_file and os.path.exists(converted_file):
            try:
                os.remove(converted_file)
            except Exception:
                pass

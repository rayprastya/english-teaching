import whisper
from Levenshtein import ratio

model = whisper.load_model("tiny")

def score_spelling(audio, expected_word):
    result = model.transcribe(audio)
    transcribed = result["text"].strip().lower()
    score = ratio(transcribed, expected_word.lower()) * 100
    return transcribed, score


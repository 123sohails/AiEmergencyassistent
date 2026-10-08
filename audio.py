import json
import os
import hashlib
from pathlib import Path

try:
    from google import genai
    from google.genai import types
    client = genai.Client()
    GEMINI_AVAILABLE = True
except Exception:
    client = None
    GEMINI_AVAILABLE = False

try:
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
    whisper_model_instance = None
except ImportError:
    WHISPER_AVAILABLE = False
    whisper_model_instance = None

try:
    import groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

def get_whisper_model():
    global whisper_model_instance
    if whisper_model_instance is None and WHISPER_AVAILABLE:
        print("Loading local faster-whisper model (tiny) into memory...")
        # Using tiny/small for hackathon speed constraints
        whisper_model_instance = WhisperModel("tiny", compute_type="int8")
    return whisper_model_instance

def process_audio_with_groq(path: Path) -> str:
    """
    Fast audio transcription using Groq's Whisper endpoint.
    Supports .ogg format natively (WhatsApp/Telegram exports).
    Much faster than Gemini for transcription tasks.
    """
    if not GROQ_AVAILABLE or not os.getenv("GROQ_API_KEY"):
        raise ValueError("Groq API not configured")
    
    groq_client = groq.Groq(api_key=os.getenv("GROQ_API_KEY"))
    
    try:
        with open(path, "rb") as audio_file:
            transcription = groq_client.audio.transcriptions.create(
                file=(path.name, audio_file),
                model="whisper-large-v3-turbo",
                response_format="text",
                language="en"  # Default to English, can auto-detect
            )
        
        return transcription.text
    except Exception as e:
        print(f"Groq transcription error: {e}")
        raise

def process_audio_with_gemini(path: Path) -> str:
    """Secondary: Pass raw audio directly to Gemini Flash."""
    if not GEMINI_AVAILABLE or not os.getenv("GEMINI_API_KEY"):
        raise ValueError("Gemini API not configured")
        
    audio_file = client.files.upload(file=str(path))
    prompt = """
    You are an expert emergency operator. Listen to this audio clip. 
    It may be in English, Telugu, Hindi, or a mix of languages (Hinglish).
    Provide a direct, exact English translation of the emergency being reported.
    Do not include any conversational filler, just the translated text of what the caller is saying.
    """
    
    response = client.models.generate_content(
        model='gemini-3.8-flash',
        contents=[audio_file, prompt],
        config=types.GenerateContentConfig(temperature=0.0)
    )
    
    transcript = response.text.strip()
    
    # Cleanup uploaded file from Gemini servers to be safe
    try:
        client.files.delete(name=audio_file.name)
    except Exception:
        pass
        
    return transcript

def transcribe_with_whisper(path: Path) -> str:
    """Fallback: Use local faster-whisper if Gemini API is unavailable."""
    model = get_whisper_model()
    if not model:
        raise RuntimeError("faster-whisper is not installed or failed to load")
        
    # task="translate" attempts to translate directly to English
    segments, info = model.transcribe(str(path), task="translate", vad_filter=True)
    return " ".join(s.text.strip() for s in segments)

def process_audio(file_path: str, cache_file="cache/transcripts.json") -> str:
    """
    Takes a path to an audio file.
    Priority 1: Groq Whisper (fastest, supports .ogg natively)
    Priority 2: Gemini Native Audio (good for multi-language)
    Priority 3: Local faster-whisper (offline fallback)
    """
    path = Path(file_path)
    cache_path = Path(cache_file)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    
    if cache_path.exists():
        try:
            cache = json.loads(cache_path.read_text(encoding="utf-8"))
            if path.name in cache:
                print(f"Loaded {path.name} from cache.")
                return cache[path.name]
        except Exception:
            cache = {}
    else:
        cache = {}
        
    print(f"Processing audio: {path.name}")
    transcript = None
    
    # 1. Try Groq Whisper (Fastest, especially for .ogg WhatsApp/Telegram exports)
    try:
        print("Attempting primary method: Groq Whisper...")
        transcript = process_audio_with_groq(path)
    except Exception as e:
        print(f"[Groq Fallback] Switching to Gemini: {e}")
        
        # 2. Try Gemini Native Audio
        try:
            print("Attempting secondary method: Gemini Native Audio API...")
            transcript = process_audio_with_gemini(path)
        except Exception as gemini_e:
            print(f"[Gemini Fallback] Switching to local Whisper: {gemini_e}")
            
            # 3. Try Local faster-whisper (Offline fallback)
            try:
                transcript = transcribe_with_whisper(path)
            except Exception as fallback_e:
                print(f"[Local Fallback Failed] {fallback_e}")
                transcript = "[Audio Processing Completely Failed]"

    if transcript:
        cache[path.name] = transcript
        cache_path.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")
        
    return transcript or "[Audio Processing Failed]"

def process_audio_folder(folder_path: str) -> list:
    """
    Scans a folder for audio files and transcribes them all.
    Returns a list of records ready to be inserted into SQLite.
    """
    AUDIO_EXT = {".mp3", ".wav", ".m4a", ".ogg", ".opus", ".flac"}
    p = Path(folder_path)
    audio_files = sorted(f for f in p.rglob("*") if f.is_file() and f.suffix.lower() in AUDIO_EXT)
    
    records = []
    import uuid
    from datetime import datetime
    
    for f in audio_files:
        transcript = process_audio(str(f))
        
        records.append({
            "id": f"AUDIO-{uuid.uuid4().hex[:6]}",
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source": "call (audio)",
            "sender": "unknown caller",
            "text": transcript,
            "stage": 1,
            "session_id": "dataset",
            "origin": "audio"
        })
        
    return records

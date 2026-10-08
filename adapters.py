"""Universal input adapter: any file or folder -> list of internal message records.

Record shape (Schema 1):
{id, time, source, sender, text, stage, flags{forwarded, from_audio}, raw_ref, error}

Usage:
    from adapters import load_any, sort_records, unique_text_groups, find_audio
    recs = sort_records(load_any("emergency_dataset"))
"""
import json
import re
import hashlib
from pathlib import Path

import pandas as pd

TEXT_NAMES = ["text", "message", "body", "content", "msg", "tweet", "report", "details", "description", "summary", "note"]
TIME_NAMES = ["timestamp", "time", "datetime", "date", "created_at", "ts"]
SENDER_NAMES = ["sender", "username", "user", "from", "author", "phone", "name"]
ID_NAMES = ["id", "message_id", "tweet_id", "sms_id", "msg_id", "record_id"]
AUDIO_EXT = {".mp3", ".wav", ".m4a", ".ogg", ".opus", ".flac"}
TABLE_EXT = {".csv", ".tsv", ".json", ".jsonl", ".xlsx", ".xls", ".txt"}
SKIP_FILES = ("ground_truth", "manifest")  # organizer files: never ingest answer keys


def _pick(cols, names):
    low = {str(c).lower(): c for c in cols}
    for n in names:
        if n in low:
            return low[n]
    for c in cols:
        if any(n in str(c).lower() for n in names):
            return c
    return None


def _pick_id(cols):
    low = {str(c).lower(): c for c in cols}
    for n in ID_NAMES:
        if n in low:
            return low[n]
    for c in cols:
        if str(c).lower().endswith("_id"):
            return c
    return None


def _guess_source(path):
    path = Path(path)
    return _source_from(path.name) if _source_from(path.name) != "unknown" else _source_from(str(path.parent))


def _source_from(p):
    p = p.lower()
    if "whatsapp" in p or "_wa" in p:
        return "whatsapp"
    if "sms" in p:
        return "sms"
    if "twitter" in p or "tweet" in p or "social" in p:
        return "social"
    if "telegram" in p:
        return "telegram"
    return "unknown"


def _guess_stage(path):
    m = re.search(r"stage[_ -]?(\d+)", str(path).lower())
    return int(m.group(1)) if m else 0


def _rows_from_json(obj):
    """List of dicts from a list, or from the first list-of-dicts inside an object."""
    if isinstance(obj, list):
        return [x for x in obj if isinstance(x, dict)]
    if isinstance(obj, dict):
        for v in obj.values():
            if isinstance(v, list) and v and isinstance(v[0], dict):
                return v
        return [obj]
    return []


def _read_table(path):
    ext = path.suffix.lower()
    if ext in (".csv", ".tsv"):
        return pd.read_csv(path, sep="\t" if ext == ".tsv" else ",", dtype=str, on_bad_lines="skip")
    if ext in (".xlsx", ".xls"):
        return pd.read_excel(path, dtype=str)
    if ext == ".jsonl":
        return pd.read_json(path, lines=True, dtype=False)
    return pd.DataFrame(_rows_from_json(json.loads(path.read_text(encoding="utf-8", errors="replace"))))


_WA_LINE = re.compile(
    r"^\[?(\d{1,2}/\d{1,2}/\d{2,4}),?\s+(\d{1,2}:\d{2}(?::\d{2})?\s?(?:[APap][Mm])?)\]?\s*-?\s*([^:]+?):\s(.*)$"
)


def _read_whatsapp_txt(path):
    rows = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = _WA_LINE.match(line.strip())
        if m:
            d, t, who, msg = m.groups()
            rows.append({"timestamp": f"{d} {t}", "sender": who, "text": msg})
        elif rows and line.strip():
            rows[-1]["text"] += " " + line.strip()  # multi-line message
    skip = ("<media omitted>", "end-to-end encrypted", "message was deleted")
    return pd.DataFrame([r for r in rows if not any(s in r["text"].lower() for s in skip)])


def _to_iso(v):
    try:
        t = pd.to_datetime(v, dayfirst=not re.match(r"^\s*\d{4}-", str(v)))
        return None if pd.isna(t) else t.isoformat()
    except Exception:
        return None


def load_file(path):
    """One file -> records. Never raises: problems are returned as error records."""
    path = Path(path)
    src, stage = _guess_source(path), _guess_stage(path)
    try:
        df = _read_whatsapp_txt(path) if path.suffix.lower() == ".txt" else _read_table(path)
    except Exception as e:
        return [dict(id=f"{path.stem}_ERR", time=None, source=src, sender=None, text="", stage=stage,
                     flags={"forwarded": False, "from_audio": False}, raw_ref=str(path),
                     error=f"unreadable file: {e}")]
    if df.empty:
        return []
    cols = list(df.columns)
    icol, dcol, scol = _pick_id(cols), _pick(cols, TIME_NAMES), _pick(cols, SENDER_NAMES)
    low = {str(c).lower().strip(): c for c in cols}
    tcol = next((low[n] for n in TEXT_NAMES if n in low), None)
    if tcol is None:  # fall back to the column with the longest strings
        obj = [c for c in cols if df[c].dtype == object and c not in (icol, dcol, scol)]
        tcol = max(obj, key=lambda c: df[c].astype(str).str.len().mean()) if obj else None
    out = []
    for i, row in df.iterrows():
        text = "" if tcol is None or pd.isna(row[tcol]) else str(row[tcol]).strip()
        
        # Look for explicit lat/lng columns for native GPS support
        lat_val = row['lat'] if 'lat' in low and not pd.isna(row['lat']) else row['latitude'] if 'latitude' in low and not pd.isna(row['latitude']) else None
        lng_val = row['lng'] if 'lng' in low and not pd.isna(row['lng']) else row['longitude'] if 'longitude' in low and not pd.isna(row['longitude']) else None
        
        try: lat_val = float(lat_val) if lat_val is not None else None
        except ValueError: lat_val = None
        try: lng_val = float(lng_val) if lng_val is not None else None
        except ValueError: lng_val = None

        out.append(dict(
            id=str(row[icol]) if icol and not pd.isna(row[icol]) else f"{path.stem}_{i}",
            time=_to_iso(row[dcol]) if dcol else None,
            source=src, stage=stage,
            sender=None if not scol or pd.isna(row[scol]) else str(row[scol]),
            text=text,
            flags={"forwarded": "forwarded" in text.lower(), "from_audio": False},
            raw_ref=f"{path.name}:{i}",
            error=None if text else "empty text",
            lat=lat_val,
            lng=lng_val
        ))
    return out


def find_audio(root):
    return sorted(p for p in Path(root).rglob("*") if p.suffix.lower() in AUDIO_EXT)


def load_any(path):
    """File or folder (recursive) -> records. Audio is listed via find_audio() and transcribed separately."""
    p = Path(path)
    files = [p] if p.is_file() else sorted(f for f in p.rglob("*") if f.is_file())
    recs = []
    for f in files:
        if f.suffix.lower() in TABLE_EXT and not any(s in f.name.lower() for s in SKIP_FILES):
            recs += load_file(f)
    return recs


def sort_records(recs):
    """Stage first, then time (rows in the files are shuffled; stage timestamps overlap)."""
    return sorted(recs, key=lambda r: (r["stage"], r["time"] or "9999", r["id"]))


def _norm(t):
    return re.sub(r"\W+", " ", t.lower()).strip()


def compute_text_hash(text: str) -> str:
    """
    Compute SHA-256 hash of cleaned text for exact duplicate detection.
    Bypasses LLM entirely if hash exists in state.
    """
    cleaned = _norm(text)
    return hashlib.sha256(cleaned.encode('utf-8')).hexdigest()


def unique_text_groups(recs):
    """
    normalized text -> [record ids].
    Enhanced with SHA-256 hashing for exact duplicate detection.
    Send each unique text to the LLM once, then fan the result out.
    """
    g = {}
    hash_to_ids = {}  # Track hashes for exact duplicates
    
    for r in recs:
        if not r["error"]:
            # Use SHA-256 hash for exact duplicate detection
            text_hash = compute_text_hash(r["text"])
            
            # Track all IDs with this hash (exact duplicates)
            if text_hash not in hash_to_ids:
                hash_to_ids[text_hash] = []
            hash_to_ids[text_hash].append(r["id"])
            
            # Use normalized text for semantic grouping
            g.setdefault(_norm(r["text"]), []).append(r["id"])
    
    # Add hash tracking to return value for worker to use
    g["_hashes"] = hash_to_ids
    return g


def transcribe_audio(paths, cache="transcripts.json", model_size="large-v3"):
    """Audio -> text with faster-whisper (untested here: needs the model downloaded).
    Stores original-language text and an English translation; results are cached on disk."""
    from faster_whisper import WhisperModel

    cache_p = Path(cache)
    done = json.loads(cache_p.read_text(encoding="utf-8")) if cache_p.exists() else {}
    model = None
    for p in map(Path, paths):
        if p.name in done:
            continue
        model = model or WhisperModel(model_size, compute_type="int8")
        seg, info = model.transcribe(str(p), task="transcribe", vad_filter=True)
        orig = " ".join(s.text.strip() for s in seg)
        seg2, _ = model.transcribe(str(p), task="translate", vad_filter=True)
        done[p.name] = {"language": info.language, "text": orig,
                        "text_en": " ".join(s.text.strip() for s in seg2)}
        cache_p.write_text(json.dumps(done, ensure_ascii=False, indent=1), encoding="utf-8")
    return done


if __name__ == "__main__":
    import sys
    root = sys.argv[1] if len(sys.argv) > 1 else "emergency_dataset"
    recs = sort_records(load_any(root))
    print(f"{len(recs)} text records, {len(find_audio(root))} audio files")
    print("errors:", sum(1 for r in recs if r["error"]))
    groups = unique_text_groups(recs)
    print(f"{len(groups)} unique texts -> LLM calls saved: {len(recs) - len(groups)}")
    for r in recs[:5]:
        print(r["stage"], r["time"], r["source"], "|", r["text"][:80])

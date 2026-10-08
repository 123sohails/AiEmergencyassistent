import os
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid
import datetime
import threading
import json
import tempfile
import time

# Load env immediately
env_path = Path('.env')
if env_path.exists():
    for line in env_path.read_text().splitlines():
        if '=' in line and not line.strip().startswith('#'):
            k, v = line.split('=', 1)
            v = v.strip()
            if v.startswith('"') and v.endswith('"'):
                v = v[1:-1]
            os.environ[k.strip()] = v

from store import get_all_incidents, get_pending_reports, get_incident_events, get_incident_reports, insert_reports, reset_session
from adapters import load_any, sort_records, unique_text_groups
from audio import process_audio
from worker import run_worker_loop

app = FastAPI(title="NDRF AI Pipeline API")

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Start background worker on boot
@app.on_event("startup")
def startup_event():
    print("Starting background AI worker thread...")
    thread = threading.Thread(target=run_worker_loop, kwargs={"delay": 1.0}, daemon=True)
    thread.start()

@app.get("/api/incidents")
def get_incidents():
    incidents = get_all_incidents('dataset')
    
    # Parse vulnerable JSON strings to arrays for frontend
    for inc in incidents:
        if isinstance(inc.get('vulnerable'), str):
            try:
                inc['vulnerable'] = json.loads(inc['vulnerable'])
            except:
                inc['vulnerable'] = []
    
    return {"incidents": incidents}

@app.get("/api/incidents/{incident_id}/details")
def get_incident_details(incident_id: str):
    events = get_incident_events(incident_id)
    reports = get_incident_reports(incident_id)
    return {
        "events": events,
        "reports": reports
    }

@app.get("/api/pipeline")
def get_pipeline_status():
    pending = get_pending_reports()
    
    # We just want a count and the ID of what is currently processing
    active_report_id = pending[0]['id'] if pending else None
    
    return {
        "pending_count": len(pending),
        "active_report_id": active_report_id
    }

@app.post("/api/upload")
async def upload_dataset(file: UploadFile = File(...)):
    try:
        if not file.filename:
            return {"error": "No file uploaded"}

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / file.filename

            content = await file.read()
            path.write_bytes(content)

            print(f"Processing file: {file.filename}")

            audio_records = []
            if path.suffix.lower() in {".mp3", ".wav", ".m4a", ".ogg", ".flac"}:
                try:
                    transcript = process_audio(str(path))
                    audio_records.append({
                        "id": f"AUDIO-{uuid.uuid4().hex[:6]}",
                        "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "source": "Call (Audio)",
                        "sender": "Unknown",
                        "text": transcript,
                        "stage": 1,
                        "session_id": "dataset",
                        "origin": "audio"
                    })
                except Exception as e:
                    print(f"Audio processing error: {e}")

            try:
                raw_recs = sort_records(load_any(tmpdir))
                print(f"Loaded {len(raw_recs)} records from file")
            except Exception as e:
                print(f"Error loading file: {e}")
                raw_recs = []

            # Simple approach: just insert all records with session_id
            records_to_process = []
            for rec in raw_recs:
                rec['session_id'] = "dataset"
                rec['origin'] = 'dataset'
                records_to_process.append(rec)

            records_to_process.extend(audio_records)
            records_to_process = sorted(records_to_process, key=lambda r: r["time"] or "9999")

            print(f"Inserting {len(records_to_process)} records")
            insert_reports(records_to_process)

        return {"status": "success", "queued": len(records_to_process)}
    except Exception as e:
        import traceback
        print(f"Upload error: {e}")
        traceback.print_exc()
        return {"error": str(e)}

@app.post("/api/reset")
def reset_db():
    reset_session('dataset')
    return {"status": "success"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

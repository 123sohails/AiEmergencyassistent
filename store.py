import sqlite3
import json
from pathlib import Path

DB_PATH = Path("cache/app.db")

def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    # Critical optimizations for concurrent SQLite access (Windows safe)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn

def init_db():
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS reports (
                id TEXT PRIMARY KEY,
                received_at TEXT,
                source TEXT,
                sender TEXT,
                raw_text TEXT,
                stage INTEGER,
                session_id TEXT,
                origin TEXT,
                ingest_order INTEGER,
                processing_status TEXT DEFAULT 'pending',
                
                -- Extraction fields populated by worker
                category TEXT,
                location_text TEXT,
                landmarks TEXT, -- JSON list
                people_count INTEGER,
                resource TEXT,
                vulnerable TEXT, -- JSON list
                urgency TEXT,
                status_hint TEXT,
                summary TEXT,
                
                -- Location fields
                lat REAL,
                lng REAL,
                loc_confidence TEXT
            );
            
            CREATE TABLE IF NOT EXISTS incidents (
                id TEXT PRIMARY KEY,
                session_id TEXT,
                status TEXT,
                urgency TEXT,
                people_latest INTEGER,
                resource TEXT,
                vulnerable TEXT, -- JSON list
                location_text TEXT,
                lat REAL,
                lng REAL,
                loc_confidence TEXT,
                summary TEXT,
                embedding TEXT, -- JSON list
                first_seen TEXT,
                last_updated TEXT
            );
            
            CREATE TABLE IF NOT EXISTS incident_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                incident_id TEXT,
                report_id TEXT,
                time TEXT,
                event_type TEXT,
                detail TEXT
            );
            
            CREATE TABLE IF NOT EXISTS matching_decisions (
                report_id TEXT,
                incident_id TEXT,
                final_score REAL,
                decision TEXT,
                reason TEXT
            );
        """)

def insert_reports(records: list):
    """Batch inserts new reports into the queue"""
    with get_connection() as conn:
        for r in records:
            conn.execute("""
                INSERT OR IGNORE INTO reports (
                    id, received_at, source, sender, raw_text, stage, session_id, origin, ingest_order, processing_status, lat, lng
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)
            """, (
                r['id'], r.get('time'), r.get('source'), r.get('sender'), r['text'], 
                r.get('stage', 1), r.get('session_id', 'default'), r.get('origin', 'dataset'), r.get('ingest_order', 0),
                r.get('lat'), r.get('lng')
            ))

def get_pending_reports():
    with get_connection() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM reports WHERE processing_status = 'pending' ORDER BY ingest_order ASC").fetchall()]

def mark_report_status(report_id: str, status: str):
    with get_connection() as conn:
        conn.execute("UPDATE reports SET processing_status = ? WHERE id = ?", (status, report_id))

def get_open_incidents(session_id: str):
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM incidents WHERE session_id = ? AND status != 'resolved'", (session_id,)).fetchall()
        return [dict(r) for r in rows]

def get_all_incidents(session_id: str = None):
    with get_connection() as conn:
        if session_id:
            rows = conn.execute("SELECT * FROM incidents WHERE session_id = ?", (session_id,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM incidents").fetchall()
        return [dict(r) for r in rows]

def get_incident_reports(incident_id: str):
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT r.* FROM reports r
            JOIN incident_events e ON r.id = e.report_id
            WHERE e.incident_id = ?
            GROUP BY r.id
            ORDER BY r.received_at ASC
        """, (incident_id,)).fetchall()
        return [dict(r) for r in rows]

def get_incident_events(incident_id: str):
    with get_connection() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM incident_events WHERE incident_id = ? ORDER BY id ASC", (incident_id,)).fetchall()]

def get_matching_decision(incident_id: str):
    with get_connection() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM matching_decisions WHERE incident_id = ?", (incident_id,)).fetchall()]

def save_incident(incident: dict, events: list, matching_decision: dict = None):
    """Upsert incident and insert events atomically"""
    with get_connection() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO incidents (
                id, session_id, status, urgency, people_latest, resource, vulnerable, 
                location_text, lat, lng, loc_confidence, summary, embedding, first_seen, last_updated
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            incident['id'], incident['session_id'], incident['status'], incident['urgency'], 
            incident.get('people_count'), incident.get('primary_resource'), json.dumps(incident.get('vulnerable', [])),
            incident.get('location_text'), incident.get('lat'), incident.get('lng'), incident.get('loc_confidence'),
            incident.get('summary'), json.dumps(incident.get('embedding')) if incident.get('embedding') else None,
            incident['first_seen'], incident['last_updated']
        ))
        
        for ev in events:
            conn.execute("""
                INSERT INTO incident_events (incident_id, report_id, time, event_type, detail)
                VALUES (?, ?, ?, ?, ?)
            """, (incident['id'], ev['message_id'], ev['timestamp'], ev['event_type'], ev['detail']))
            
        if matching_decision:
            conn.execute("""
                INSERT INTO matching_decisions (report_id, incident_id, final_score, decision, reason)
                VALUES (?, ?, ?, ?, ?)
            """, (
                matching_decision['report_id'], matching_decision['incident_id'], 
                matching_decision['score'], matching_decision['decision'], matching_decision.get('reason', '')
            ))

def reset_session(session_id: str):
    with get_connection() as conn:
        conn.execute("DELETE FROM reports WHERE session_id = ?", (session_id,))
        conn.execute("DELETE FROM incidents WHERE session_id = ?", (session_id,))
        # cascades would be better, but doing it manually for simplicity
        conn.execute("DELETE FROM incident_events WHERE incident_id IN (SELECT id FROM incidents WHERE session_id = ?)", (session_id,))
        conn.execute("DELETE FROM matching_decisions WHERE incident_id IN (SELECT id FROM incidents WHERE session_id = ?)", (session_id,))

def insert_test_incidents(incidents: list):
    """Directly insert test incidents for demo purposes"""
    with get_connection() as conn:
        for inc in incidents:
            conn.execute("""
                INSERT OR REPLACE INTO incidents (
                    id, session_id, status, urgency, people_latest, resource, vulnerable,
                    location_text, lat, lng, loc_confidence, summary, embedding, first_seen, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                inc['id'], inc['session_id'], inc['status'], inc['urgency'],
                inc['people_latest'], inc['resource'], json.dumps(inc.get('vulnerable', [])),
                inc['location_text'], inc['lat'], inc['lng'], inc['loc_confidence'],
                inc['summary'], json.dumps(inc.get('embedding')) if inc.get('embedding') else None,
                inc['first_seen'], inc['last_updated']
            ))

# Initialize tables on load
init_db()

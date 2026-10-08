import time
from datetime import datetime
import uuid
import json
import hashlib
import re

from store import get_pending_reports, mark_report_status, get_open_incidents, save_incident
from extract import extract_information
from locate import resolve_location
from cluster import calculate_score, get_embedding, T_HI, T_LO
from tracker import Incident, update_incident_state

# In-memory cache for exact duplicate hashes (for hackathon demo)
# In production, this should be stored in database
seen_hashes = {}  # hash -> (count, first_report_id, extraction_result)

def compute_text_hash(text: str) -> str:
    """Compute SHA-256 hash of cleaned text for exact duplicate detection."""
    cleaned = re.sub(r"\W+", " ", text.lower()).strip()
    return hashlib.sha256(cleaned.encode('utf-8')).hexdigest()

def process_report(report: dict):
    msg_id = report['id']
    timestamp = report.get('received_at') or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    session_id = report.get('session_id', 'default')
    
    try:
        # 0. Check for exact duplicates using SHA-256 hash (bypass LLM if duplicate)
        text_hash = compute_text_hash(report['raw_text'])
        
        if text_hash in seen_hashes:
            # Exact duplicate found - skip LLM, increment counter
            count, first_report_id, cached_extraction = seen_hashes[text_hash]
            seen_hashes[text_hash] = (count + 1, first_report_id, cached_extraction)
            print(f"Exact duplicate detected (hash: {text_hash[:8]}...), skipping LLM. Total duplicates: {count + 1}")
            
            # Mark as processed but don't create new incident
            mark_report_status(msg_id, 'duplicate')
            return
        
        # 1. Extraction (No context for batch mode right now, could fetch recent from DB)
        extraction = extract_information(report['raw_text'], [])
        ext_dict = extraction.model_dump()
        
        # Cache the extraction result for this hash
        seen_hashes[text_hash] = (1, msg_id, ext_dict)

        if extraction.category not in ["emergency", "update"]:
            mark_report_status(msg_id, 'ignored')
            return

        # 2. Location
        if report.get('lat') is not None and report.get('lng') is not None:
            # Native GPS Pin (e.g. from Telegram)
            lat = report['lat']
            lng = report['lng']
            conf = "exact"
        else:
            lat, lng, conf = resolve_location(
                extraction.location_text, 
                extraction.landmarks, 
                extraction.city_or_region
            )

        # 3. Clustering
        open_incidents_data = get_open_incidents(session_id)
        open_incidents = []
        for inc_data in open_incidents_data:
            # Rehydrate Incident object
            inc = Incident(
                id=inc_data['id'],
                status=inc_data['status'],
                urgency=inc_data['urgency'],
                people_count=inc_data['people_latest'],
                primary_resource=inc_data['resource'],
                vulnerable=json.loads(inc_data['vulnerable']) if inc_data['vulnerable'] else [],
                location_text=inc_data['location_text'],
                lat=inc_data['lat'],
                lng=inc_data['lng'],
                loc_confidence=inc_data['loc_confidence'],
                summary=inc_data['summary'],
                embedding=json.loads(inc_data['embedding']) if inc_data['embedding'] else None,
                first_seen=inc_data['first_seen'],
                last_updated=inc_data['last_updated']
            )
            open_incidents.append(inc)

        # Only compute embedding if there are existing incidents to match against
        # This saves ~0.5-1 second per report when creating new incidents
        if open_incidents:
            msg_embedding = get_embedding(extraction.summary or report['raw_text'])
        else:
            msg_embedding = None

        best_incident = None
        best_score = -1

        for inc in open_incidents:
            # Pass timestamp for spatio-temporal gating
            score = calculate_score(ext_dict, lat, lng, msg_embedding, inc, timestamp)
            if score > best_score:
                best_score = score
                best_incident = inc

        matching_decision = None

        if best_score >= T_HI:
            # Merge
            update_incident_state(best_incident, ext_dict, msg_id, timestamp)
            best_incident.summary = extraction.summary
            best_incident.embedding = msg_embedding
            
            matching_decision = {
                'report_id': msg_id, 'incident_id': best_incident.id, 
                'score': best_score, 'decision': 'merged'
            }
            inc_dump = best_incident.model_dump()
            inc_dump['session_id'] = session_id
            save_incident(inc_dump, [e.model_dump() for e in best_incident.events], matching_decision)

        elif best_score < T_LO and extraction.category == "emergency":
            # Create new
            new_inc = Incident(
                id=f"INC-{str(uuid.uuid4())[:8].upper()}",
                first_seen=timestamp,
                last_updated=timestamp,
                location_text=extraction.location_text or "",
                lat=lat, lng=lng, loc_confidence=conf,
                summary=extraction.summary or "",
                embedding=msg_embedding
            )
            update_incident_state(new_inc, ext_dict, msg_id, timestamp)
            
            matching_decision = {
                'report_id': msg_id, 'incident_id': new_inc.id, 
                'score': best_score, 'decision': 'created'
            }
            inc_dump = new_inc.model_dump()
            inc_dump['session_id'] = session_id
            save_incident(inc_dump, [e.model_dump() for e in new_inc.events], matching_decision)
        
        else:
            # Tie break placeholder
            if extraction.category == "emergency":
                new_inc = Incident(
                    id=f"INC-{str(uuid.uuid4())[:8].upper()}",
                    first_seen=timestamp,
                    last_updated=timestamp,
                    location_text=extraction.location_text or "",
                    lat=lat, lng=lng, loc_confidence=conf,
                    summary=extraction.summary or "",
                    embedding=msg_embedding
                )
                update_incident_state(new_inc, ext_dict, msg_id, timestamp)
                
                matching_decision = {
                    'report_id': msg_id, 'incident_id': new_inc.id, 
                    'score': best_score, 'decision': 'created (tiebreak fallback)'
                }
                inc_dump = new_inc.model_dump()
                inc_dump['session_id'] = session_id
                save_incident(inc_dump, [e.model_dump() for e in new_inc.events], matching_decision)

        mark_report_status(msg_id, 'processed')
        
    except Exception as e:
        print(f"Error processing report {msg_id}: {e}")
        mark_report_status(msg_id, 'error')

def run_worker_loop(delay=0.1):
    while True:
        try:
            pending = get_pending_reports()
            for report in pending:
                process_report(report)
        except Exception as e:
            print(f"Worker Loop Error: {e}")
        time.sleep(delay)

if __name__ == "__main__":
    print("Starting background worker...")
    run_worker_loop()

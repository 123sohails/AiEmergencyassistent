import uuid
import math
import numpy as np
import re
from datetime import datetime, timedelta
from google import genai
from tracker import Incident, update_incident_state

client = genai.Client()

# Spatio-temporal gating parameters
SPATIAL_RADIUS_KM = 1.5  # Only cluster if within 1.5km
TEMPORAL_WINDOW_HOURS = 3  # Only cluster if within 3 hours

def extract_landmark_similarity(loc1: str, loc2: str) -> float:
    """
    Compare two location texts for landmark similarity.
    Returns score between 0 and 1.
    Improved to handle Indian landmark descriptions better.
    """
    if not loc1 or not loc2:
        return 0.0

    # Check if they share a common landmark (case-insensitive)
    loc1_lower = loc1.lower()
    loc2_lower = loc2.lower()

    # Extract potential landmark names (proper nouns and specific location terms)
    def extract_landmark_terms(location: str) -> set:
        """Extract meaningful landmark terms from location text"""
        # Remove common prepositions and articles
        stopwords = {'the', 'a', 'an', 'near', 'behind', 'opposite', 'beside', 'in', 'on', 'at', 'from', 'to', 'of', 'by', 'backside', 'side', 'gate', 'west', 'east', 'north', 'south'}
        words = location.lower().split()
        # Keep words that are not stopwords and are longer than 2 chars
        return {w for w in words if w not in stopwords and len(w) > 2}

    terms1 = extract_landmark_terms(loc1)
    terms2 = extract_landmark_terms(loc2)

    # Find common meaningful terms
    common_terms = terms1.intersection(terms2)

    # If no common terms, no similarity
    if not common_terms:
        return 0.0

    # Calculate Jaccard similarity (intersection / union)
    union_terms = terms1.union(terms2)
    jaccard_sim = len(common_terms) / len(union_terms) if union_terms else 0.0

    # Boost score if they share proper nouns (area names)
    proper_nouns1 = {w for w in loc1.split() if w[0].isupper() and len(w) > 2}
    proper_nouns2 = {w for w in loc2.split() if w[0].isupper() and len(w) > 2}
    proper_overlap = len(proper_nouns1.intersection(proper_nouns2))

    # Final score calculation
    base_score = jaccard_sim
    if proper_overlap > 0:
        base_score += 0.3  # Boost for shared proper nouns

    # Cap at 1.0
    return min(base_score, 1.0)

def get_embedding(text: str) -> list[float]:
    try:
        response = client.models.embed_content(
            model='models/text-embedding-004',
            contents=text,
        )
        return response.embeddings[0].values
    except Exception as e:
        print(f"Embedding error: {e}")
        return None

def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    if not v1 or not v2: return 0.0
    vec1 = np.array(v1)
    vec2 = np.array(v2)
    num = np.dot(vec1, vec2)
    den = np.linalg.norm(vec1) * np.linalg.norm(vec2)
    return float(num / den) if den > 0 else 0.0

T_HI = 0.60
T_LO = 0.35

def within_spatial_radius(lat1: float, lng1: float, lat2: float, lng2: float, radius_km: float = SPATIAL_RADIUS_KM) -> bool:
    """
    Check if two coordinates are within the specified spatial radius (in km).
    Uses Haversine formula for accurate distance calculation.
    """
    if None in (lat1, lng1, lat2, lng2):
        return False
    
    # Convert to radians
    lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Earth's radius in km
    r = 6371
    distance = c * r
    
    return distance <= radius_km

def within_temporal_window(time1: str, time2: str, window_hours: int = TEMPORAL_WINDOW_HOURS) -> bool:
    """
    Check if two timestamps are within the specified temporal window (in hours).
    """
    try:
        t1 = datetime.strptime(time1, "%Y-%m-%d %H:%M:%S")
        t2 = datetime.strptime(time2, "%Y-%m-%d %H:%M:%S")
        delta = abs(t1 - t2)
        return delta <= timedelta(hours=window_hours)
    except Exception:
        return True  # If parsing fails, allow clustering (conservative)

def calculate_score(msg_extract: dict, msg_lat: float, msg_lng: float, msg_embedding: list[float], incident: Incident, msg_timestamp: str = None) -> float:
    """
    Calculate clustering score with spatio-temporal gating.
    Only computes cosine similarity if reports are within spatial radius AND temporal window.
    """
    # Spatio-temporal gating check
    spatial_ok = within_spatial_radius(msg_lat, msg_lng, incident.lat, incident.lng)
    temporal_ok = within_temporal_window(msg_timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S"), incident.last_updated)
    
    # If not within spatial or temporal bounds, return low score
    if not spatial_ok or not temporal_ok:
        return 0.0
    
    # 1. Location similarity (0 to 1)
    loc_sim = 0.0
    if msg_lat is not None and msg_lng is not None and incident.lat is not None and incident.lng is not None:
        # Simple distance based decay (300m is roughly 0.0027 degrees)
        dist = math.sqrt((msg_lat - incident.lat)**2 + (msg_lng - incident.lng)**2)
        if dist < 0.005:
            loc_sim = 1.0 - (dist / 0.005)

    # 2. Text similarity using embeddings (0 to 1) - only computed if spatio-temporal gates pass
    text_sim = 0.0
    if msg_embedding and incident.embedding:
        text_sim = max(0.0, cosine_similarity(msg_embedding, incident.embedding))

    # 3. Landmark similarity (for Indian-style descriptions) - use as fallback
    landmark_sim = 0.0
    msg_location = msg_extract.get("location_text", "")
    inc_location = incident.location_text or ""
    if msg_location and inc_location and not text_sim:  # Only use if embedding similarity is low
        landmark_sim = extract_landmark_similarity(msg_location, inc_location)

    # 4. Resource similarity
    res_match = 0.0
    if msg_extract.get("resource") and incident.primary_resource:
        if msg_extract.get("resource").lower() == incident.primary_resource.lower():
            res_match = 1.0
        else:
            res_match = 0.0
    else:
        res_match = 0.5 # Unknown

    # Total Score (40% location, 40% text, 10% landmark, 10% resource)
    # Text embeddings handle semantic location understanding well
    score = (0.40 * loc_sim) + (0.40 * text_sim) + (0.10 * landmark_sim) + (0.10 * res_match)
    return score

def process_message(msg_id: str, text: str, extraction: dict, lat: float, lng: float, conf: str, 
                    timestamp: str, open_incidents: list) -> tuple:
    """
    Decides whether to merge the message into an existing incident or create a new one.
    Returns (action, incident_id) where action is 'merged', 'created', or 'ignored'.
    Uses spatio-temporal gating to prevent over-merging unrelated incidents.
    """
    if extraction.get("category") not in ["emergency", "update"]:
        return "ignored", None
        
    msg_embedding = get_embedding(extraction.get("summary", text))
        
    best_incident = None
    best_score = -1
    
    for inc in open_incidents:
        # We now evaluate resolved incidents so that delayed duplicate messages 
        # (e.g. an old SMS arriving late) get safely absorbed into the existing 
        # resolved ticket rather than spawning a fake new emergency.
        # Pass timestamp for spatio-temporal gating
        score = calculate_score(extraction, lat, lng, msg_embedding, inc, timestamp)
        if score > best_score:
            best_score = score
            best_incident = inc
            
    if best_score >= T_HI:
        # Merge
        update_incident_state(best_incident, extraction, msg_id, timestamp)
        # Keep embedding updated with the latest summary
        best_incident.summary = extraction.get("summary", "")
        best_incident.embedding = msg_embedding
        return "merged", best_incident.id
        
    elif best_score < T_LO and extraction.get("category") == "emergency":
        # Create new
        new_inc = Incident(
            id=f"INC-{str(uuid.uuid4())[:8].upper()}",
            first_seen=timestamp,
            last_updated=timestamp,
            location_text=extraction.get("location_text", ""),
            lat=lat,
            lng=lng,
            loc_confidence=conf,
            summary=extraction.get("summary", ""),
            embedding=msg_embedding
        )
        update_incident_state(new_inc, extraction, msg_id, timestamp)
        open_incidents.append(new_inc)
        return "created", new_inc.id
        
    else:
        # Tie break LLM (skipped for now, acting as created if emergency else ignored)
        if extraction.get("category") == "emergency":
            new_inc = Incident(
                id=f"INC-{str(uuid.uuid4())[:8].upper()}",
                first_seen=timestamp,
                last_updated=timestamp,
                location_text=extraction.get("location_text", ""),
                lat=lat,
                lng=lng,
                loc_confidence=conf,
                summary=extraction.get("summary", ""),
                embedding=msg_embedding
            )
            update_incident_state(new_inc, extraction, msg_id, timestamp)
            open_incidents.append(new_inc)
            return "created", new_inc.id
            
    return "ignored", None

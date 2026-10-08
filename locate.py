import os
import time
import requests
import re
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from google import genai

LOCATIONIQ_API_KEY = os.getenv("LOCATIONIQ_API_KEY", "")
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

geolocator = Nominatim(user_agent="emergency_assistant_hackathon")
geocode_cache = {}
genai_client = genai.Client()

# Common Indian landmark patterns
LANDMARK_PATTERNS = [
    r'(MRTS|metro|station)',
    r'(junction|signal|flyover)',
    r'(school|college|hospital)',
    r'(temple|church|mosque)',
    r'(market|complex|mall)',
    r'(gate|entrance|exit)',
]

def extract_base_landmark(location_text: str) -> tuple:
    """
    Extract base landmark and relative direction from Indian-style descriptions.
    Returns (base_landmark, relative_direction)
    """
    if not location_text:
        return None, None

    # Spatial relationship patterns
    spatial_patterns = {
        'near': r'\b(near|nearby|close to|by)\b',
        'behind': r'\b(behind|back of|backside)\b',
        'opposite': r'\b(opposite|across from|facing)\b',
        'beside': r'\b(beside|next to|adjacent to)\b',
        'in front of': r'\b(in front of|front of)\b',
    }

    # Extract relative direction
    relative_direction = None
    for direction, pattern in spatial_patterns.items():
        if re.search(pattern, location_text, re.IGNORECASE):
            relative_direction = direction
            break

    # Extract base landmark (remove spatial words)
    base_landmark = location_text
    for pattern in spatial_patterns.values():
        base_landmark = re.sub(pattern, '', base_landmark, flags=re.IGNORECASE)

    # Clean up extra words
    base_landmark = re.sub(r'\b(the|a|an)\b', '', base_landmark, flags=re.IGNORECASE)
    base_landmark = base_landmark.strip()

    return base_landmark, relative_direction

def geocode_location_locationiq(landmark_name: str, detected_city: str = None):
    if detected_city and detected_city.lower() not in landmark_name.lower():
        query = f"{landmark_name}, {detected_city}"
    else:
        query = landmark_name
        
    if query in geocode_cache:
        return geocode_cache[query]
        
    try:
        # Enforce LocationIQ's 2 req/sec rate limit
        time.sleep(0.5)
        url = f"https://us1.locationiq.com/v1/search?key={LOCATIONIQ_API_KEY}&q={query}&format=json"
        res = requests.get(url, timeout=5)
        if res.status_code == 200 and res.json():
            data = res.json()[0]
            result = (float(data["lat"]), float(data["lon"]), "high")
            geocode_cache[query] = result
            return result
    except Exception as e:
        print(f"[LocationIQ Error] {e}")
        
    result = (None, None, "low")
    geocode_cache[query] = result
    return result

def geocode_location_nominatim(landmark_name: str, detected_city: str = None):
    if detected_city and detected_city.lower() not in landmark_name.lower():
        query = f"{landmark_name}, {detected_city}"
    else:
        query = landmark_name
        
    if query in geocode_cache:
        return geocode_cache[query]
    
    try:
        # Rate limit Nominatim to 1 request per second
        time.sleep(1.1)
        location = geolocator.geocode(query)
        if location:
            result = (location.latitude, location.longitude, "high")
        else:
            result = (None, None, "low")
        geocode_cache[query] = result
        return result
    except (GeocoderTimedOut, GeocoderServiceError):
        return (None, None, "low")

def geocode_location(landmark_name: str, detected_city: str = None):
    """Routes to LocationIQ if API key exists, otherwise Nominatim."""
    if LOCATIONIQ_API_KEY:
        # Try LocationIQ first
        lat, lng, conf = geocode_location_locationiq(landmark_name, detected_city)
        if lat is not None:
            return lat, lng, conf
            
    # Fallback to Nominatim
    return geocode_location_nominatim(landmark_name, detected_city)

def resolve_location(location_text: str, landmarks: list, detected_city: str = None):
    """
    Two-pass geocoding fallback chain:
    Pass 1: Direct geocoding via Nominatim/LocationIQ
    Pass 2: AI-based landmark name extraction, then re-query Nominatim
    Returns (lat, lng, loc_confidence) for cluster.py
    """
    if not landmarks and not location_text:
        # If we have a city but no landmark, geocode the city centroid
        if detected_city:
            reg_loc = geocode_location(detected_city, None)
            return reg_loc[0], reg_loc[1], "low"
        return None, None, "low"
    
    # PASS 1: Direct geocoding
    if landmarks:
        for landmark in landmarks:
            lat, lng, conf = geocode_location(landmark, detected_city)
            if lat is not None and conf == "high":
                return lat, lng, "high"
                
    if location_text:
         lat, lng, conf = geocode_location(location_text, detected_city)
         if lat is not None and conf == "high":
             return lat, lng, "high"
         # If we got coordinates but with low confidence, continue to pass 2
    
    # PASS 2: AI-based landmark name extraction for hyper-local vernacular
    # Only triggered if confidence is low or coordinates are missing
    if location_text and (not location_text or (lat is None and lng is None)):
        print(f"[Geocoding Pass 2] Using AI to extract canonical landmark from: {location_text}")
        
        # Use AI to extract canonical landmark name
        ai_result = normalize_landmark_with_ai(location_text, detected_city)
        primary_landmark = ai_result.get("primary_landmark")
        area = ai_result.get("area", detected_city)
        
        if primary_landmark and primary_landmark != location_text:
            print(f"[Geocoding Pass 2] AI extracted landmark: {primary_landmark} in {area}")
            
            # Re-query Nominatim with canonical landmark
            lat, lng, conf = geocode_location(primary_landmark, area)
            if lat is not None:
                return lat, lng, "medium"  # Medium confidence (AI-assisted)
    
    # Final fallback: Use city centroid if available
    if detected_city:
        reg_loc = geocode_location(detected_city, None)
        return reg_loc[0], reg_loc[1], "low"

    return None, None, "low"

def normalize_landmark_with_ai(location_text: str, detected_city: str = None) -> dict:
    """
    Use AI to normalize Indian landmark descriptions.
    Returns structured landmark information.
    """
    try:
        from google.genai import types

        prompt = f"""
        Analyze this Indian location description and extract:
        1. Primary landmark (main place name)
        2. Secondary landmarks (nearby places)
        3. Spatial relationship (near, behind, opposite, etc.)
        4. Specific direction (north, south, east, west, etc.)
        5. City/area if mentioned

        Location: "{location_text}"
        City context: {detected_city or "Not specified"}

        Return as JSON:
        {{
            "primary_landmark": "string",
            "secondary_landmarks": ["string"],
            "spatial_relationship": "string",
            "direction": "string",
            "area": "string"
        }}
        """

        response = genai_client.models.generate_content(
            model='gemini-3.8-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.0,
            ),
        )

        import json
        return json.loads(response.text)
    except Exception as e:
        print(f"AI landmark normalization error: {e}")
        return {"primary_landmark": location_text, "secondary_landmarks": [], "spatial_relationship": None, "direction": None, "area": detected_city}

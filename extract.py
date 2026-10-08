import os
import json
import hashlib
from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from pathlib import Path

# Define the expected JSON schema using Pydantic
class ExtractionResult(BaseModel):
    category: Literal['emergency', 'update', 'rumor', 'noise'] = Field(description="Classification of the message.")
    confidence: float = Field(description="Confidence score from 0.0 to 1.0", ge=0.0, le=1.0)
    location_text: Optional[str] = Field(description="Verbatim location text mentioned.")
    city_or_region: Optional[str] = Field(description="Extracted city or state if mentioned, else null.")
    landmarks: List[str] = Field(description="List of landmarks extracted.", default_factory=list)
    people_count: Optional[int] = Field(description="Number of people affected, if mentioned.")
    count_is_approx: bool = Field(description="True if the people count is approximate.", default=False)
    resource: Optional[str] = Field(description="Resource needed (e.g., medical, rescue, food, pump).")
    vulnerable: List[str] = Field(description="Vulnerable people mentioned (e.g., elderly, children, diabetic).", default_factory=list)
    urgency: Literal['low', 'medium', 'high', 'critical'] = Field(description="Assessed urgency.")
    status_hint: Literal['reported', 'rescue_arrived', 'rescued', 'ongoing', 'none'] = Field(description="Hint about the current status.")
    summary: str = Field(description="A brief 1-2 sentence summary of the report.")
    # Image verification fields
    image_verified: bool = Field(description="Whether an image was verified as an emergency scene.", default=False)
    damage_level: Optional[Literal['Minor', 'Severe', 'Catastrophic']] = Field(description="Visible damage level from image verification.", default=None)
    visible_landmarks: List[str] = Field(description="Landmarks visible in the image.", default_factory=list)

# Assumes GEMINI_API_KEY is set in the environment
client = genai.Client()

def get_cache_key(text: str, context: List[str]) -> str:
    content = text + "|".join(context)
    return hashlib.md5(content.encode()).hexdigest()

def verify_image_with_vision(image_path: str) -> dict:
    """
    Verify if an image matches an emergency scene using Gemini Vision.
    Extracts damage level and visible landmarks.
    """
    if not os.getenv("GEMINI_API_KEY"):
        return {"verified": False, "error": "Gemini API not configured"}
    
    path = Path(image_path)
    if not path.exists():
        return {"verified": False, "error": "Image file not found"}
    
    try:
        # Upload image to Gemini
        image_file = client.files.upload(file=str(path))
        
        prompt = """
        Analyze this image and determine:
        1. Is this an emergency scene (flood, fire, structural damage, accident, etc.)?
        2. What is the damage level (Minor, Severe, or Catastrophic)?
        3. What landmarks or location indicators are visible?
        
        Return your answer in this exact JSON format:
        {
            "is_emergency_scene": true/false,
            "damage_level": "Minor/Severe/Catastrophic",
            "visible_landmarks": ["landmark1", "landmark2"],
            "description": "brief description"
        }
        """
        
        response = client.models.generate_content(
            model='gemini-3.8-flash',
            contents=[image_file, prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.0,
            ),
        )
        
        # Cleanup uploaded file
        try:
            client.files.delete(name=image_file.name)
        except Exception:
            pass
        
        result = json.loads(response.text)
        return {
            "verified": result.get("is_emergency_scene", False),
            "damage_level": result.get("damage_level"),
            "visible_landmarks": result.get("visible_landmarks", []),
            "description": result.get("description", "")
        }
        
    except Exception as e:
        return {"verified": False, "error": str(e)}

def extract_information(text: str, context_messages: List[str] = None, image_path: str = None) -> ExtractionResult:
    """
    Extracts structured emergency information from a message text using Gemini.
    Optionally verifies an attached image using Gemini Vision.
    """
    if context_messages is None:
        context_messages = []
    
    # Verify image if provided
    image_verification = None
    if image_path:
        image_verification = verify_image_with_vision(image_path)
        if not image_verification.get("verified"):
            print(f"Image verification failed: {image_verification.get('error', 'Not an emergency scene')}")
    
    # Add image context to prompt if verified
    image_context = ""
    if image_verification and image_verification.get("verified"):
        image_context = f"""
        ATTACHED IMAGE VERIFICATION:
        - Damage Level: {image_verification.get('damage_level')}
        - Visible Landmarks: {', '.join(image_verification.get('visible_landmarks', []))}
        - Description: {image_verification.get('description')}
        """
        
    prompt = f"""
    You are an AI Emergency Response Assistant. Extract structured information from the following report.
    Do not invent values. If information is missing, use null or empty lists.
    Keep the location verbatim. Treat 'forwarded' or 'unverified' in the text as rumors unless confirmed.
    
    IMPORTANT CATEGORY RULES:
    1. If the report contains phrases like "forwarded as received", "heard a rumor", or is clearly unverified hearsay, you MUST classify it strictly as 'rumor' and set urgency to 'low'.
    2. If the report is a general question (e.g. "when will power return?", "food delivery"), classify it strictly as 'noise'.
    3. If the report is a genuine, direct observation of Fire, Medical, Traffic, Police, or Hazard, classify it as 'emergency'.
    
    {image_context}
    
    Context messages (previous messages in the same stage for resolving short replies like 'same place'):
    {json.dumps(context_messages)}
    
    Current Report to analyze:
    "{text}"
    """
    
    # We use gemini-3.8-flash for fast and reliable structured extraction
    response = client.models.generate_content(
        model='gemini-3.8-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ExtractionResult,
            temperature=0.0,
        ),
    )
    
    result = ExtractionResult.model_validate_json(response.text)
    
    # Add image verification data if available
    if image_verification and image_verification.get("verified"):
        result.image_verified = True
        result.damage_level = image_verification.get("damage_level")
        result.visible_landmarks = image_verification.get("visible_landmarks", [])
    
    return result

if __name__ == "__main__":
    # Quick test
    test_msg = "6 people trapped near the Velachery station. Water rising. Elderly person is diabetic."
    print(f"Testing extraction on: '{test_msg}'\n")
    try:
        res = extract_information(test_msg)
        print(res.model_dump_json(indent=2))
    except Exception as e:
        print("Error:", e)

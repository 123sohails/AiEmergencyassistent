from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class IncidentEvent(BaseModel):
    timestamp: str
    event_type: str # e.g., 'created', 'status_changed', 'count_changed', 'escalated'
    detail: str
    message_id: str

class Incident(BaseModel):
    id: str
    status: str = "active" # active, rescue_in_progress, resolved
    urgency: str = "low" # low, medium, high, critical
    people_count: Optional[int] = None
    primary_resource: Optional[str] = None
    vulnerable: List[str] = Field(default_factory=list)
    
    first_seen: str
    last_updated: str
    
    # Location
    location_text: str = ""
    lat: Optional[float] = None
    lng: Optional[float] = None
    loc_confidence: str = "low"
    
    # Text Tracking
    summary: str = ""
    embedding: Optional[List[float]] = None
    
    message_ids: List[str] = Field(default_factory=list)
    events: List[IncidentEvent] = Field(default_factory=list)
    
    def add_event(self, event_type: str, detail: str, message_id: str, timestamp: str):
        self.events.append(IncidentEvent(
            timestamp=timestamp,
            event_type=event_type,
            detail=detail,
            message_id=message_id
        ))
        self.last_updated = timestamp

def update_incident_state(incident: Incident, extraction: dict, message_id: str, timestamp: str):
    """
    Updates the incident state based on new extraction evidence.
    """
    # 1. Update status
    status_hint = extraction.get("status_hint")
    if status_hint == "rescue_arrived" and incident.status == "active":
        incident.status = "rescue_in_progress"
        incident.add_event("status_changed", "Rescue in progress", message_id, timestamp)
    elif status_hint == "rescued" and incident.status != "resolved":
        incident.status = "resolved"
        incident.add_event("status_changed", "Incident resolved", message_id, timestamp)

    # 2. Update people count
    new_count = extraction.get("people_count")
    if new_count is not None:
        if incident.people_count is None or new_count > incident.people_count:
            incident.people_count = new_count
            incident.add_event("count_changed", f"Count updated to {new_count}", message_id, timestamp)

    # 3. Escalation / Urgency
    urgency_levels = {"low": 1, "medium": 2, "high": 3, "critical": 4}
    new_urgency = extraction.get("urgency")
    if new_urgency and urgency_levels.get(new_urgency, 0) > urgency_levels.get(incident.urgency, 0):
        incident.urgency = new_urgency
        incident.add_event("escalated", f"Urgency increased to {new_urgency}", message_id, timestamp)
        
    # 4. Vulnerable people
    new_vuln = extraction.get("vulnerable", [])
    for v in new_vuln:
        if v not in incident.vulnerable:
            incident.vulnerable.append(v)
            incident.add_event("vulnerable_added", f"Added vulnerable: {v}", message_id, timestamp)
            
    # Update resource if not set
    if incident.primary_resource is None and extraction.get("resource"):
        incident.primary_resource = extraction.get("resource")
        
    if message_id not in incident.message_ids:
        incident.message_ids.append(message_id)

import pandas as pd
import random
from datetime import datetime, timedelta

def generate_full_dataset(count=100, output_file="emergency_calls_large.csv"):
    categories = ["Medical", "Fire", "Traffic", "Police", "Hazard"]
    urgencies = ["Low", "Medium", "High", "Critical"]
    
    transcripts_map = {
        "Medical": [
            "Dispatcher: 911. Caller: Patient experiencing severe chest pain and dizziness.",
            "Dispatcher: Emergency medical. Caller: Unresponsive individual found on the sidewalk.",
            "Dispatcher: 911 dispatch. Caller: Severe asthma attack, inhaler is not working."
        ],
        "Fire": [
            "Dispatcher: 911 fire department. Caller: Smoke seen blowing from the garage roof.",
            "Dispatcher: Where is the fire? Caller: Brush fire spreading near the highway fence.",
            "Dispatcher: 911. Caller: Electrical fire sparking inside the wall outlet."
        ],
        "Traffic": [
            "Dispatcher: 911 traffic. Caller: Two-car rear-end crash on the bridge.",
            "Dispatcher: Emergency services. Caller: Vehicle hit a guardrail, road blocked.",
            "Dispatcher: 911 dispatch. Caller: Debris fallen off a truck causing a hazard."
        ],
        "Police": [
            "Dispatcher: 911 emergency. Caller: Suspicious person trying car door handles.",
            "Dispatcher: Police dispatch. Caller: Shoplifting suspect fleeing on foot toward Main St.",
            "Dispatcher: 911. Caller: Vandalism in progress at the public park."
        ],
        "Hazard": [
            "Dispatcher: 911. Caller: Water main burst flooding the basement and road.",
            "Dispatcher: Hazard dispatch. Caller: Chemical odor reported in the basement area.",
            "Dispatcher: Emergency services. Caller: Tree branch fell onto active power lines."
        ]
    }

    data = []
    start_time = datetime(2026, 10, 8, 8, 0, 0)

    for i in range(1, count + 1):
        call_id = f"EMG-2026-{i:04d}"
        timestamp = (start_time + timedelta(seconds=random.randint(10, 50000))).strftime("%Y-%m-%d %H:%M:%S")
        phone = f"+1555{random.randint(1000000, 9999999)}"
        lat = round(37.7000 + random.uniform(0.0000, 0.1000), 4)
        lon = round(-122.5000 + random.uniform(0.0000, 0.1000), 4)
        cat = random.choice(categories)
        urgency = random.choice(urgencies)
        duration = random.randint(45, 300)
        audio = f"call_{i:04d}.wav"
        transcript = random.choice(transcripts_map[cat])

        data.append([call_id, timestamp, phone, lat, lon, cat, urgency, duration, audio, transcript])

    df = pd.DataFrame(data, columns=[
        "id", "time", "sender", "lat", "lng", 
        "category", "urgency_level", "duration_sec", "audio_file", "text"
    ])
    
    df.to_csv(output_file, index=False)
    print(f"Generated {count} records in '{output_file}'.")

if __name__ == "__main__":
    generate_full_dataset(100)

import json
from pathlib import Path
from store import insert_test_incidents, reset_session

# Load test incidents
with open('test_incidents.json', 'r') as f:
    test_incidents = json.load(f)

# Reset and insert
reset_session('dataset')
insert_test_incidents(test_incidents)

print(f"Loaded {len(test_incidents)} test incidents into database")

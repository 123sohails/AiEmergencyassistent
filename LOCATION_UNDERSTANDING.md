# Location Understanding Implementation

## Challenge
Indian emergency reports often use familiar landmarks, directions, nearby buildings, roads, stations, schools, shops, or junctions instead of clean street addresses.

### Example Problem
- Report A: "Near the Velachery MRTS west gate"
- Report B: "Behind the MRTS station, on the Vijayanagar side"
- Report C: "Opposite the medical shop near the station backside road"

**Challenge**: Understand that these may refer to the same area while avoiding over-merging genuinely different incidents.

## Current Implementation

### 1. Semantic Embeddings (Primary Method)
- **What**: Uses Gemini's `text-embedding-004` model
- **How**: Converts location descriptions into vector embeddings
- **Why**: Captures semantic meaning - "MRTS station" and "metro station" are semantically similar
- **Weight**: 40% of clustering score

### 2. Geographic Distance (Secondary Method)
- **What**: Calculates Euclidean distance between coordinates
- **How**: Geocodes locations using LocationIQ/Nominatim
- **Threshold**: ~550m (0.005 degrees)
- **Weight**: 40% of clustering score

### 3. Landmark Text Similarity (Fallback Method)
- **What**: Compares location text using Jaccard similarity
- **How**:
  - Removes stopwords (near, behind, opposite, the, a, etc.)
  - Extracts meaningful terms (landmarks, area names)
  - Calculates Jaccard similarity (intersection/union)
  - Boosts score if proper nouns overlap
- **Use Case**: When embeddings are unavailable or unclear
- **Weight**: 10% of clustering score

### 4. Resource Matching (Context)
- **What**: Compares resource types (medical, rescue, fire, etc.)
- **How**: Exact string match (case-insensitive)
- **Weight**: 10% of clustering score

## Test Results

### Improved Clustering Behavior

| Test Case | Score | Result | Interpretation |
|-----------|-------|--------|----------------|
| "Near Velachery MRTS" vs "Near MRTS station Velachery" | 0.97 | ✅ Merge | Same location, different wording |
| "Behind Velachery station" vs "Near Velachery MRTS" | 0.63 | ✅ Merge | Same area, different direction |
| "T Nagar signal" vs "T Nagar junction" | 0.63 | ✅ Merge | Same location, different landmark type |
| "Near Chennai Central" vs "Near Central station Chennai" | 1.00 | ✅ Merge | Same location, word order change |
| "Near Marina Beach" vs "Near Besant Nagar Beach" | 0.55 | ⚠️ Borderline | Different beaches, similar structure |
| "Near Velachery MRTS" vs "Opposite medical shop" | 0.00 | ❌ No Merge | Different locations |
| "Near MRTS station" vs "Opposite medical shop" | 0.00 | ❌ No Merge | No common terms |

## Key Features

### ✅ What Works Well
1. **Semantic Understanding**: Embeddings understand that "MRTS" and "metro" are related
2. **Proper Noun Recognition**: Area names (Velachery, T Nagar) are given weight
3. **Stopword Removal**: Filters out directional words that add noise
4. **Geographic Fallback**: Coordinates provide hard constraints
5. **Multi-factor Scoring**: Combines multiple signals to avoid over-merging

### ⚠️ Limitations
1. **No Spatial Relationship Parsing**: Doesn't understand "behind" vs "opposite" geographically
2. **No Landmark Database**: Doesn't have pre-known landmark relationships
3. **Fixed Distance Threshold**: 550m may not work for all urban densities
4. **Ambiguous Similarity**: "Marina Beach" vs "Besant Nagar Beach" score 0.55 (borderline)

## Recommendations for Improvement

### 1. AI-Based Landmark Normalization
Use Gemini to parse spatial relationships:
```python
# Extract: primary landmark, spatial relationship, direction
normalize_landmark_with_ai("Near the Velachery MRTS west gate")
# Returns: {primary_landmark: "Velachery MRTS", spatial: "near", direction: "west"}
```

### 2. Landmark Database
Pre-load known landmarks (MRTS stations, major junctions) with their coordinates and relationships.

### 3. Adaptive Distance Thresholds
Use landmark type to adjust thresholds:
- Stations: 1km (large area)
- Shops: 100m (small area)
- Junctions: 500m (medium area)

### 4. Hierarchical Clustering
First cluster by area (city/zone), then by specific location within that area.

## Conclusion

The current implementation **addresses the location understanding challenge** through:
- ✅ Semantic embeddings that understand related terms
- ✅ Geographic distance as a hard constraint
- ✅ Text similarity as a fallback
- ✅ Multi-factor scoring to avoid over-merging

While not perfect, it handles the Indian landmark challenge better than naive keyword matching and satisfies the hackathon requirements.

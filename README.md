# AI Emergency Response Assistant 🚨

**Turning raw disaster chaos into clear, explainable, and actionable incidents.**

## 🛑 The Problem
During a disaster, emergency control rooms are flooded with reports from multiple channels (WhatsApp, Twitter, calls, SMS). These reports are messy, duplicated, contradictory, and often lack exact coordinates. 

Responders shouldn't have to read 450 messages to understand what is happening. They need to know: **What is the crisis, where is it, how urgent is it, and who needs what?**

## 💡 Our Solution
We built an **AI Intelligence Pipeline** that acts as a cognitive filter for emergency dispatchers. Our system ingests unstructured, multi-modal chaos and distills it into a clean, evolving dashboard of live incidents. 

Unlike basic AI wrappers, our system possesses **Core Memory (Sequential Awareness)**. It doesn't just drop 400 pins on a map; it understands when a new message is an update to an existing incident, merging duplicates and escalating urgency dynamically.

---

## ⚙️ The Architecture Pipeline

1. **Ingest & Normalize (`adapters.py`)**
   - A universal adapter that ingests CSV, JSON, Excel, and messy WhatsApp `.txt` exports.
   - Automatically deduplicates exact texts to save LLM compute and latency.
   
2. **AI Extraction (`extract.py`)**
   - Powered by **Gemini**.
   - Extracts structured evidence with a strict schema: `Location`, `People Count`, `Resource Needed`, `Vulnerable Status`, and `Urgency`.
   - Filters out noise, general queries, and unverified rumors.

3. **Intelligent Location Resolution (`locate.py`)**
   - Handles messy, Indian-style landmark descriptions (e.g., *"behind MRTS west gate"*).
   - Resolves locations in layers: exact matching -> Nominatim Geocoding -> regional fallbacks.
   - Preserves an AI Confidence Score for the responder.

4. **Clustering & Memory (`cluster.py` & `tracker.py`)**
   - **The Engine:** We score incoming messages against open incidents using geographic distance (`geopy`) and **Semantic Cosine Similarity** (`gemini-text-embedding-004`).
   - Tracks the state machine: `Active` ➡️ `Rescue in Progress` ➡️ `Resolved`.
   - Maintains a historical event timeline as counts and urgency change.

5. **Explainable Dashboard (`app.py`)**
   - Built with Streamlit and Folium.
   - **Metrics:** Instantly see how much noise was filtered.
   - **Explainability Panel:** Responders don't trust black boxes. Our UI shows exactly *Why Merged?* (Location Match + Text Similarity) and exposes the original evidence.

---

## 🏆 Key Differentiators (Why we win)

*   **Sequential Awareness:** We don't over-merge or blindly create tickets. We track incidents over time (Phase 1 to Phase 4).
*   **Explainable AI:** Our UI shows the exact reasoning and evidence for every grouped incident.
*   **Universal Ingestion:** Drag and drop *any* file format (CSV, Excel, TXT, JSON) directly into the UI.
*   **No Pytorch Bloat:** We leverage Gemini for both structured extraction and semantic embeddings, making our app lightning fast without requiring massive local GPU dependencies.

---

## 🚀 Setup & Execution

### Prerequisites
Make sure you have Python 3.9+ installed. You also need a Google Gemini API Key.

### Installation
```bash
# Navigate to the project directory
cd emergency_assistant

# Install the required dependencies
pip install -r requirements.txt
```

### Running the System
1. Set your Gemini API key in your terminal:
   ```bash
   # Windows
   set GEMINI_API_KEY=your_gemini_api_key_here
   
   # Mac/Linux
   export GEMINI_API_KEY=your_gemini_api_key_here
   ```
2. Start the Streamlit Dashboard:
   ```bash
   streamlit run app.py
   ```
3. **Demo:** Drag and drop the dataset files into the sidebar, or manually type in simulated emergency reports to watch the map evolve!

---

*Built for the 24-Hour Tech Fest Hackathon.*

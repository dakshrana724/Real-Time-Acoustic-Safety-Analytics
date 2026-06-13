# Monitor real-time audio for in-transit safety alerts

Problem mentioned in (Ai-google project  https://cloud.google.com/blog/products/ai-machine-learning/real-world-gen-ai-use-cases-with-technical-blueprints 
)

This repository hosts a production-grade, event-driven intelligent system designed to monitor real-time vehicle cabin audio for in-transit safety alerts and crises. 
The architecture couples local machine learning optimization at the edge with an asynchronous multi-cloud cascading validation framework and an automated telephony emergency dispatch gateway.

---

##  Architectural Core Pillars

### 1. Edge AI Triage Layer

To mitigate the financial and quota limitations of cloud LLM web requests, the system implements a local natural language processing (NLP) model. 
Ambient cabin text segments are passed first through a local classifier; if labeled benign, the pipeline resolves the thread instantly with zero external overhead. 
The system only utilizes high-token cloud APIs when a localized alert threshold is crossed.

### 2. Universal Circuit Breaker

The backend eliminates defensive token-filtering by using a broad error-handling wrapper.
If the primary cloud engine (Gemini) fails for any structural or network reason, the system trips a circuit breaker and automatically routes traffic down to an alternative open-source runtime cluster
(Groq running a Llama 3.1 architecture) within milliseconds, preventing downstream unhandled crashes.

### 3. Asynchronous Telephony Gateway

Placing real-time cellular network calls or dispatching international SMS text alerts introduces massive synchronous I/O blocks.
To keep the streaming microphone interface alive with zero latency or lag, verified threat states are handed off asynchronously to an isolated background thread running a custom Twilio SDK runtime worker.

### 4. Client Lifecycle Resiliency

Optimized for aggressive Chromium environments (like Vivaldi), the frontend employs a memory teardown loop on the native Web Speech API instance , Suggestion : Use chrome or edge .
If a network disruption drops the persistent state of the underlying socket connection, the client cleanses the speech handler allocations and triggers a recursive re-instantiation from scratch rather than forcing a restart on a hung thread.

---

##  Project Architecture

```text
safe-audio-backend/
│
├── venv/                      # Isolated virtual dependency directory
├── train_model.py             # Pre-processing & edge model training logic
├── app.py                     # Primary WebSocket server & dispatch loop
├── vectorizer.pkl             # Serialized local text vectorizer weights
├── safety_model.pkl           # Serialized edge ML model weights
└── .env                       # Encrypted structural credential keys

```

>  **Directory Architecture Rule:** All custom scripts, server definitions, and localized models must live outside the `venv` folder, which is strictly preserved for housing package manager requirements.
> 
> 

---

##  Step-by-Step Installation & Setup

### 1. Set Up the Python Virtual Environment

On Windows systems, it is vital to utilize an isolated virtual environment so local development extensions do not conflict with your global operating system installations.

Open the internal terminal panel inside VS Code (`Ctrl + ~`) and execute:

```powershell
python -m venv venv

```

* 
**Edge Case Fallback:** If your localized shell path configurations throw error flags during generation, bypass them by invoking the direct local binary path of your Python executable:


```powershell
"C:\Users\Dakshrana\AppData\Local\Programs\Python\Python313\python.exe" -m venv venv

```




To activate the virtual environment folder, run the script policy:

```powershell
.\venv\Scripts\Activate.ps1

```

(Note: For shell standard profiles, execute `.\venv\bin\Activate.ps1` instead ). A green `(venv)` prefix will appear on your terminal path when successfully locked down.

### 2. Install Project Dependencies

With the virtual environment actively engaged, install the underlying edge machine learning frameworks followed by the real-time networking and communication web layers:

```powershell
pip install scikit-learn numpy flask flask-socketio simple-websocket google-generativeai twilio

```



### 3. Configure Local Secret Environment Variables

Create a protected file named `.env` in the root backend directory and configure your multi-cloud API tokens and Twilio numbers:

```text
GEMINI_API_KEY=your_primary_gemini_api_key_here
GROQ_API_KEY=your_backup_groq_api_key_here

TWILIO_ACCOUNT_SID=your_twilio_account_sid_string
TWILIO_AUTH_TOKEN=your_private_twilio_auth_token_string
TWILIO_PHONE_NUMBER=your_assigned_trial_sender_number
EMERGENCY_CONTACT_NUMBER=your_verified_receiver_phone_number

```

---

## 🚀 Execution Guide

### Phase A: Compile and Start the Backend Runtime

1. Compile and train the edge text classification model weights:


```powershell
python train_model.py

```



2. Start up the real-time asynchronous multi-cloud Python WebSocket server:


```powershell
python app.py

```






### Phase B: Launch the Reactive Telemetry Dashboard

1. Open a secondary terminal split window and change directories into the web dashboard app:


```powershell
cd audio-dashboard

```





2. Boot up the local browser development infrastructure engine:


```powershell
npm run dev

```





3. Open the displayed local server address in your web browser, click **Allow Browser Location Permissions**, and engage **Activate Continuous Background Monitoring** to start the pipeline execution.

---

## 📝 Engineering Retrospective & Resolution History

* 
**The Sluggish Continuous Ingestion Bottleneck:** Initial prototype phases forwarded raw continuous conversational audio slices straight to a cloud framework.
  Under persistent streaming conditions, this hit free-tier rate limits rapidly. Forcing the audio tracker to listen only to single "one-click" manual blocks was attempted
  but proved impractical for hand-free driving safety applications.
   Building a custom local machine learning triage model solved this by keeping safe conversations local and executing cloud API calls only when distress markers are matched.


* **The Vivaldi Audio Interface Lockup:** Long-term cross-browser reliability testing in Vivaldi revealed a fatal interface freeze issue. When the cloud pipeline encountered transient server faults, the backend exception was parsed looking strictly for the word "quota". If a non-quota error fired, it crashed the active Flask-SocketIO event loop, causing Vivaldi to aggressively suspend the silent browser microphone process. This was fully resolved by wrapping the cloud router in a universal `try/except Exception` circuit fallback and decoupling the frontend microphone recycling logic inside `recognition.onend`.
* **The Decommissioned Model Outage:** Simulated failure drills revealed a secondary error when traffic crashed through to the Groq backup engine. The backend was targeting the `llama3-8b-8192` framework, which Groq had officially decommissioned and removed from its hardware clusters. Updating the model ID to the active production model `llama-3.1-8b-instant` completely resolved the handshake error.
* **The Twilio Multi-Segment Error 30044:** Early integration designs dispatched highly descriptive, structured, and emoji-decorated alert formats. This metadata caused the SMS payload text to expand across 6 distinct international segments. Twilio's free trial layer blocks multi-segment concatenated SMS delivery to international regions to protect account balances. Condensing the notification template down into a single, compact segment under 160 characters bypassed the length ceiling, allowing live text tracking links to deliver instantly.

import os
import pickle
from flask import Flask
from flask_socketio import SocketIO, emit
from dotenv import  load_dotenv # 🚀 Import dotenv loader
import google.generativeai as genai
# from groq import Groq

# 💥 Load environment variables from the local .env file
load_dotenv()

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# 🔐 Safely grab the credentials from the operating system environment
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Initialize Cloud Clients using the secure keys
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel("gemini-2.5-flash")
# groq_client = Groq(api_key=GROQ_API_KEY)

# 🧠 2. Load the Local Edge Machine Learning Layer (Tier 1 Filter)
print("⚙️ Loading custom local Natural Language Processing models...")
try:
    with open("vectorizer.pkl", "rb") as f:
        vectorizer = pickle.load(f)
    with open("safety_model.pkl", "rb") as f:
        local_model = pickle.load(f)
    print("🧠 Local ML Model and Vectorizer armed successfully!")
except Exception as e:
    print(f"❌ Failed to load local .pkl assets: {e}")

@app.route('/')
def index():
    return "Hybrid Edge-Cloud Safety Engine Active."

@socketio.on('connect')
def handle_connect():
    print("⚡ React continuous text-stream connected!")

@socketio.on('disconnect')
def handle_disconnect():
    print("❌ Client disconnected.")

# 🔄 3. Continuous Real-Time Text Stream Event
@socketio.on('live_transcript')
def handle_live_transcript(data):
    transcript = data.get('text', '').strip()
    if not transcript:
        return

    print(f"🎙️ Ingestion: \"{transcript}\"")

    try:
        # 🧪 Tier 1: Local Edge Machine Learning Evaluation
        X_transformed = vectorizer.transform([transcript])
        local_prediction = local_model.predict(X_transformed)[0]

        # Class 0 = Safe, Class 1 = Potential Distress
        if local_prediction == 0:
            print("✅ [Tier 1 Edge]: Safe Conversation. Bypassing Cloud APIs.")
            emit('chunk_processed', {'status': 'processed', 'info': 'Safe (Local Execution)'})
        
        else:
            print("⚠️ [Tier 1 Edge]: Potential Distress Detected! Escalating to Tier 2 Cloud...")
            
            # 🌤️ Tier 2: Cloud LLM Contextual Validation
            prompt = (
                f"You are a validation layer analyzing a flagged vehicle cabin transcript.\n"
                f"Transcript to evaluate: \"{transcript}\"\n\n"
                f"Determine if this is an actual, active emergency or crisis, or just a false positive (like singing a song or casual talking).\n"
                f"Reply strictly in this exact format:\n"
                f"STATUS: [RED if an active crisis/threat, GREEN if it is a false positive safe context]\n"
                f"REASON: [A 5-word summary of your contextual decision]"
            )
            
            response = gemini_model.generate_content(prompt)
            result_text = response.text.strip().upper().replace("*", "")
            
            print(f"🤖 [Tier 2 Gemini Cloud] Evaluation -> \n{result_text}\n")
            
            # Fire alerts over WebSockets based on deep validation
            if "STATUS: RED" in result_text or "RED" in result_text.split("STATUS:")[-1]:
                print("🚨 CRITICAL ALERT BROADCASTED TO FRONTEND!")
                reason = result_text.split("REASON:")[-1].strip() if "REASON:" in result_text else "Crisis confirmed"
                emit('safety_alert', {'status': 'RED', 'info': reason}, broadcast=True)
            else:
                print("🍃 Cloud verification determined a False Positive. System Clear.")
                emit('chunk_processed', {'status': 'processed', 'info': 'False Positive (Cleared by Cloud)'})

    except Exception as e:
        print(f"⚠️ Hybrid Pipeline Error: {e}")
        emit('chunk_processed', {'status': 'error', 'message': str(e)})

if __name__ == '__main__':
    print("🚀 Starting Hybrid Cascading Audio-Text Backend Server")
    socketio.run(app, host='127.0.0.1', port=5000, debug=True)
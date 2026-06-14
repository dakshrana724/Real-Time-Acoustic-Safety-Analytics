import os
import pickle
import threading 
from flask import Flask
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv
import google.generativeai as genai
from groq import Groq
from twilio.rest import Client  

load_dotenv()

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE = os.getenv("TWILIO_PHONE_NUMBER")
EMERGENCY_CONTACT = os.getenv("EMERGENCY_CONTACT_NUMBER")

genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel("gemini-2.5-flash")
groq_client = Groq(api_key=GROQ_API_KEY)
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN) if TWILIO_ACCOUNT_SID else None


print(" Loading custom local Natural Language Processing models... Ruko zra sabar karo")
try:
    with open("vectorizer.pkl", "rb") as f:
        vectorizer = pickle.load(f)
    with open("safety_model.pkl", "rb") as f:
        local_model = pickle.load(f)
    print(" Local ML Model and Vectorizer armed successfully!")
except Exception as e:
    print(f" Failed to load local .pkl assets: {e}")



def execute_emergency_dispatch(transcript, lat, lng, provider, reason):
    print(" Initializing background emergency dispatch worker...")
    if not twilio_client:
        print("Dispatch Aborted: Twilio client credentials missing from .env")
        return

    maps_link = f"https://www.google.com/maps?q={lat},{lng}" if lat and lng else "Location unavailable"

  
    sms_body = f"CRITICAL: {reason}. Driver said: '{transcript}'. Location: http://maps.google.com/?q={lat},{lng}"

    
    twiml_voice_script = (
        f"<Response>"
        f"<Say voice='en-US-Standard-C' speed='0.95'>"
        f"Emergency dispatch alert triggered by vehicle cabin monitoring. "
        f"A critical safety crisis was verified using {provider}. "
        f"The system logged the following statement. {transcript}. "
        f"An emergency text message containing the driver's precise Google Maps GPS location has been sent to your phone. "
        f"Please check your messages and take immediate action."
        f"</Say>"
        f"</Response>"
    )

    try:
        
        print(" Dispatching outbound security text message...")
        message = twilio_client.messages.create(
            body=sms_body,
            from_=TWILIO_PHONE,
            to=EMERGENCY_CONTACT
        )
        print(f"✅ Text sent successfully! SID: {message.sid}")

        
        print("Initiating outbound automated emergency call sequence...")
        call = twilio_client.calls.create(
            twiml=twiml_voice_script,
            from_=TWILIO_PHONE,
            to=EMERGENCY_CONTACT
        )
        print(f"✅ Voice dispatch established successfully! SID: {call.sid}")

    except Exception as dispatch_err:
        print(f"❌ Telephony Dispatch Pipeline Failure: {dispatch_err}")


@app.route('/')
def index():
    return "Hybrid Safety Engine with Dispatch active."

@socketio.on('connect')
def handle_connect():
    print("⚡ React continuous text-stream connected!")

@socketio.on('live_transcript')
def handle_live_transcript(data):
    transcript = data.get('text', '').strip()
    if not transcript:
        return

    lat = data.get('lat')
    lng = data.get('lng')

    print(f"\n🎙️ Ingestion: \"{transcript}\"")
    print(f"📍 Location Coordinates -> Lat: {lat}, Lng: {lng}")

    try:
        X_transformed = vectorizer.transform([transcript])
        local_prediction = local_model.predict(X_transformed)[0]

        if local_prediction == 0:
            print("✅ [Tier 1 Edge]: Safe Conversation. Bypassing Cloud APIs.")
            emit('chunk_processed', {'status': 'processed', 'info': 'Safe (Local Execution)'})
        
        else:
            print("⚠️ [Tier 1 Edge]: Potential Distress Detected! Escalating to Tier 2 Cloud...")
            
            prompt = (
                f"You are a validation layer analyzing a flagged vehicle cabin transcript.\n"
                f"Transcript to evaluate: \"{transcript}\"\n\n"
                f"Determine if this is an actual, active emergency or crisis, or just a false positive.\n"
                f"Reply strictly in this exact format:\n"
                f"STATUS: [RED if an active crisis/threat, GREEN if it is a false positive safe context]\n"
                f"REASON: [A 5-word summary of your contextual decision]"
            )
            
            result_text = ""
            provider_used = ""

            try:
                print(" Routing to Primary Cloud Provider (Gemini)...")
                response = gemini_model.generate_content(prompt)
                result_text = response.text.strip().upper().replace("*", "")
                provider_used = "Gemini Primary"
            except Exception as gemini_err:
                print(f"\n [CIRCUIT BREAKER ACTIVE]: Gemini hit a wall: {gemini_err}")
                print(" Instantly routing traffic to Secondary Cloud Circuit (Groq Llama-3)...")
                try:
                    chat_completion = groq_client.chat.completions.create(
                        messages=[{"role": "user", "content": prompt}],
                        model="llama-3.1-8b-instant",
                        temperature=0.0
                    )
                    result_text = chat_completion.choices[0].message.content.strip().upper().replace("*", "")
                    provider_used = "Groq Backup Failover"
                except Exception as groq_err:
                    print(f" Critical: Both Cloud Providers Failed! {groq_err}")
                    return

            print(f" [{provider_used}] Evaluation -> \n{result_text}\n")
            
            if "STATUS: RED" in result_text or "RED" in result_text.split("STATUS:")[-1]:
                print(f" CRITICAL ALERT BROADCASTED VIA [{provider_used}]!")
                reason = result_text.split("REASON:")[-1].strip() if "REASON:" in result_text else "Crisis confirmed"
                
                # Send real-time data status right back to the React UI
                emit('safety_alert', {'status': 'RED', 'info': f"{reason} ({provider_used})"}, broadcast=True)
                
                # ASYNCHRONOUS THREAD HANDOFF: Spawns the Twilio worker in the background
                dispatch_thread = threading.Thread(
                    target=execute_emergency_dispatch,
                    args=(transcript, lat, lng, provider_used, reason)
                )
                dispatch_thread.start() # Starts processing the SMS/Call instantly without blocking the server
                
            else:
                print(f"🍃 Verification via [{provider_used}] cleared the context. System Clear.")
                emit('chunk_processed', {'status': 'processed', 'info': f'Cleared by Cloud ({provider_used})'})

    except Exception as e:
        print(f" Hybrid Pipeline Error: {e}")
        emit('chunk_processed', {'status': 'error', 'message': str(e)})

if __name__ == '__main__':
    socketio.run(app, host='127.0.0.1', port=5000, debug=True)
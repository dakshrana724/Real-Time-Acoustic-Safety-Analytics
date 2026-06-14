import os
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

#  1. Curate the Dataset (Vehicle Cabin Context)
# 0 = Normal/Safe Conversation, 1 = Active Threat/Distress
data = [
    # --- Class 0: Safe/Normal Phrases ---
    ("Let's turn up the radio volume", 0),
    ("Can we stop at the next gas station for food", 0),
    ("The traffic on the highway is pretty bad today", 0),
    ("I am driving back home from college right now", 0),
    ("What a beautiful sunny day for a long drive", 0),
    ("Can you pass me my water bottle please", 0),
    ("I love singing along to this song on the radio", 0),
    ("Let's navigate using the GPS map turn left here", 0),
    ("I'm feeling a bit tired from this long road trip", 0),
    ("We should check the tire pressure before we leave", 0),
    
    # --- Class 1: Distress/Threat Phrases ---
    ("Help me help me please stop the car", 1),
    ("Oh my god we are going to crash watch out", 1),
    ("There is a massive accident here call an ambulance", 1),
    ("Emergency emergency somebody call the police right now", 1),
    ("Stop the vehicle immediately I am in danger", 1),
    ("Get out of the car someone is attacking us", 1),
    ("Please help me I think I am trapped in here", 1),
    ("Screaming for help somebody please stop this vehicle", 1),
    ("He has a weapon stop the car right now", 1),
    ("There is smoke coming from the engine emergency", 1)
]

# Separate texts and labels
texts = [item[0] for item in data]
labels = [item[1] for item in data]

print(" Initializing Local Edge-Model Training Pipeline...")

#  2. Text Vectorization (TF-IDF)
# Converts sentences into numerical feature matrices based on word importance
vectorizer = TfidfVectorizer(lowercase=True, stop_words='english')
X = vectorizer.fit_transform(texts)
y = labels

#  3. Train/Test Split (For evaluation)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

#  4. Model Training
# Using Logistic Regression - perfect for low-latency, binary edge classification
model = LogisticRegression()
model.fit(X_train, y_train)

#  5. Evaluate the Quality
y_pred = model.predict(X_test)
print("\n📋 Model Evaluation Metrics:")
print(classification_report(y_test, y_pred, target_names=['Safe (0)', 'Distress (1)']))

#  6. Serialize and Save the Model Assets
print(" Saving trained intelligence assets locally...")
with open("vectorizer.pkl", "wb") as f:
    pickle.dump(vectorizer, f)

with open("safety_model.pkl", "wb") as f:
    pickle.dump(model, f)

print("\n Success! 'safety_model.pkl' and 'vectorizer.pkl' are armed and ready.")
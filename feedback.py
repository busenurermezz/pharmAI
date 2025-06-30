
import pandas as pd
import os
from datetime import datetime

FEEDBACK_FILE = "data/feedback.csv"

if not os.path.exists(FEEDBACK_FILE):
    pd.DataFrame(columns=["username", "drug", "liked", "timestamp"]).to_csv(FEEDBACK_FILE, index=False)

def save_feedback(username, drug_name, liked):
    df = pd.read_csv(FEEDBACK_FILE)
    new = {
        "username": username,
        "drug": drug_name,
        "liked": liked,
        "timestamp": datetime.now().isoformat()
    }
    df = pd.concat([df, pd.DataFrame([new])], ignore_index=True)
    df.to_csv(FEEDBACK_FILE, index=False)

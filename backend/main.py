# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests   # 👈 We'll send the link to your friend's NLP API

app = FastAPI()

# ✅ Allow frontend (Next.js) access
origins = ["http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Request body schema
class ReviewLink(BaseModel):
    link: str

# 👇 Replace with your friend's ngrok URL
FRIEND_API_URL = "https://josh-exiguous-consonantally.ngrok-free.dev/analyze"

@app.post("/analyze")
async def analyze(data: ReviewLink):
    link = data.link
    print(f"🔗 Received link from frontend: {link}")

    # 🧠 Send link to your friend’s NLP API
    try:
        response = requests.post(FRIEND_API_URL, json={"link": link})
        response.raise_for_status()  # raises error if status != 200
        result = response.json()
    except requests.RequestException as e:
        print(f"❌ Error calling friend's API: {e}")
        return {"error": "Failed to contact NLP service"}

    # ✅ Return result to your frontend
    return result

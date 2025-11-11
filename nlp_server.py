from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# -----------------------------
# Pydantic model for POST /analyze
# -----------------------------
class ReviewLink(BaseModel):
    link: str

# -----------------------------
# Root route
# -----------------------------
@app.get("/")
def root():
    return {"message": "API is running! Use POST /analyze with JSON {'link': 'your_link'}"}

# Optional: catch POST to root
@app.post("/")
def root_post():
    return {"error": "POST not allowed here. Use POST /analyze with JSON {'link': 'your_link'}"}

# -----------------------------
# Favicon route (prevents 404 spam)
# -----------------------------
@app.get("/favicon.ico")
def favicon():
    return '', 204

# -----------------------------
# Main analyze route
# -----------------------------
@app.post("/analyze")
def analyze(data: ReviewLink):
    link = data.link
    print(f"Received link: {link}")
    
    # Replace with your real NLP logic
    from data_extract import do1
    from processor import analyze1
    df, product_description = do1(link)
    result = analyze1(df,product_description)

    return {"result": result}

# -----------------------------
# Run locally with uvicorn
# -----------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000, log_level="info")

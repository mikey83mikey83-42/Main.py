from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"status": "success", "message": "Your FastAPI app is running on Render!"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
     

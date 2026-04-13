from fastapi import FastAPI

app = FastAPI()  # This 'app' variable must exist

@app.get("/")
def read_root():
    return {"Hello": "World"}

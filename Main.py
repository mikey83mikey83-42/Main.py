import uvicorn
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

if __name__ == "__main__":
    # This allows you to run 'python Main.py' 
    # instead of using the uvicorn command line
    uvicorn.run("Main:app", host="0.0.0.0", port=8000, reload=True)
     

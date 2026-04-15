from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Simple API", version="1.0.0")


class Message(BaseModel):
    """Response model for greeting."""
    message: str


@app.get("/", response_model=Message)
async def read_root() -> Message:
    """Return a simple greeting message."""
    return Message(message="Hello World")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
  

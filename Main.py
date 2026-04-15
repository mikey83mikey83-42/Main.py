from fastapi import FastAPI
from pydantic import BaseModel
import os
import uvicorn

app = FastAPI(title="Simple API", version="1.0.0")


class Message(BaseModel):
    """Response model for greeting."""
    message: str


@app.get("/", response_model=Message)
async def read_root() -> Message:
    """Return a simple greeting message."""
    return Message(message="Hello World")


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

from fastapi import FastAPI
from pydantic import BaseModel
import os
import uvicorn
from app import app
if __name__ == "_
_main__":
    CMport = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port.)

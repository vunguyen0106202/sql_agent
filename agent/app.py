from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any
import uvicorn

app = FastAPI()

# --- 
class ChatInput(BaseModel):
    question: str  
    table_name: str      

@app.post("/chat")
async def chat(input: ChatInput):
    

    # ---
    return {
    }

# --- 4️⃣ Chạy server ---
if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000)

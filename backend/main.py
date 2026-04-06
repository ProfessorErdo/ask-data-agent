from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import httpx
import logging
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent.parent / ".env")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI()

# Add CORS middleware - allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration from environment variables
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "https://ollama.com/api")
SERVER_PORT = int(os.getenv("SERVER_PORT", "8080"))

# Paths
BASE_DIR = Path(__file__).parent.parent
FRONTEND_DIR = BASE_DIR / "frontend" / "dist"
DOC_DIR = BASE_DIR / "doc"
OUTPUT_DIR = DOC_DIR / "output"
BRD_TEMPLATE = DOC_DIR / "BRD Template for Data Analyst Project (Data Visualization & Insight Analysis).md"

# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Chat request/response models
class ChatMessage(BaseModel):
    message: str
    model: str = "qwen3:8b"
    history: List[dict] = []

class ExportRequest(BaseModel):
    brd_content: str
    filename: Optional[str] = None

@app.get("/")
async def root():
    """Serve the React app"""
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "Frontend not built. Run 'npm run build' in frontend directory."}

@app.get("/brd-template")
async def get_brd_template():
    """Get the BRD template content"""
    if BRD_TEMPLATE.exists():
        try:
            content = BRD_TEMPLATE.read_text()
            return {"content": content}
        except IOError as e:
            logger.error(f"Error reading BRD template: {e}")
            raise HTTPException(status_code=500, detail="Failed to read BRD template")
    raise HTTPException(status_code=404, detail="BRD template not found")

@app.get("/models")
async def get_models():
    """Proxy to get available models from Ollama Cloud"""
    if not OLLAMA_API_KEY:
        raise HTTPException(status_code=401, detail="Ollama API key not configured")

    url = f"{OLLAMA_BASE_URL}/tags"
    headers = {"Authorization": f"Bearer {OLLAMA_API_KEY}"}

    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            models = data.get("models", [])
            return {"models": [{"name": m["name"]} for m in models]}
    except Exception as e:
        logger.error(f"Error fetching models: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch models: {str(e)}")

@app.post("/chat")
async def chat(chat_message: ChatMessage):
    """Proxy to send chat messages to Ollama Cloud"""
    url = f"{OLLAMA_BASE_URL}/chat"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OLLAMA_API_KEY}"
    }
    
    # Build messages for Ollama
    system_prompt = """You are a Product Manager / Project Manager for a data analysis project.
Your goal is to collect business requirements from the user to create a Business Requirements Document (BRD).
Ask questions one at a time to gather this information. Be professional and thorough."""

    messages = [{"role": "system", "content": system_prompt}]
    for msg in chat_message.history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": chat_message.message})

    payload = {
        "model": chat_message.model,
        "messages": messages,
        "stream": False
    }

    try:
        async with httpx.AsyncClient(timeout=180.0, follow_redirects=True) as client:
            response = await client.post(url, json=payload, headers=headers)
            if response.status_code >= 400:
                logger.error(f"Ollama error: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=503, 
                    detail=f"Ollama error: {response.status_code}. Response: {response.text[:200]}"
                )
            data = response.json()
            return {"response": data["message"]["content"]}
    except httpx.HTTPError as e:
        logger.error(f"HTTP error calling Ollama: {e}")
        raise HTTPException(status_code=503, detail=f"Failed to connect to Ollama: {str(e)}")
    except Exception as e:
        logger.error(f"Error calling Ollama: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/export-brd")
async def export_brd(request: ExportRequest):
    """Export BRD to file"""
    import datetime

    if request.filename:
        filename = request.filename
    else:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"draft_brd_{timestamp}.md"

    file_path = OUTPUT_DIR / filename
    try:
        file_path.write_text(request.brd_content)
    except IOError as e:
        logger.error(f"Error writing BRD file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to write BRD file: {str(e)}")

    return {"file_path": str(file_path), "filename": filename}

# Mount frontend static files if built
if FRONTEND_DIR.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="assets")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=SERVER_PORT)
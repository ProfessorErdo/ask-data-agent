from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import httpx
import logging
import os
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    model: str = "qwen"
    history: List[Dict[str, str]] = []

class ExportRequest(BaseModel):
    brd_content: str
    filename: Optional[str] = None

# System prompt for the AI
SYSTEM_PROMPT = """You are a Product Manager / Project Manager for a data analysis project.
Your goal is to collect business requirements from the user to create a Business Requirements Document (BRD).

You have a template with the following sections to collect:
1. Project Overview (name, sponsor, owner, team, timeline, objective)
2. Business Background & Problem Statement (context, pain points, business value)
3. Stakeholder Analysis
4. Core Requirements (data requirements, visualization requirements, insight analysis, non-functional)
5. Constraints & Risks
6. Deliverables
7. Acceptance Criteria

Ask questions one at a time to gather this information. Be professional and thorough.
After collecting all necessary information, summarize and offer to export the BRD.

Template file content:
{template_content}
"""

def get_ollama_response(messages: List[Dict[str, str]], model: str) -> str:
    """Call Ollama API to get response"""
    url = "http://localhost:11434/api/chat"
    payload = {
        "model": model,
        "messages": messages,
        "stream": False
    }
    try:
        with httpx.Client(timeout=120.0) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            return response.json()["message"]["content"]
    except httpx.HTTPError as e:
        logger.error(f"HTTP error calling Ollama: {e}")
        raise HTTPException(status_code=503, detail=f"Failed to connect to Ollama: {str(e)}")
    except Exception as e:
        logger.error(f"Error calling Ollama: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

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

@app.post("/chat")
async def chat(chat_message: ChatMessage):
    """Handle chat messages"""
    # Build messages for Ollama
    template_content = ""
    if BRD_TEMPLATE.exists():
        try:
            template_content = BRD_TEMPLATE.read_text()
        except IOError as e:
            logger.error(f"Error reading BRD template: {e}")
            template_content = ""

    messages = [{"role": "system", "content": SYSTEM_PROMPT.format(template_content=template_content)}]

    # Add conversation history
    for msg in chat_message.history:
        messages.append({"role": msg["role"], "content": msg["content"]})

    # Add current message
    messages.append({"role": "user", "content": chat_message.message})

    # Get response from Ollama
    response = get_ollama_response(messages, chat_message.model)

    return {"response": response}

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
    uvicorn.run(app, host="0.0.0.0", port=8000)
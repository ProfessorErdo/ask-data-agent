# Ask Data Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a React + FastAPI chatbot application that collects business requirements for data analysis projects using local Ollama models (qwen/gemma), and exports draft BRD documents.

**Architecture:** React SPA frontend with FastAPI backend. Backend serves static files and provides /chat API endpoint that communicates with Ollama. AI acts as Product Manager to collect BRD fields through conversation.

**Tech Stack:** React (Vite), FastAPI, Python, Ollama (qwen, gemma)

---

## File Structure

```
ask-data/
├── frontend/                 # React app (create via Vite)
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatMessage.jsx
│   │   │   ├── ChatInput.jsx
│   │   │   ├── ModelSelector.jsx
│   │   │   ├── ProgressTracker.jsx
│   │   │   └── Header.jsx
│   │   ├── App.jsx
│   │   ├── App.css
│   │   └── main.jsx
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── backend/
│   ├── main.py              # FastAPI app
│   └── requirements.txt     # Python dependencies
├── doc/
│   ├── BRD Template for Data Analyst Project (Data Visualization & Insight Analysis).md
│   ├── output/              # Exported BRDs
│   ├── superpowers/
│   │   ├── specs/
│   │   └── plans/
└── pyproject.toml
```

---

## Task 1: Set up FastAPI Backend

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/main.py`

- [ ] **Step 1: Create backend/requirements.txt**

```txt
fastapi==0.109.0
uvicorn==0.27.0
python-multipart==0.0.6
httpx==0.26.0
jinja2==3.1.3
```

- [ ] **Step 2: Create backend/main.py**

```python
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import httpx
import os
from pathlib import Path

app = FastAPI()

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
    except Exception as e:
        return f"Error: {str(e)}"

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
        content = BRD_TEMPLATE.read_text()
        return {"content": content}
    raise HTTPException(status_code=404, detail="BRD template not found")

@app.post("/chat")
async def chat(chat_message: ChatMessage):
    """Handle chat messages"""
    # Build messages for Ollama
    template_content = ""
    if BRD_TEMPLATE.exists():
        template_content = BRD_TEMPLATE.read_text()

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
    file_path.write_text(request.brd_content)

    return {"file_path": str(file_path), "filename": filename}

# Mount frontend static files if built
if FRONTEND_DIR.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="assets")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

- [ ] **Step 3: Test backend starts**

Run: `cd backend && pip install -r requirements.txt && python main.py`
Expected: Server starts on port 8000

- [ ] **Step 4: Commit**

```bash
git add backend/requirements.txt backend/main.py
git commit -m "feat: add FastAPI backend with Ollama integration"
```

---

## Task 2: Set up React Frontend with Vite

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.js`
- Create: `frontend/index.html`
- Create: `frontend/src/main.jsx`
- Create: `frontend/src/App.jsx`
- Create: `frontend/src/App.css`

- [ ] **Step 1: Create frontend/package.json**

```json
{
  "name": "ask-data-frontend",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.43",
    "@types/react-dom": "^18.2.17",
    "@vitejs/plugin-react": "^4.2.1",
    "vite": "^5.0.8"
  }
}
```

- [ ] **Step 2: Create frontend/vite.config.js**

```javascript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/chat': 'http://localhost:8000',
      '/brd-template': 'http://localhost:8000',
      '/export-brd': 'http://localhost:8000'
    }
  }
})
```

- [ ] **Step 3: Create frontend/index.html**

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Ask Data - BRD Collection</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
```

- [ ] **Step 4: Create frontend/src/main.jsx**

```jsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
```

- [ ] **Step 5: Create frontend/src/index.css (base styles)**

```css
:root {
  --primary: #1e40af;
  --primary-light: #3b82f6;
  --primary-lighter: #dbeafe;
  --bg: #f8fafc;
  --white: #ffffff;
  --text: #1e293b;
  --text-light: #64748b;
  --border: #e2e8f0;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: Inter, system-ui, -apple-system, sans-serif;
  background: var(--bg);
  color: var(--text);
  line-height: 1.5;
}

#root {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}
```

- [ ] **Step 6: Create frontend/src/App.css (main styles)**

```css
.app {
  display: flex;
  flex-direction: column;
  height: 100vh;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
}

/* Header */
.header {
  background: var(--primary);
  color: var(--white);
  padding: 1rem 1.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.header h1 {
  font-size: 1.25rem;
  font-weight: 600;
}

.header-controls {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.model-selector {
  padding: 0.5rem 1rem;
  border-radius: 6px;
  border: 1px solid rgba(255,255,255,0.3);
  background: rgba(255,255,255,0.1);
  color: var(--white);
  font-size: 0.875rem;
  cursor: pointer;
}

.model-selector option {
  color: var(--text);
  background: var(--white);
}

/* Main content */
.main-content {
  display: flex;
  flex: 1;
  overflow: hidden;
}

/* Chat container */
.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--white);
  margin: 1rem;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  overflow: hidden;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

/* Chat messages */
.message {
  max-width: 80%;
  padding: 0.75rem 1rem;
  border-radius: 12px;
  line-height: 1.5;
}

.message.user {
  align-self: flex-end;
  background: var(--primary-lighter);
  color: var(--primary);
  border-bottom-right-radius: 4px;
}

.message.ai {
  align-self: flex-start;
  background: var(--white);
  border: 1px solid var(--border);
  border-bottom-left-radius: 4px;
}

.message-header {
  font-size: 0.75rem;
  font-weight: 600;
  margin-bottom: 0.25rem;
  opacity: 0.7;
}

/* Chat input */
.chat-input-container {
  padding: 1rem;
  border-top: 1px solid var(--border);
  display: flex;
  gap: 0.75rem;
}

.chat-input {
  flex: 1;
  padding: 0.75rem 1rem;
  border: 1px solid var(--border);
  border-radius: 8px;
  font-size: 0.9375rem;
  font-family: inherit;
  resize: none;
}

.chat-input:focus {
  outline: none;
  border-color: var(--primary-light);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.send-button {
  padding: 0.75rem 1.5rem;
  background: var(--primary);
  color: var(--white);
  border: none;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.send-button:hover {
  background: var(--primary-light);
}

.send-button:disabled {
  background: var(--text-light);
  cursor: not-allowed;
}

/* Progress sidebar */
.progress-sidebar {
  width: 280px;
  background: var(--white);
  margin: 1rem 0 1rem 0;
  border-radius: 12px;
  padding: 1.25rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.progress-sidebar h3 {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-light);
  margin-bottom: 1rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.progress-section {
  margin-bottom: 1rem;
}

.progress-section-title {
  font-size: 0.8125rem;
  font-weight: 500;
  margin-bottom: 0.5rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.progress-section-title .icon {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.625rem;
}

.progress-section-title .icon.completed {
  background: #10b981;
  color: white;
}

.progress-section-title .icon.pending {
  background: var(--border);
  color: var(--text-light);
}

.progress-items {
  padding-left: 1.5rem;
}

.progress-item {
  font-size: 0.8125rem;
  color: var(--text-light);
  padding: 0.25rem 0;
}

.progress-item.completed {
  color: #10b981;
}

/* Export button */
.export-section {
  margin-top: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid var(--border);
}

.export-button {
  width: 100%;
  padding: 0.75rem;
  background: #10b981;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.export-button:hover {
  background: #059669;
}

.export-button:disabled {
  background: var(--border);
  color: var(--text-light);
  cursor: not-allowed;
}

/* Loading state */
.loading {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--text-light);
  font-size: 0.875rem;
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid var(--border);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
```

- [ ] **Step 7: Create frontend/src/App.jsx (main component)**

```jsx
import { useState, useEffect, useRef } from 'react'
import './App.css'

function App() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [model, setModel] = useState('qwen')
  const [loading, setLoading] = useState(false)
  const [brdTemplate, setBrdTemplate] = useState('')
  const [collectedFields, setCollectedFields] = useState({})
  const messagesEndRef = useRef(null)

  // Load BRD template on mount
  useEffect(() => {
    fetch('/brd-template')
      .then(res => res.json())
      .then(data => setBrdTemplate(data.content))
      .catch(err => console.error('Failed to load template:', err))
  }, [])

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() || loading) return

    const userMessage = input.trim()
    setInput('')
    setLoading(true)

    // Add user message
    setMessages(prev => [...prev, { role: 'user', content: userMessage }])

    try {
      const response = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMessage,
          model: model,
          history: messages
        })
      })

      const data = await response.json()
      setMessages(prev => [...prev, { role: 'ai', content: data.response }])
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'ai',
        content: 'Sorry, I encountered an error. Make sure Ollama is running with the qwen or gemma model.'
      }])
    }

    setLoading(false)
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleExport = async () => {
    // For now, export a simple summary
    const summary = `# Draft BRD - ${new Date().toLocaleDateString()}

## Collected Information

${messages.map(m => `### ${m.role === 'user' ? 'User' : 'AI'}
${m.content}
`).join('\n')}

---
*Generated by Ask Data - BRD Collection Chatbot*
`

    try {
      const response = await fetch('/export-brd', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ brd_content: summary })
      })

      const data = await response.json()
      alert(`BRD exported to: ${data.file_path}`)
    } catch (err) {
      alert('Failed to export BRD')
    }
  }

  // Progress sections based on BRD template
  const progressSections = [
    { id: 'project', title: 'Project Overview', items: ['Name', 'Sponsor', 'Owner', 'Team', 'Timeline', 'Objective'] },
    { id: 'business', title: 'Business Background', items: ['Context', 'Pain Points', 'Business Value'] },
    { id: 'stakeholder', title: 'Stakeholder Analysis', items: ['Stakeholders', 'Interests', 'Expectations'] },
    { id: 'requirements', title: 'Core Requirements', items: ['Data Sources', 'Visualization', 'Insights', 'Non-functional'] },
    { id: 'constraints', title: 'Constraints & Risks', items: ['Resources', 'Timeline', 'Risks'] },
    { id: 'deliverables', title: 'Deliverables', items: ['List of deliverables'] }
  ]

  return (
    <div className="app">
      <header className="header">
        <h1>Ask Data - BRD Collection</h1>
        <div className="header-controls">
          <select
            className="model-selector"
            value={model}
            onChange={(e) => setModel(e.target.value)}
          >
            <option value="qwen">Qwen</option>
            <option value="gemma">Gemma</option>
          </select>
        </div>
      </header>

      <main className="main-content">
        <div className="chat-container">
          <div className="chat-messages">
            {messages.length === 0 && (
              <div className="message ai">
                <div className="message-header">AI Assistant</div>
                Hello! I'm your Product Manager assistant. I'll help you create a Business Requirements Document (BRD) for your data analysis project. Let's start by discussing your project. What is the name of your project?
              </div>
            )}
            {messages.map((msg, idx) => (
              <div key={idx} className={`message ${msg.role}`}>
                <div className="message-header">
                  {msg.role === 'user' ? 'You' : 'AI Assistant'}
                </div>
                {msg.content}
              </div>
            ))}
            {loading && (
              <div className="loading">
                <div className="spinner"></div>
                Thinking...
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="chat-input-container">
            <textarea
              className="chat-input"
              placeholder="Type your message..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              rows={1}
            />
            <button
              className="send-button"
              onClick={handleSend}
              disabled={loading || !input.trim()}
            >
              Send
            </button>
          </div>
        </div>

        <aside className="progress-sidebar">
          <h3>BRD Progress</h3>
          {progressSections.map(section => (
            <div key={section.id} className="progress-section">
              <div className="progress-section-title">
                <span className="icon pending">○</span>
                {section.title}
              </div>
              <div className="progress-items">
                {section.items.map((item, idx) => (
                  <div key={idx} className="progress-item">{item}</div>
                ))}
              </div>
            </div>
          ))}

          <div className="export-section">
            <button className="export-button" onClick={handleExport}>
              Export Draft BRD
            </button>
          </div>
        </aside>
      </main>
    </div>
  )
}

export default App
```

- [ ] **Step 8: Install dependencies and build**

Run: `cd frontend && npm install && npm run build`
Expected: Build completes successfully

- [ ] **Step 9: Commit**

```bash
git add frontend/
git commit -m "feat: add React frontend with chat UI"
```

---

## Task 3: Test Full Integration

**Files:**
- Test: Full system integration

- [ ] **Step 1: Ensure Ollama is running**

Run: `ollama list` (check if qwen and gemma models are available)
Expected: List of installed models

- [ ] **Step 2: Start backend**

Run: `cd backend && python main.py`
Expected: Server starts on http://localhost:8000

- [ ] **Step 3: Test frontend loads**

Open: http://localhost:8000
Expected: Chat interface loads with corporate blue theme

- [ ] **Step 4: Test chat functionality**

Send a message: "I want to build a sales dashboard"
Expected: AI responds (if Ollama is running)

- [ ] **Step 5: Test export**

Click "Export Draft BRD"
Expected: File saved to doc/output/

- [ ] **Step 6: Commit**

```bash
git add .
git commit -m "test: verify full integration"
```

---

## Task 4: Final Polish

**Files:**
- Modify: `frontend/src/App.jsx`
- Modify: `frontend/src/App.css`

- [ ] **Step 1: Add better progress tracking logic**

Update App.jsx to track which fields have been collected based on conversation

- [ ] **Step 2: Add export with full BRD template**

Update export to fill in the actual BRD template with collected data

- [ ] **Step 3: Commit**

```bash
git add .
git commit -m "feat: add progress tracking and full BRD export"
```

---

## Summary

| Task | Description |
|------|-------------|
| 1 | Set up FastAPI backend with Ollama integration |
| 2 | Set up React frontend with Vite |
| 3 | Test full integration |
| 4 | Final polish |

**Plan complete and saved to `docs/superpowers/plans/2026-04-05-ask-data-implementation-plan.md`. Two execution options:**

1. **Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

2. **Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
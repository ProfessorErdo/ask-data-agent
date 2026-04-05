# Ask Data Frontend - Project Specification

## 1. Project Overview

**Project Name**: Ask Data - Business Requirements Collection Chatbot

**Core Functionality**: A web-based chatbot interface that collects business requirements for data analysis projects. Users chat with an AI (powered by Ollama) acting as a Product Manager to gather all necessary information, then export a draft BRD document.

## 2. Architecture

### Tech Stack
- **Frontend**: React (Vite)
- **Backend**: FastAPI (Python)
- **AI**: Ollama (local models: qwen, gemma)
- **Styling**: Corporate blue theme

### System Components
1. **React Frontend** - Chat UI with message bubbles, model selector, progress tracker
2. **FastAPI Backend** - Serves static files, provides /chat API endpoint
3. **Ollama Integration** - Local LLM for conversational AI

## 3. UI/UX Specification

### Layout Structure
- **Header**: App title, model selector dropdown
- **Main Area**: Chat messages container (scrollable)
- **Input Area**: Text input + send button at bottom
- **Sidebar** (optional): Progress indicator showing BRD sections

### Visual Design
- **Primary Color**: #1e40af (Corporate Blue)
- **Secondary Color**: #3b82f6 (Lighter blue)
- **Background**: #f8fafc (Light gray)
- **User Message**: #dbeafe (Light blue bubble)
- **AI Message**: #ffffff (White bubble)
- **Text Color**: #1e293b (Dark slate)
- **Font**: Inter or system-ui

### Components
1. **ChatMessage** - Message bubble (user/AI differentiated)
2. **ChatInput** - Text input with send button
3. **ModelSelector** - Dropdown for qwen/gemma
4. **ProgressTracker** - Shows completed sections of BRD
5. **ExportButton** - Triggers BRD export

## 4. Backend API Specification

### Endpoints
- `GET /` - Serve React app
- `POST /chat` - Send message to Ollama
  - Request: `{ "message": string, "model": string, "history": array }`
  - Response: `{ "response": string, "collected_fields": object }`
- `POST /export-brd` - Export filled BRD
  - Request: `{ "brd_content": string }`
  - Response: `{ "file_path": string }`
- `GET /brd-template` - Get the BRD template content

### Ollama Integration
- Default model: qwen
- Streaming response for chat
- System prompt defines the AI role as Product Manager

## 5. Chatbot Behavior

### AI Role
- Acts as Product Manager / Project Manager
- Reads BRD template from `doc/BRD Template for Data Analyst Project.md`
- Systematically collects all required fields through conversation

### Conversation Flow
1. Greet user and explain purpose
2. Ask about project basics (name, sponsor, owner)
3. Explore business context and pain points
4. Discuss data requirements
5. Discuss visualization requirements
6. Discuss insight analysis requirements
7. Review constraints and risks
8. Confirm completion and offer export

### Progress Tracking
- Track which BRD sections have been filled
- Display progress in sidebar/header
- Allow user to see what's been collected

## 6. File Structure
```
ask-data/
├── frontend/           # React app
│   ├── src/
│   │   ├── components/
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── index.html
│   └── vite.config.js
├── backend/
│   ├── main.py
│   └── requirements.txt
├── doc/
│   ├── BRD Template for Data Analyst Project.md
│   └── output/         # Exported BRDs
└── pyproject.toml
```

## 7. Acceptance Criteria

1. ✅ React app loads and displays chat interface
2. ✅ User can send messages and receive AI responses
3. ✅ Model selector switches between qwen and gemma
4. ✅ AI collects all BRD fields through conversation
5. ✅ Progress tracker shows completed sections
6. ✅ Export button generates BRD in doc/output folder
7. ✅ Corporate blue theme applied consistently
8. ✅ FastAPI serves both frontend and API endpoints
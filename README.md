# Ask Data - BRD Collection Assistant

A chatbot application that helps collect Business Requirements Documents (BRD) for data analysis projects through natural conversation.

## Features

- Interactive chat interface for gathering BRD information
- Real-time progress tracking of collected requirements
- Multiple AI model support via Ollama Cloud
- Export draft BRD documents as Markdown files
- Responsive React frontend with modern UI

## Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend | React + Vite |
| Backend | FastAPI (Python) |
| AI Models | Ollama Cloud API |
| Deployment | Self-hosted server |

## Project Structure

```
ask-data/
├── frontend/          # React frontend application
│   ├── src/           # React components and styles
│   └── dist/          # Built static files (after build)
├── backend/           # FastAPI backend service
│   ├── main.py        # Main application server
│   └── requirements.txt
├── doc/               # Documentation and BRD templates
│   ├── BRD Template*.md
│   └── output/        # Generated BRD files
├── deploy-ali.sh      # Deployment script for Alibaba Cloud
├── .env               # Environment configuration
└── README.md
```

## Quick Start

### Prerequisites

- Python 3.8+
- Node.js 18+
- Ollama Cloud API key

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ask-data
   ```

2. **Configure environment**
   ```bash
   # Create .env file
   echo "OLLAMA_API_KEY=your-api-key" > .env
   echo "OLLAMA_BASE_URL=https://ollama.com/api" >> .env
   echo "SERVER_PORT=8080" >> .env
   ```

3. **Install dependencies**
   ```bash
   # Backend
   pip install -r backend/requirements.txt

   # Frontend
   cd frontend && npm install && cd ..
   ```

4. **Build frontend**
   ```bash
   cd frontend && npm run build && cd ..
   ```

5. **Run server**
   ```bash
   python backend/main.py
   ```

6. **Access application**
   Open http://localhost:8080 in your browser

## Server Deployment

See [doc/deployment-guide.md](doc/deployment-guide.md) for detailed deployment instructions on Alibaba Cloud Lightweight Server.

### Quick Deployment

```bash
./deploy-ali.sh          # Full deployment (build + start)
./deploy-ali.sh status   # Check service status
./deploy-ali.sh restart  # Restart service
./deploy-ali.sh stop     # Stop service
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Serve frontend application |
| `/models` | GET | Get available AI models |
| `/chat` | POST | Send chat message to AI |
| `/brd-template` | GET | Get BRD template content |
| `/export-brd` | POST | Export BRD to Markdown file |

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `OLLAMA_API_KEY` | Ollama Cloud API key | Required |
| `OLLAMA_BASE_URL` | Ollama API endpoint | `https://ollama.com/api` |
| `SERVER_PORT` | Server port | `8080` |

## License

MIT
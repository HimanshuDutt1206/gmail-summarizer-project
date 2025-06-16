# Quick Start Guide - Gmail Intelligent Processor

## Prerequisites

- Python 3.7+
- Ollama installed and running
- Gmail account

## 5-Minute Setup

### 1. Install Ollama

```bash
# Visit ollama.ai and install for your OS
# Then pull a model:
ollama pull mistral:7b
```

### 2. Gmail API Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create project → Enable Gmail API → Create OAuth2 credentials
3. Download as `credentials.json` → Place in `credentials/` folder

### 3. Run Application

```bash
pip install -r requirements.txt
python app.py
```

## That's It!

- Browser opens automatically at http://127.0.0.1:5000
- Click "Analyze My Emails" to process unread emails
- All AI processing happens locally with Ollama
- No API keys needed!

## Troubleshooting

- **Ollama not available**: Run `ollama serve` first
- **Model not found**: Run `ollama pull mistral:7b`
- **Gmail auth failed**: Check `credentials.json` placement

## Features

- ✅ Local AI processing (privacy-first)
- ✅ Smart email categorization
- ✅ Deadline extraction
- ✅ Real-time filtering
- ✅ No external API costs

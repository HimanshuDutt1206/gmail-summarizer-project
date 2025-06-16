# Gmail Intelligent Processor

An AI-powered email management system that automatically categorizes, summarizes, and extracts important information from your Gmail inbox using **Ollama** for local LLM processing.

## Features

- **Smart Email Analysis**: Uses Ollama (local LLM) to analyze emails for importance, content, and deadlines
- **Importance-Based Categorization**: Automatically sorts emails into VERY_IMPORTANT, IMPORTANT, UNIMPORTANT, and SPAM
- **Intelligent Summarization**: Generates concise summaries focusing on actionable information
- **Deadline Detection**: Automatically extracts dates, deadlines, and time-sensitive information
- **Real-time Filtering**: Filter emails by importance level and deadline presence
- **Privacy-First**: All LLM processing happens locally with Ollama - no data sent to external APIs
- **Modern Web Interface**: Clean, responsive UI with real-time updates

## Prerequisites

1. **Python 3.7+**
2. **Gmail API Credentials** (Google Cloud Console)
3. **Ollama** installed and running locally

## Setup Instructions

### 1. Install Ollama

First, install Ollama on your system:

- Visit [ollama.ai](https://ollama.ai) and download for your OS
- Install and start Ollama
- Pull a model (recommended: Mistral 7B):
  ```bash
  ollama pull mistral:7b
  ```

### 2. Gmail API Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Gmail API
4. Create credentials (OAuth 2.0 Client ID) for Desktop Application
5. Download the credentials file as `credentials.json`
6. Place it in the `credentials/` folder of this project

### 3. Project Setup

1. Clone/download this project
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Create the required directories:

   ```bash
   mkdir credentials config
   ```

4. Place your `credentials.json` in the `credentials/` folder

5. **No API keys needed!** - Ollama runs locally

### 4. Run the Application

```bash
python app.py
```

The application will:

- Start the local web server
- Open your browser automatically
- Connect to Ollama for LLM processing
- Authenticate with Gmail (first time only)

## How It Works

### Email Processing Pipeline

1. **Fetch**: Retrieves unread emails from Gmail
2. **Analyze**: Uses Ollama (local LLM) to analyze each email for:
   - Importance level (VERY_IMPORTANT, IMPORTANT, UNIMPORTANT, SPAM)
   - Content summary (actionable information only)
   - Deadlines and dates
   - Important links and attachments
3. **Filter**: Provides real-time filtering by importance and deadlines
4. **Display**: Shows results in a clean, modern interface

### Ollama Integration

- **Local Processing**: All AI analysis happens on your machine
- **Privacy**: No email content sent to external services
- **Customizable**: Easy to switch between different Ollama models
- **Fast**: Direct local API calls without network latency

## Usage

1. **Process Emails**: Click "Analyze My Emails" to process unread emails
2. **Filter Results**: Use dropdown filters to view specific importance levels
3. **View Details**: Click on any email to see detailed analysis
4. **Real-time Updates**: Interface updates automatically as emails are processed

## Configuration

### Changing Ollama Model

Edit `src/llm_service.py` and change the model name:

```python
self.model_name = "mistral:7b"  # Change to your preferred model
```

Available models (pull with `ollama pull <model>`):

- `mistral:7b` (recommended)
- `llama2:7b`
- `codellama:7b`
- `neural-chat:7b`

### Email Processing Limits

Edit `app.py` to change the number of emails processed:

```python
MAX_EMAILS_TO_PROCESS = 50  # Adjust as needed
```

## File Structure

```
mail-project/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── src/
│   ├── gmail_client.py   # Gmail API integration
│   └── llm_service.py    # Ollama LLM service
├── templates/            # HTML templates
├── static/              # CSS, JS, images
├── credentials/         # Gmail API credentials
└── config/             # Configuration files
```

## Troubleshooting

### Ollama Issues

- **"Ollama not available"**: Ensure Ollama is running (`ollama serve`)
- **Model not found**: Pull the model first (`ollama pull mistral:7b`)
- **Connection refused**: Check if Ollama is running on default port (11434)

### Gmail API Issues

- **Authentication failed**: Ensure `credentials.json` is in the `credentials/` folder
- **Permission denied**: Check Gmail API is enabled in Google Cloud Console
- **Token expired**: Delete `credentials/token.json` and re-authenticate

### General Issues

- **Import errors**: Run `pip install -r requirements.txt`
- **Port in use**: Change the port in `app.py` if 5000 is occupied

## Privacy & Security

- **Local Processing**: All email analysis happens locally with Ollama
- **No External APIs**: No email content sent to third-party services
- **Secure Storage**: Credentials stored locally, never transmitted
- **Open Source**: Full transparency of data handling

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source and available under the MIT License.

---

**Happy Email Processing! 🎉**

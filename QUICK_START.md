# Quick Start Guide 🚀

## For the Impatient 😄

Want to get this running ASAP? Follow these steps:

### 1. Run Setup Script

```bash
python setup.py
```

### 2. Get Gmail API Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create project → Enable Gmail API → Create OAuth2 credentials
3. Download as `credentials.json` → Put in `credentials/` folder

### 3. Get Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Get API key → Create `.env` file → Add `GOOGLE_API_KEY=your_key`

### 4. Run the App

```bash
python app.py
```

### 5. First Time Setup

- Browser opens → Sign in to Gmail → Grant permissions → Done! 🎉

---

**That's it!** The app will process your unread emails with AI and show them in a beautiful interface.

For detailed instructions, see the main [README.md](README.md) file.

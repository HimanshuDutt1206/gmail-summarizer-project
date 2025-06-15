# Gmail Intelligent Processor 🤖📧

An AI-powered Gmail email processing application that automatically categorizes, summarizes, and extracts deadlines from your emails using Google Gemini AI.

## Features ✨

- **AI-Powered Classification**: Automatically categorizes emails into VERY_IMPORTANT, IMPORTANT, UNIMPORTANT, or SPAM
- **Smart Summarization**: Generates concise 2-3 sentence summaries of email content
- **Deadline Extraction**: Automatically identifies and extracts deadlines from emails
- **Real-time Filtering**: Filter emails by importance level and deadline presence
- **Modern UI**: Clean, responsive interface with color-coded importance badges
- **Gmail Integration**: Secure OAuth2 integration with Gmail API

## Prerequisites 📋

Before setting up this project, ensure you have:

1. **Python 3.7+** installed on your system
2. **A Gmail account** that you want to process
3. **Google Cloud Console access** for API setup
4. **Google AI Studio account** for Gemini API (free tier available)

## Setup Instructions 🚀

### Step 1: Download and Extract Project

1. Download/clone this project to your local machine
2. Navigate to the project directory in your terminal/command prompt

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Set Up Gmail API Access

1. **Go to Google Cloud Console**: https://console.cloud.google.com/
2. **Create a new project** or select an existing one
3. **Enable Gmail API**:
   - Go to "APIs & Services" > "Library"
   - Search for "Gmail API" and enable it
4. **Create OAuth2 Credentials**:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth 2.0 Client IDs"
   - Choose "Desktop application" as application type
   - Name it (e.g., "Gmail Processor")
   - Download the JSON file
5. **Save credentials**:
   - Rename the downloaded file to `credentials.json`
   - Place it in the `credentials/` folder of this project

### Step 4: Set Up Google Gemini API

1. **Go to Google AI Studio**: https://aistudio.google.com/
2. **Get API Key**:
   - Click "Get API Key"
   - Create a new API key or use existing one
   - Copy the API key
3. **Create environment file**:
   - Create a file named `.env` in the project root directory
   - Add your API key:
   ```
   GOOGLE_API_KEY=your_gemini_api_key_here
   ```

### Step 5: Run the Application

```bash
python app.py
```

### Step 6: First-Time Gmail Authentication

1. When you first run the app, it will open a browser window
2. **Sign in to your Gmail account**
3. **Grant permissions** to the application
4. The app will save authentication tokens for future use

## Project Structure 📁

```
mail-project/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── .env                  # Environment variables (create this)
├── credentials/
│   └── credentials.json  # Gmail API credentials (add this)
├── src/
│   ├── llm_service.py    # Google Gemini integration
│   └── gmail_client.py   # Gmail API client
├── config/
│   └── config.py         # Application configuration
├── templates/
│   └── index.html        # Web interface
└── static/
    ├── style.css         # Styling
    └── script.js         # Frontend JavaScript
```

## Usage 💡

1. **Start the application**: Run `python app.py`
2. **Open web browser**: Navigate to `http://127.0.0.1:5000`
3. **Process emails**: Click "Process Emails" to analyze unread emails
4. **Filter results**: Use the dropdown filters to view specific email categories
5. **View details**: Click on any email to see full content and analysis

## API Limits 📊

- **Google Gemini Free Tier**: 60 requests/minute, 1,500 requests/day
- **Gmail API**: 1 billion quota units/day (more than sufficient for personal use)

## Troubleshooting 🔧

### Common Issues:

1. **"No module named 'google'"**

   - Run: `pip install -r requirements.txt`

2. **"Invalid credentials"**

   - Ensure `credentials.json` is in the `credentials/` folder
   - Check that Gmail API is enabled in Google Cloud Console

3. **"API key not found"**

   - Ensure `.env` file exists with `GOOGLE_API_KEY=your_key`
   - Verify the API key is valid in Google AI Studio

4. **"Permission denied" on first run**

   - Complete the OAuth flow in the browser
   - Grant all requested permissions

5. **"Rate limit exceeded"**
   - Wait a few minutes and try again
   - The app has built-in retry logic for API limits

### Debug Mode:

The application runs in debug mode by default and provides detailed logging. Check the console output for specific error messages.

## Security Notes 🔒

- **Never share your `credentials.json` file** - it contains sensitive authentication data
- **Never share your `.env` file** - it contains your API keys
- **The `token.json` file** (created after first authentication) should also not be shared
- All sensitive files are automatically excluded from this distribution

## Customization 🎨

You can customize the application by:

- **Modifying categories**: Edit the importance levels in `src/llm_service.py`
- **Changing UI colors**: Update CSS classes in `static/style.css`
- **Adjusting AI prompts**: Modify the prompts in `src/llm_service.py`
- **Adding new filters**: Extend the filtering logic in `static/script.js`

## Support 💬

If you encounter any issues:

1. Check the troubleshooting section above
2. Verify all setup steps were completed correctly
3. Check the console output for detailed error messages
4. Ensure your API keys and credentials are valid

## License 📄

This project is for educational and personal use. Please respect Gmail's Terms of Service and Google's API usage policies.

---

**Happy Email Processing! 🎉**

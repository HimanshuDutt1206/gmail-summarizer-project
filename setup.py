#!/usr/bin/env python3
"""
Gmail Intelligent Processor Setup Script
This script helps set up the project for first-time users.
"""

import os
import sys
import subprocess


def check_python_version():
    """Check if Python version is 3.7 or higher"""
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required!")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True


def install_dependencies():
    """Install required Python packages"""
    print("\n📦 Installing dependencies...")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies!")
        return False


def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating directories...")

    # Create credentials directory if it doesn't exist
    if not os.path.exists("credentials"):
        os.makedirs("credentials")
        print("✅ Created credentials/ directory")
    else:
        print("✅ credentials/ directory already exists")


def check_credentials():
    """Check if credentials.json exists"""
    print("\n🔑 Checking credentials...")

    if os.path.exists("credentials/credentials.json"):
        print("✅ credentials.json found!")
        return True
    else:
        print("❌ credentials.json not found!")
        print("\n📋 To set up Gmail API credentials:")
        print("1. Go to: https://console.cloud.google.com/")
        print("2. Create a new project or select existing one")
        print("3. Enable Gmail API")
        print("4. Create OAuth 2.0 Client ID credentials")
        print("5. Download the JSON file as 'credentials.json'")
        print("6. Place it in the credentials/ folder")
        return False


def check_env_file():
    """Check if .env file exists"""
    print("\n🌍 Checking environment file...")

    if os.path.exists(".env"):
        print("✅ .env file found!")
        return True
    else:
        print("❌ .env file not found!")
        print("\n📋 To set up Google Gemini API:")
        print("1. Go to: https://aistudio.google.com/")
        print("2. Get your API key")
        print("3. Create a .env file in the project root")
        print("4. Add: GOOGLE_API_KEY=your_api_key_here")

        # Create a template .env file
        with open(".env.template", "w") as f:
            f.write("# Google Gemini API Key\n")
            f.write("# Get your key from: https://aistudio.google.com/\n")
            f.write("GOOGLE_API_KEY=your_api_key_here\n")

        print("✅ Created .env.template file for reference")
        return False


def main():
    """Main setup function"""
    print("🚀 Gmail Intelligent Processor Setup")
    print("=" * 40)

    # Check Python version
    if not check_python_version():
        return False

    # Create directories
    create_directories()

    # Install dependencies
    if not install_dependencies():
        return False

    # Check credentials
    credentials_ok = check_credentials()

    # Check environment file
    env_ok = check_env_file()

    print("\n" + "=" * 40)

    if credentials_ok and env_ok:
        print("🎉 Setup complete! You can now run:")
        print("   python app.py")
    else:
        print("⚠️  Setup incomplete. Please complete the missing steps above.")
        print("   Then run: python app.py")

    return True


if __name__ == "__main__":
    main()

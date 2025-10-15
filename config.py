import os
from dotenv import load_dotenv, find_dotenv

# Load environment variables (.env preferred, fallback to env.production)
env_file = find_dotenv('.env') or find_dotenv('env.production')
if env_file:
    load_dotenv(env_file)
else:
    # Last resort: load default .env if present in current dir
    load_dotenv()

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '7433503826:AAExwKQ630W1jQRy0QnV_XelK-1cTy4b2jI')

# OpenAI Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')

# ElevenLabs API Configuration
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY', 'sk_1cf8e41230cc2f3605941b4f29684e926ec3fcb64ab4c0ed')

# The Odds API Configuration
THE_ODDS_API_KEY = os.getenv('THE_ODDS_API_KEY', '9f217215a2311cb1994f9d8e6b989b17')
THE_ODDS_API_BASE_URL = 'https://api.the-odds-api.com/v4'

# Database Configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///betting_bot.db')

# Voice Options (ElevenLabs Voice IDs)
VOICE_OPTIONS = {
    "Taylor Swift": "21m00Tcm4TlvDq8ikWAM",
    "Morgan Freeman": "9BWtwzW0fW0X0Y2Y0Y2Y0",
    "Arnold Schwarzenegger": "2EiwWnXFnvU5JabPnv8n",
    "Snoop Dogg": "2EiwWnXFnvU5JabPnv8n",
    "Barack Obama": "2EiwWnXFnvU5JabPnv8n",
    "Donald Trump": "2EiwWnXFnvU5JabPnv8n",
    "Joe Rogan": "2EiwWnXFnvU5JabPnv8n",
    "Elon Musk": "2EiwWnXFnvU5JabPnv8n"
}

# Bet Types
BET_TYPES = {
    "ML": "Money Line",
    "SPREAD": "Point Spread", 
    "OVER": "Over",
    "UNDER": "Under",
    "TOTAL": "Total Points"
}

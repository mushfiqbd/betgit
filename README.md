# 🎰 Sports Betting Telegram Bot

A sophisticated Telegram bot for sports betting-style entertainment with AI voice generation using ElevenLabs.

## ✨ Features

- **Smart Bet Parsing**: Parse natural language betting commands like "Real Madrid ML $500"
- **AI Voice Generation**: Get voice confirmations using famous voices (Taylor Swift, Morgan Freeman, etc.)
- **Voice Selection**: Choose your preferred voice from a list of celebrity voices
- **User Management**: Track user preferences, betting history, and statistics
- **Casino Interface**: Professional sportsbook-style user experience
- **Database Storage**: SQLite database for user data and betting history

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.10+ (tested on Windows with Python 3.14)
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- OpenAI API Key (https://platform.openai.com) for AI Q&A/suggestions
- ElevenLabs API Key (https://elevenlabs.io) for voice (optional)

### 2. Installation (Windows PowerShell)

```powershell
# Go to project folder
Set-Location -Path "F:\Beting bot"

# Install dependencies for current user
python -m pip install --user -r requirements.txt

# Create .env (or edit manually)
"TELEGRAM_BOT_TOKEN=your_token_here`nOPENAI_API_KEY=your_openai_key_here`nELEVENLABS_API_KEY=optional_elevenlabs_key_here`nDATABASE_URL=sqlite:///betting_bot.db" | Out-File -Encoding utf8 .env
```

### 3. Configuration

Edit the `.env` file with your credentials:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
OPENAI_API_KEY=your_openai_api_key_here
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here   # optional
DATABASE_URL=sqlite:///betting_bot.db
```
Notes:
- Keep real tokens in `.env` (loaded by `config.py`).
- Windows console emoji issues are handled in `bot.py` via UTF-8.

### 4. Run the Bot

```powershell
Set-Location -Path "F:\Beting bot"
python bot.py
```
If you see: Conflict: terminated by other getUpdates request → stop other bot instances.

## 🎯 How to Use

### Basic Commands

- `/start` - Welcome message and setup
- `/help` - Show betting examples and format
- `/voice` - Change your preferred voice
- `/stats` - View your betting statistics
- `/my_bets` - View your recent bets
 - `/ask` - Ask OpenAI a question (uses your OPENAI_API_KEY)
 - `/ai_bet` - AI-suggested simulated bet (optional team hint)

Examples:
```text
/ask Messi er agami match niye bolo?
/ai_bet Real Madrid
```

### Placing Bets

Send messages in these formats:
- `Real Madrid ML $500`
- `Lakers SPREAD $250`
- `Over 2.5 TOTAL $100`
- `Barcelona Money Line $750`

### Available Bet Types

- **ML** - Money Line
- **SPREAD** - Point Spread
- **OVER** - Over
- **UNDER** - Under
- **TOTAL** - Total Points

### Voice Options

- Taylor Swift
- Morgan Freeman
- Arnold Schwarzenegger
- Snoop Dogg
- Barack Obama
- Donald Trump
- Joe Rogan
- Elon Musk

## 🏗️ Project Structure

```
F:\Beting bot\
├── bot.py              # Main bot application
├── config.py           # Configuration settings
├── database.py         # Database management
├── bet_parser.py       # Bet parsing logic
├── voice_generator.py  # ElevenLabs TTS integration
├── requirements.txt    # Python dependencies
├── README.md          # This file
├── betting_bot.db     # SQLite database (created automatically)
└── unused\            # Non-essential prod/ops files stored here
```

## 🔧 Configuration

### Voice Settings

Edit `config.py` to modify available voices:

```python
VOICE_OPTIONS = {
    "Taylor Swift": "21m00Tcm4TlvDq8ikWAM",
    "Morgan Freeman": "9BWtwzW0fW0X0Y2Y0Y2Y0",
    # Add more voices...
}
```

### Bet Types

Modify `config.py` to add new bet types:

```python
BET_TYPES = {
    "ML": "Money Line",
    "SPREAD": "Point Spread",
    # Add more types...
}
```

## 🚀 Deployment

### Local Development

1. Run the bot locally for testing
2. Use ngrok for webhook testing: `ngrok http 8000`

### Production Deployment

#### Option 1: VPS/Cloud Server

1. Set up a VPS (DigitalOcean, AWS, etc.)
2. Install Python and dependencies
3. Set up environment variables
4. Run with process manager (PM2, systemd)

#### Option 2: Heroku

1. Create `Procfile`:
```
worker: python bot.py
```

2. Deploy to Heroku:
```bash
git init
git add .
git commit -m "Initial commit"
heroku create your-bot-name
git push heroku main
```

#### Option 3: Railway/Render

1. Connect your GitHub repository
2. Set environment variables in dashboard
3. Deploy automatically

## 🛠️ Development

### Adding New Features

1. **New Voice**: Add to `VOICE_OPTIONS` in `config.py`
2. **New Bet Type**: Add to `BET_TYPES` in `config.py`
3. **New Command**: Add handler in `bot.py`

### Database Schema

- **users**: User information and preferences
- **bets**: Betting history and details

### Error Handling

The bot includes comprehensive error handling for:
- Invalid bet formats
- API failures
- Database errors
- Voice generation issues

## 📊 Monitoring

- Check logs for errors and performance
- Monitor database size and growth
- Track API usage (ElevenLabs)
- Monitor bot uptime

## 🔒 Security

- Environment variables for sensitive data
- Input validation for all user inputs
- Rate limiting (implement if needed)
- Database sanitization

## 🆘 Troubleshooting

### Common Issues

1. **Bot not responding**: Check token and internet connection
2. **Voice not working**: Verify ElevenLabs API key
3. **Database errors**: Check file permissions
4. **Import errors**: Install all requirements

### Debug Mode

Enable debug logging:

```python
logging.basicConfig(level=logging.DEBUG)
```

## 📝 License

This project is for educational and entertainment purposes only. Please ensure compliance with local laws and regulations regarding gambling and betting.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📞 Support

For issues and questions:
- Check the troubleshooting section
- Review logs for error messages
- Ensure all dependencies are installed
- Verify API keys are correct

---

**Disclaimer**: This bot is for entertainment purposes only. No real money is involved in the betting system.

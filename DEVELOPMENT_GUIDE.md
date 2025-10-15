# 🚀 Sports Betting Bot - Complete Development Guide

## 📋 Table of Contents
1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [File Structure](#file-structure)
4. [Core Components](#core-components)
5. [Setup & Installation](#setup--installation)
6. [Configuration](#configuration)
7. [Database Schema](#database-schema)
8. [API Integration](#api-integration)
9. [Bot Features](#bot-features)
10. [Development Workflow](#development-workflow)
11. [Testing](#testing)
12. [Deployment](#deployment)
13. [Troubleshooting](#troubleshooting)
14. [Contributing](#contributing)

---

## 🎯 Project Overview

This is a comprehensive Telegram-based sports betting bot with cryptocurrency integration, AI assistance, and voice generation capabilities.

### Key Features
- 🎮 **Interactive Button Interface** - Pure button-based UI (no commands except `/start`)
- 💰 **Cryptocurrency System** - Deposit/withdrawal with admin approval
- 🤖 **AI Integration** - OpenAI-powered Q&A and betting suggestions
- 🎵 **Voice Generation** - ElevenLabs voice confirmations
- 📊 **Betting Engine** - Automated odds calculation and results
- 👑 **Admin Panel** - Complete admin management system
- 🔒 **Security** - Rate limiting and input validation

### Technology Stack
- **Backend**: Python 3.8+
- **Bot Framework**: python-telegram-bot
- **Database**: SQLite3
- **AI**: OpenAI API
- **Voice**: ElevenLabs API
- **Deployment**: Docker + Docker Compose

---

## 🏗️ System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Telegram      │    │   Betting Bot   │    │   External      │
│   Users         │◄──►│   (bot.py)      │◄──►│   APIs          │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   Database      │
                       │   (SQLite)     │
                       └─────────────────┘
```

### Core Modules
- **bot.py** - Main application entry point
- **database.py** - Data persistence layer
- **crypto_system.py** - Cryptocurrency operations
- **betting_engine.py** - Betting logic and calculations
- **ai_helper.py** - AI integration
- **voice_generator.py** - Voice synthesis
- **config.py** - Configuration management

---

## 📁 File Structure

```
F:\Beting bot\
├── 📁 Core Application Files
│   ├── bot.py                    # Main bot application
│   ├── database.py              # Database management
│   ├── crypto_system.py          # Cryptocurrency system
│   ├── betting_engine.py         # Betting logic
│   ├── bet_parser.py            # Bet parsing
│   ├── voice_generator.py       # Voice generation
│   ├── ai_helper.py             # AI assistance
│   └── config.py                # Configuration
├── 📁 Configuration Files
│   ├── requirements.txt          # Python dependencies
│   ├── .env                     # Environment variables
│   ├── env.production           # Production environment
│   └── env_example.txt          # Environment template
├── 📁 Database Files
│   ├── betting_bot.db           # SQLite database
│   └── bot.log                  # Application logs
├── 📁 Documentation
│   └── README.md                # Main documentation
├── 📁 Deployment Files
│   ├── deploy.sh                # Deployment script
│   ├── docker-compose.production.yml
│   └── Dockerfile.production
└── 📁 Unused Files (Archived)
    └── unused_files/
        ├── debug_bot.py
        ├── monitoring.py
        ├── production_bot.py
        ├── production_config.py
        ├── real_life_bot.py
        └── security.py
```

---

## 🔧 Core Components

### 1. Bot Application (`bot.py`)

**Main Class**: `BettingBot`

**Key Methods**:
- `start_command()` - Main interface with button navigation
- `button_callback()` - Handles all button interactions
- `handle_message()` - Processes text messages and bets
- `handle_photo()` - Processes image uploads (payment proofs)
- `notify_admins_deposit_request()` - Sends admin notifications
- `_handle_admin_approve_callback()` - Admin approval workflow
- `_handle_admin_reject_callback()` - Admin rejection workflow

**Button Flow Architecture**:
```
/start → Main Interface
├── 🎮 Betting
│   ├── Place Bet → Bet Input → Voice Confirmation → Result
│   └── My Bets → Bet History
├── 💰 Wallet Management
│   ├── Deposit → Currency Selection → Wallet Address → Payment Proof → Complete
│   ├── Withdraw → Add Wallet → Amount Input → Request Submission
│   └── My Wallets → Wallet List
├── 🤖 AI Features
│   ├── Ask AI → Q&A Interface
│   └── AI Betting Tips → AI Suggestions
├── 📊 Statistics
│   ├── My Stats → User Statistics
│   ├── Leaderboard → Top Users
│   └── Payment History → Transaction History
└── 👑 Admin Panel (Admin Only)
    ├── Payment Requests → Approve/Reject Deposits
    ├── View Users → User Management
    ├── Bot Statistics → System Stats
    └── Manage Admin Wallets → Wallet Management
```

### 2. Database Management (`database.py`)

**Main Class**: `DatabaseManager`

**Tables**:
- `users` - User accounts and balances
- `bets` - Betting history
- `live_odds` - Current betting odds
- `payment_history` - Transaction records
- `admin_wallets` - Admin wallet addresses

**Key Methods**:
- `create_user()` - Register new users
- `get_user()` - Retrieve user data
- `update_user_balance()` - Update user balance
- `add_bet()` - Record new bets
- `get_user_bets()` - Retrieve user bet history
- `is_admin()` - Check admin privileges

### 3. Cryptocurrency System (`crypto_system.py`)

**Main Class**: `CryptoSystem`

**Features**:
- Deposit/withdrawal request management
- Admin wallet management
- Payment proof handling
- Request approval/rejection workflow

**Key Methods**:
- `create_payment_request()` - Create deposit/withdrawal requests
- `approve_payment_request()` - Approve requests (updates balance)
- `reject_payment_request()` - Reject requests
- `get_payment_requests()` - Retrieve pending requests
- `get_admin_wallets()` - Get admin wallet addresses

### 4. Betting Engine (`betting_engine.py`)

**Main Class**: `BettingEngine`

**Features**:
- Odds calculation
- Bet result simulation (10% win rate, 90% loss rate)
- Payout calculations
- Fair and automated results

**Key Methods**:
- `calculate_odds()` - Calculate betting odds
- `simulate_bet_result()` - Determine bet outcome
- `calculate_payout()` - Calculate winnings

### 5. AI Integration (`ai_helper.py`)

**Main Class**: `AIHelper`

**Features**:
- OpenAI-powered Q&A system
- Betting suggestions and tips
- Context-aware responses

**Key Methods**:
- `ask_question()` - Process user questions
- `get_betting_tips()` - Generate betting suggestions

### 6. Voice Generation (`voice_generator.py`)

**Main Class**: `VoiceGenerator`

**Features**:
- ElevenLabs integration
- Voice confirmations for bets
- Customizable voice options

**Key Methods**:
- `generate_voice()` - Create voice messages
- `send_voice_confirmation()` - Send bet confirmations

---

## ⚙️ Setup & Installation

### Prerequisites
- Python 3.8 or higher
- Telegram Bot Token
- OpenAI API Key
- ElevenLabs API Key

### Installation Steps

1. **Clone/Download Project**
   ```bash
   # Navigate to project directory
   cd "F:\Beting bot"
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Configuration**
   ```bash
   # Copy environment template
   copy env_example.txt .env
   
   # Edit .env file with your API keys
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   OPENAI_API_KEY=your_openai_key_here
   ELEVENLABS_API_KEY=your_elevenlabs_key_here
   ```

4. **Database Initialization**
   ```bash
   # Database will be created automatically on first run
   python bot.py
   ```

5. **Set Admin User**
   ```python
   # In bot.py, add your user ID to admin list
   # Or use the admin panel to promote users
   ```

---

## 🔧 Configuration

### Environment Variables (`.env`)

```env
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=8306444578:AAF8CTcWFBsVg5RIfb1IOTiwoPgQorVVgLw

# AI Configuration
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-3.5-turbo

# Voice Configuration
ELEVENLABS_API_KEY=your_elevenlabs_api_key
VOICE_ID=21m00Tcm4TlvDq8ikWAM

# Database Configuration
DATABASE_PATH=betting_bot.db

# Bot Settings
DEFAULT_BALANCE=0.0
WIN_RATE=0.1
LOSS_RATE=0.9
```

### Bot Configuration (`config.py`)

```python
# Bot Settings
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')

# Voice Options
VOICE_OPTIONS = {
    'voice_id': '21m00Tcm4TlvDq8ikWAM',
    'model_id': 'eleven_monolingual_v1',
    'voice_settings': {
        'stability': 0.5,
        'similarity_boost': 0.5
    }
}
```

---

## 🗄️ Database Schema

### Users Table
```sql
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    balance REAL DEFAULT 0.0,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Bets Table
```sql
CREATE TABLE bets (
    bet_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    team TEXT NOT NULL,
    bet_type TEXT NOT NULL,
    amount REAL NOT NULL,
    odds REAL NOT NULL,
    result TEXT,
    payout REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (user_id)
);
```

### Payment Requests Table
```sql
CREATE TABLE payment_requests (
    request_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    type TEXT NOT NULL,
    currency TEXT NOT NULL,
    amount REAL NOT NULL,
    wallet_address TEXT,
    proof_file_id TEXT,
    status TEXT DEFAULT 'pending',
    admin_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (user_id)
);
```

### Admin Wallets Table
```sql
CREATE TABLE admin_wallets (
    wallet_id INTEGER PRIMARY KEY AUTOINCREMENT,
    currency TEXT NOT NULL,
    address TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🔌 API Integration

### Telegram Bot API
- **Framework**: python-telegram-bot
- **Features**: Inline keyboards, callback queries, file handling
- **Rate Limiting**: Built-in rate limiting for user actions

### OpenAI API
- **Model**: GPT-3.5-turbo
- **Usage**: Q&A system and betting suggestions
- **Rate Limiting**: Handled by OpenAI

### ElevenLabs API
- **Model**: eleven_monolingual_v1
- **Usage**: Voice generation for bet confirmations
- **Voice ID**: 21m00Tcm4TlvDq8ikWAM

---

## 🎮 Bot Features

### User Features

#### 1. Betting System
- **Place Bets**: Team selection, bet type (ML, Spread, Total), amount
- **Voice Confirmation**: ElevenLabs voice confirmation
- **Automatic Results**: 10% win rate, 90% loss rate
- **Fair System**: "All results are fair and automatically decided"

#### 2. Wallet Management
- **Deposit Flow**:
  1. Click "Deposit" → Select currency → Get wallet address
  2. Click "Paid" → Upload payment proof → Enter amount
  3. Click "Complete" → Submit for admin approval
- **Withdrawal Flow**:
  1. Click "Withdraw" → Add wallet address → Enter amount
  2. Submit request → Wait for admin approval
- **Wallet Management**: Add/remove wallet addresses

#### 3. AI Features
- **Ask AI**: General Q&A using OpenAI
- **AI Betting Tips**: AI-generated betting suggestions

#### 4. Statistics
- **My Stats**: Personal betting statistics
- **Leaderboard**: Top users by balance/winnings
- **Payment History**: Transaction history

### Admin Features

#### 1. Payment Management
- **View Requests**: See all pending deposit/withdrawal requests
- **Approve/Reject**: One-click approval with balance updates
- **Request Details**: View payment proofs and user information

#### 2. User Management
- **View Users**: List all users with statistics
- **User Details**: Individual user information and history

#### 3. System Management
- **Bot Statistics**: System-wide statistics
- **Admin Wallets**: Manage admin wallet addresses
- **Add Wallets**: Add new admin wallet addresses

---

## 🔄 Development Workflow

### 1. Local Development

```bash
# Start development server
python bot.py

# Check logs
tail -f bot.log

# Test specific features
python -c "from bot import BettingBot; bot = BettingBot(); print('Bot initialized successfully')"
```

### 2. Code Structure

#### Button Callback Pattern
```python
async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    
    # Route to appropriate handler based on callback data
    if data.startswith("cmd_"):
        await self._handle_main_callback(query, data)
    elif data.startswith("bet_"):
        await self._handle_bet_callback(query, data)
    # ... more patterns
```

#### Message Handling Pattern
```python
async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    user_id = message.from_user.id
    
    # Check if user is in deposit flow
    if user_id in self.deposit_states:
        await self.handle_deposit_amount_message(update, context)
        return
    
    # Check if message is a bet
    if self.bet_parser.is_valid_bet(message.text):
        await self.handle_bet_message(update, context)
        return
    
    # Default: show main interface
    await self.start_command(update, context)
```

### 3. Database Operations

#### User Management
```python
# Create user
user_id = 123456789
self.db.create_user(user_id, "username", "John", "Doe")

# Update balance
self.db.update_user_balance(user_id, 100.0)  # Add $100
self.db.update_user_balance(user_id, -50.0)  # Deduct $50

# Check admin status
is_admin = self.db.is_admin(user_id)
```

#### Payment Requests
```python
# Create deposit request
request_id = self.crypto.create_payment_request(
    user_id=user_id,
    request_type='deposit',
    currency='USDT',
    amount=100.0,
    wallet_address='admin_wallet_address'
)

# Approve request
success = self.crypto.approve_payment_request(request_id, "Approved")
```

---

## 🧪 Testing

### 1. Unit Testing

```python
# Test database operations
def test_user_creation():
    db = DatabaseManager()
    user_id = 999999999
    db.create_user(user_id, "testuser", "Test", "User")
    user = db.get_user(user_id)
    assert user['username'] == "testuser"

# Test betting engine
def test_betting_calculation():
    engine = BettingEngine()
    odds = engine.calculate_odds("Real Madrid", "ML")
    assert odds > 1.0
```

### 2. Integration Testing

```python
# Test complete deposit flow
async def test_deposit_flow():
    bot = BettingBot()
    
    # Simulate user clicking deposit button
    await bot._handle_deposit_callback(mock_query)
    
    # Simulate currency selection
    await bot._handle_deposit_currency_callback(mock_query, "USDT")
    
    # Simulate payment proof upload
    await bot.handle_photo(mock_update, mock_context)
    
    # Simulate amount input
    await bot.handle_deposit_amount_message(mock_update, mock_context)
    
    # Simulate completion
    await bot._handle_deposit_complete_callback(mock_query, request_id)
```

### 3. Manual Testing Checklist

#### User Flow Testing
- [ ] User registration via `/start`
- [ ] Deposit flow completion
- [ ] Withdrawal flow completion
- [ ] Betting with voice confirmation
- [ ] AI Q&A functionality
- [ ] Statistics viewing

#### Admin Flow Testing
- [ ] Admin panel access
- [ ] Payment request approval/rejection
- [ ] User management
- [ ] Wallet management
- [ ] System statistics

#### Error Handling Testing
- [ ] Invalid bet formats
- [ ] Insufficient balance
- [ ] Network timeouts
- [ ] API failures
- [ ] Database errors

---

## 🚀 Deployment

### 1. Production Setup

#### Environment Preparation
```bash
# Copy production environment
cp env.production .env

# Install production dependencies
pip install -r requirements.txt

# Set up admin user
python -c "
from database import DatabaseManager
db = DatabaseManager()
db.set_admin(YOUR_USER_ID, True)
"
```

#### Docker Deployment
```bash
# Build production image
docker build -f Dockerfile.production -t betting-bot .

# Run with docker-compose
docker-compose -f docker-compose.production.yml up -d
```

### 2. Monitoring

#### Log Monitoring
```bash
# View real-time logs
tail -f bot.log

# Check error logs
grep "ERROR" bot.log

# Monitor API calls
grep "HTTP Request" bot.log
```

#### Database Monitoring
```python
# Check database health
import sqlite3
conn = sqlite3.connect('betting_bot.db')
cursor = conn.cursor()

# Check user count
cursor.execute("SELECT COUNT(*) FROM users")
user_count = cursor.fetchone()[0]

# Check pending requests
cursor.execute("SELECT COUNT(*) FROM payment_requests WHERE status='pending'")
pending_count = cursor.fetchone()[0]

conn.close()
```

### 3. Backup Strategy

#### Database Backup
```bash
# Daily backup
cp betting_bot.db "backups/betting_bot_$(date +%Y%m%d).db"

# Automated backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
cp betting_bot.db "backups/betting_bot_$DATE.db"
echo "Backup created: betting_bot_$DATE.db"
```

---

## 🔧 Troubleshooting

### Common Issues

#### 1. Bot Not Starting
```bash
# Check Python version
python --version  # Should be 3.8+

# Check dependencies
pip list | grep telegram

# Check environment variables
python -c "from config import TELEGRAM_BOT_TOKEN; print('Token loaded:', bool(TELEGRAM_BOT_TOKEN))"
```

#### 2. Database Issues
```python
# Check database connection
import sqlite3
try:
    conn = sqlite3.connect('betting_bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables:", tables)
    conn.close()
except Exception as e:
    print("Database error:", e)
```

#### 3. API Integration Issues
```python
# Test OpenAI connection
from ai_helper import AIHelper
ai = AIHelper()
response = ai.ask_question("Test question")
print("AI Response:", response)

# Test ElevenLabs connection
from voice_generator import VoiceGenerator
voice = VoiceGenerator()
# Check if API key is valid
```

#### 4. Button Callback Issues
```python
# Check callback patterns
patterns = [
    "^cmd_",      # Main commands
    "^bet_",      # Betting actions
    "^deposit_",  # Deposit flow
    "^withdraw_", # Withdrawal flow
    "^admin_",    # Admin actions
]

# Verify all patterns are registered in main()
```

### Error Logs Analysis

#### Common Error Patterns
```bash
# Telegram API errors
grep "telegram.error" bot.log

# Database errors
grep "sqlite3" bot.log

# API timeout errors
grep "timeout" bot.log

# Rate limiting errors
grep "rate" bot.log
```

### Performance Optimization

#### 1. Database Optimization
```sql
-- Add indexes for better performance
CREATE INDEX idx_users_user_id ON users(user_id);
CREATE INDEX idx_bets_user_id ON bets(user_id);
CREATE INDEX idx_payment_requests_user_id ON payment_requests(user_id);
CREATE INDEX idx_payment_requests_status ON payment_requests(status);
```

#### 2. Memory Management
```python
# Clear deposit states periodically
def cleanup_deposit_states(self):
    current_time = datetime.now()
    expired_users = []
    
    for user_id, state in self.deposit_states.items():
        if (current_time - state['timestamp']).seconds > 3600:  # 1 hour
            expired_users.append(user_id)
    
    for user_id in expired_users:
        del self.deposit_states[user_id]
```

---

## 🤝 Contributing

### Development Guidelines

#### 1. Code Style
- Follow PEP 8 guidelines
- Use type hints where possible
- Add docstrings to all functions
- Keep functions focused and small

#### 2. Database Changes
- Always use migrations for schema changes
- Test database operations thoroughly
- Backup before making changes

#### 3. API Integration
- Handle all possible error cases
- Implement proper rate limiting
- Add logging for debugging

#### 4. Testing
- Write tests for new features
- Test both success and failure cases
- Verify database integrity

### Pull Request Process

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/new-feature`
3. **Make changes**: Follow coding guidelines
4. **Add tests**: Ensure all tests pass
5. **Update documentation**: Update relevant docs
6. **Submit PR**: Include description and test results

### Code Review Checklist

- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] Documentation updated
- [ ] No breaking changes
- [ ] Error handling implemented
- [ ] Logging added where needed

---

## 📚 Additional Resources

### Documentation Links
- [python-telegram-bot Documentation](https://python-telegram-bot.readthedocs.io/)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [ElevenLabs API Documentation](https://docs.elevenlabs.io/)
- [SQLite Documentation](https://www.sqlite.org/docs.html)

### Useful Commands

#### Development
```bash
# Start bot in development mode
python bot.py

# Check bot status
ps aux | grep python

# View recent logs
tail -n 100 bot.log

# Test database connection
python -c "from database import DatabaseManager; db = DatabaseManager(); print('DB OK')"
```

#### Production
```bash
# Deploy with Docker
docker-compose -f docker-compose.production.yml up -d

# Check container status
docker ps

# View container logs
docker logs betting-bot

# Backup database
docker exec betting-bot cp betting_bot.db /backup/
```

---

## 🎯 Future Enhancements

### Planned Features
- [ ] Multi-language support
- [ ] Advanced analytics dashboard
- [ ] Mobile app integration
- [ ] Real-time odds updates
- [ ] Social features (friends, groups)
- [ ] Advanced AI betting strategies

### Technical Improvements
- [ ] Redis caching for better performance
- [ ] PostgreSQL migration for scalability
- [ ] Microservices architecture
- [ ] Real-time notifications
- [ ] Advanced security features

---

## 📞 Support

For technical support or questions:
- Check the troubleshooting section first
- Review error logs for specific issues
- Test individual components in isolation
- Verify API keys and environment setup

---

**Last Updated**: October 14, 2025  
**Version**: 1.0.0  
**Maintainer**: Development Team

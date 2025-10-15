import asyncio
import logging
import random
from datetime import datetime, timedelta
import sys
from ai_helper import AIHelper
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.constants import ParseMode

from config import TELEGRAM_BOT_TOKEN, VOICE_OPTIONS
from database import DatabaseManager
from bet_parser import BetParser
from voice_generator import VoiceGenerator
from betting_engine import BettingEngine
from crypto_system import CryptoSystem
from sports_api import SportsAPIService
from bot_ui import BotUI

# Ensure UTF-8 console output (Windows consoles may default to cp1252)
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class BettingBot:
    def __init__(self):
        self.db = DatabaseManager()
        self.bet_parser = BetParser()
        self.voice_generator = VoiceGenerator()
        self.betting_engine = BettingEngine()
        self.ai = AIHelper()
        self.crypto = CryptoSystem()
        self.sports_api = SportsAPIService()
        self.ui = BotUI(self.sports_api, self.betting_engine)
        self.rate_limits = {}  # Simple rate limiting
        self.deposit_states = {}  # Track deposit flow states
        self.application = None  # Will be set in main()
    
    def check_rate_limit(self, user_id: int) -> bool:
        """Check if user is within rate limit (10 requests per minute)"""
        now = datetime.now()
        if user_id not in self.rate_limits:
            self.rate_limits[user_id] = []
        
        # Remove requests older than 1 minute
        self.rate_limits[user_id] = [
            req_time for req_time in self.rate_limits[user_id]
            if now - req_time < timedelta(minutes=1)
        ]
        
        # Check if under limit
        if len(self.rate_limits[user_id]) >= 10:
            return False
        
        # Add current request
        self.rate_limits[user_id].append(now)
        return True
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        user_id = user.id
        
        # Create user if doesn't exist
        if not self.db.get_user(user_id):
            self.db.create_user(
                user_id=user_id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
            # Set first user as admin
            if user_id == 6251161332:  # Your user ID
                self.db.set_admin(user_id, True)
        
        user_data = self.db.get_user(user_id)
        if not user_data:
            user_data = {
                'balance': 0.0,
                'is_admin': False,
                'preferred_voice': 'Taylor Swift'
            }
        
        # Use enhanced UI
        try:
            welcome_message, reply_markup = self.ui.create_enhanced_main_menu(user_data)
            await update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            logger.error(f"Error in enhanced UI: {e}")
            # Fallback to simple UI
            welcome_message = f"""🎰 Welcome to Sports Betting Bot! 🎰

Hey {user.first_name}! I'm your personal sports betting assistant with real cryptocurrency support.

💰 Your Balance: ${user_data.get('balance', 0.0):,.2f}

📱 BUTTON INTERFACE - Only /start Command Available
Use the buttons below to navigate and place bets.

How to place a bet:
Just send me a message like:
• Real Madrid ML $500
• Lakers SPREAD $250
• Over 2.5 TOTAL $100

Current Voice: {user_data.get('preferred_voice', 'Taylor Swift')}

Choose an option below:"""
            
            # Create simple keyboard with 3 buttons per row
            keyboard = [
                [InlineKeyboardButton("💰 Balance", callback_data="cmd_balance"),
                 InlineKeyboardButton("📊 Stats", callback_data="cmd_stats"),
                 InlineKeyboardButton("🎯 My Bets", callback_data="cmd_my_bets")],
                [InlineKeyboardButton("📈 Live Odds", callback_data="cmd_odds"),
                 InlineKeyboardButton("🏆 Leaderboard", callback_data="cmd_leaderboard"),
                 InlineKeyboardButton("💡 Tips", callback_data="cmd_tips")],
                [InlineKeyboardButton("🎤 Voice", callback_data="cmd_voice"),
                 InlineKeyboardButton("🤖 Ask AI", callback_data="cmd_ask"),
                 InlineKeyboardButton("🎲 AI Bet", callback_data="cmd_ai_bet")],
                [InlineKeyboardButton("💳 My Wallets", callback_data="cmd_my_wallets"),
                 InlineKeyboardButton("📝 Payment History", callback_data="cmd_payment_history"),
                 InlineKeyboardButton("💸 Deposit", callback_data="cmd_deposit")],
                [InlineKeyboardButton("💵 Withdraw", callback_data="cmd_withdraw"),
                 InlineKeyboardButton("❓ Help", callback_data="cmd_help")]
            ]
            
            # Add admin buttons if user is admin
            if user_data.get('is_admin', False):
                keyboard.append([InlineKeyboardButton("🔧 Admin Panel", callback_data="cmd_admin")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    
    async def voice_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle voice selection callback"""
        query = update.callback_query
        await query.answer()
        
        if query.data.startswith("voice_"):
            voice_name = query.data.replace("voice_", "")
            user_id = query.from_user.id
            
            # Update user's voice preference
            if self.db.update_user_voice(user_id, voice_name):
                await query.edit_message_text(
                    f"✅ Voice changed to: *{voice_name}*",
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                await query.edit_message_text("❌ Failed to update voice preference.")
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline button callbacks"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        data = query.data
        
        # Check rate limit
        if not self.check_rate_limit(user_id):
            await query.edit_message_text("⏰ Rate limit exceeded. Please wait a moment before trying again.")
            return
        
        # Route to appropriate command based on callback data
        if data == "cmd_balance":
            await self._handle_balance_callback(query)
        elif data == "cmd_stats":
            await self._handle_stats_callback(query)
        elif data == "cmd_my_bets":
            await self._handle_my_bets_callback(query)
        elif data == "cmd_odds":
            await self._handle_odds_callback(query)
        elif data == "cmd_leaderboard":
            await self._handle_leaderboard_callback(query)
        elif data == "cmd_tips":
            await self._handle_tips_callback(query)
        elif data == "cmd_voice":
            await self._handle_voice_callback(query)
        elif data == "cmd_ask":
            await self._handle_ask_callback(query)
        elif data == "cmd_ai_bet":
            await self._handle_ai_bet_callback(query)
        elif data == "cmd_my_wallets":
            await self._handle_my_wallets_callback(query)
        elif data == "cmd_payment_history":
            await self._handle_payment_history_callback(query)
        elif data == "cmd_deposit":
            await self._handle_deposit_callback(query)
        elif data == "cmd_withdraw":
            await self._handle_withdraw_callback(query)
        elif data == "cmd_help":
            await self._handle_help_callback(query)
        elif data == "cmd_admin":
            await self._handle_admin_callback(query)
        elif data == "back_to_main":
            await self._handle_back_to_main_callback(query)
        elif data.startswith("deposit_currency_"):
            currency = data.replace("deposit_currency_", "")
            await self._handle_deposit_currency_callback(query, currency)
        elif data.startswith("deposit_paid_"):
            currency = data.replace("deposit_paid_", "")
            await self._handle_deposit_paid_callback(query, currency)
        elif data.startswith("deposit_complete_"):
            parts = data.replace("deposit_complete_", "").split("_")
            currency = parts[0]
            amount = parts[1]
            await self._handle_deposit_complete_callback(query, currency, amount)
        elif data.startswith("admin_approve_"):
            request_id = int(data.replace("admin_approve_", ""))
            await self._handle_admin_approve_callback(query, request_id)
        elif data.startswith("admin_reject_"):
            request_id = int(data.replace("admin_reject_", ""))
            await self._handle_admin_reject_callback(query, request_id)
        elif data.startswith("admin_view_"):
            request_id = int(data.replace("admin_view_", ""))
            await self._handle_admin_view_callback(query, request_id)
        elif data == "cmd_add_wallet":
            await self._handle_add_wallet_callback(query)
        elif data.startswith("withdraw_currency_"):
            currency = data.replace("withdraw_currency_", "")
            await self._handle_withdraw_currency_callback(query, currency)
        elif data.startswith("add_wallet_currency_"):
            currency = data.replace("add_wallet_currency_", "")
            await self._handle_add_wallet_currency_callback(query, currency)
        elif data == "cmd_payment_requests":
            await self._handle_payment_requests_callback(query)
        elif data == "cmd_users":
            await self._handle_users_callback(query)
        elif data == "cmd_bot_stats":
            await self._handle_bot_stats_callback(query)
        elif data == "cmd_admin_wallets":
            await self._handle_admin_wallets_callback(query)
        elif data == "cmd_add_admin_wallet":
            await self._handle_add_admin_wallet_callback(query)
        elif data == "cmd_quick_bet":
            await self.ui.show_quick_bet_interface(update, context)
        elif data == "cmd_live_games":
            await self.ui.show_live_games(update, context)
        elif data == "cmd_enhanced_stats":
            await self.ui.show_betting_stats(update, context)
        elif data.startswith("bet_game_"):
            await self._handle_game_bet_callback(query, data)
        elif data.startswith("bet_team_"):
            await self._handle_team_bet_callback(query, data)
        elif data.startswith("bet_total_"):
            await self._handle_total_bet_callback(query, data)
        elif data.startswith("bet_amount_"):
            await self._handle_bet_amount_callback(query, data)
        elif data.startswith("quick_bet_"):
            await self._handle_quick_bet_callback(query, data)
        elif data.startswith("view_odds_"):
            # view_odds_{game_id}
            game_id = data.replace("view_odds_", "")
            await self.ui.show_game_odds(update, context, game_id)
    
    async def _handle_balance_callback(self, query):
        """Handle balance button callback"""
        user_data = self.db.get_user(query.from_user.id)
        if not user_data:
            await query.edit_message_text("❌ User not found. Please use /start first.")
            return
        
        current_balance = user_data['balance']
        
        balance_message = f"""💰 *Your Betting Balance*

💵 *Current Balance:* ${current_balance:,.2f}

*Available Actions:*
• /deposit - Add cryptocurrency
• /withdraw - Remove cryptocurrency
• /my_wallets - Manage wallets
• /payment_history - View transactions

*Note:* This is real money for betting purposes."""
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(balance_message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def _handle_stats_callback(self, query):
        """Handle stats button callback"""
        user = self.db.get_user(query.from_user.id)
        if not user:
            await query.edit_message_text("❌ User not found. Please use /start first.")
            return
        
        username_display = user['username'] if user['username'] else 'N/A'
        stats_message = f"""📊 *Your Betting Statistics*

👤 *User:* {user['first_name']} (@{username_display})
🎤 *Voice:* {user['preferred_voice']}
🎯 *Total Bets:* {user['total_bets']}
💰 *Total Wagered:* ${user['total_wagered']:,.2f}
📅 *Member Since:* {user['created_at']}

Keep betting responsibly! 🎰"""
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(stats_message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def _handle_my_bets_callback(self, query):
        """Handle my bets button callback"""
        bets = self.db.get_user_bets(query.from_user.id, limit=5)
        
        if not bets:
            message = "📝 No bets found. Place your first bet!"
        else:
            message = "📝 *Your Recent Bets:*\n\n"
        for bet in bets:
            status_emoji = "✅" if bet['status'] == 'won' else "❌" if bet['status'] == 'lost' else "⏳"
            message += f"{status_emoji} {bet['team']} {bet['bet_type']} ${bet['amount']:,.0f}\n"
            message += f"   📅 {bet['created_at']}\n\n"
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def _handle_odds_callback(self, query):
        """Handle odds button callback"""
        popular_teams = self.betting_engine.get_popular_teams()[:5]
        live_odds = await self.betting_engine.get_live_odds(popular_teams)
        
        odds_message = "📊 *Live Odds*\n\n"
        
        for team in popular_teams:
            team_odds = live_odds.get(team, [])
            if team_odds:
                odds_message += f"🏆 *{team}*\n"
                for odds_data in team_odds[:3]:
                    odds_message += f"• {odds_data.bet_type}: {odds_data.odds:.2f} ({odds_data.probability:.1%})\n"
                odds_message += "\n"
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(odds_message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def _handle_leaderboard_callback(self, query):
        """Handle leaderboard button callback"""
        leaderboard = self.db.get_leaderboard(10)
        
        if not leaderboard:
            message = "📊 No betting data available yet. Be the first to place a bet!"
        else:
            message = "🏆 *Top Bettors Leaderboard*\n\n"
        
        for i, player in enumerate(leaderboard, 1):
            emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else str(i) + "."
            name = player['first_name'] or player['username'] or "Anonymous"
            profit = player['total_profit']
            profit_emoji = "💰" if profit > 0 else "📉" if profit < 0 else "➖"
            
            message += f"{emoji} {name}\n"
            message += f"   {profit_emoji} Profit: ${profit:,.2f}\n"
            message += f"   🎯 Bets: {player['total_bets']}\n"
            message += f"   💵 Wagered: ${player['total_wagered']:,.2f}\n\n"
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def _handle_tips_callback(self, query):
        """Handle tips button callback"""
        tips = self.betting_engine.get_betting_tips()
        
        tips_message = "💡 *Betting Tips & Advice*\n\n"
        for tip in tips:
            tips_message += tip + "\n\n"
        
        tips_message += "Remember: Bet responsibly and within your means! 🎯"
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(tips_message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def _handle_voice_callback(self, query):
        """Handle voice button callback"""
        keyboard = []
        voices = self.voice_generator.get_available_voices()
        
        for voice_name in voices.keys():
            keyboard.append([InlineKeyboardButton(voice_name, callback_data=f"voice_{voice_name}")])
        
        keyboard.append([InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🎤 *Choose your preferred voice:*",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _handle_ask_callback(self, query):
        """Handle ask AI button callback"""
        await query.edit_message_text(
            "🤖 Ask AI a Question\n\n"
            "Send your question as a regular message.\n\n"
            "Example: What are the best betting strategies?\n\n"
            "The AI will respond with helpful betting advice!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main")
            ]])
        )
    
    async def _handle_ai_bet_callback(self, query):
        """Handle AI bet button callback"""
        await query.edit_message_text(
            "🎲 Get AI Betting Suggestion\n\n"
            "Send your request as a regular message.\n\n"
            "Example: Suggest a bet for Real Madrid\n\n"
            "The AI will analyze and suggest betting options!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main")
            ]])
        )
    
    async def _handle_my_wallets_callback(self, query):
        """Handle my wallets button callback"""
        wallets = self.crypto.get_user_wallets(query.from_user.id)
        
        if not wallets:
            message = """💳 *No Wallet Addresses Found*

You haven't added any wallet addresses yet.
Use /deposit or /withdraw to add wallet addresses automatically."""
        else:
            message = "💳 *Your Wallet Addresses:*\n\n"
            
            for wallet in wallets:
                verified_badge = "✅" if wallet['is_verified'] else "⏳"
                message += f"{verified_badge} *{wallet['currency']}*\n"
                message += f"Address: `{wallet['address']}`\n"
                message += f"Status: {'Verified' if wallet['is_verified'] else 'Pending'}\n"
                message += f"Added: {wallet['created_at']}\n\n"
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def _handle_payment_history_callback(self, query):
        """Handle payment history button callback"""
        requests = self.crypto.get_user_payment_requests(query.from_user.id)
        
        if not requests:
            message = "📝 No payment history found."
        else:
            message = "📝 *Payment History:*\n\n"
            
            for request in requests:
                status_emoji = {
                    'pending': '⏳',
                    'approved': '✅',
                    'rejected': '❌'
                }.get(request.status, '❓')
                
                message += f"{status_emoji} *{request.type.upper()}*\n"
                message += f"Currency: {request.currency}\n"
                message += f"Amount: {request.amount}\n"
                message += f"Status: {request.status}\n"
                message += f"Date: {request.created_at}\n"
                if request.admin_notes:
                    message += f"Notes: {request.admin_notes}\n"
                message += "\n"
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def _handle_deposit_callback(self, query):
        """Handle deposit button callback"""
        # Get supported currencies
        currencies = self.crypto.get_supported_currencies()
        
        keyboard = []
        for currency_info in currencies:
            currency = currency_info['currency']
            name = currency_info['name']
            min_deposit = currency_info['min_deposit']
            keyboard.append([InlineKeyboardButton(
                f"{currency} ({name}) - Min: {min_deposit}", 
                callback_data=f"deposit_currency_{currency}"
            )])
        
        keyboard.append([InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "💸 Choose Cryptocurrency for Deposit\n\n"
            "Select a cryptocurrency to see deposit instructions:",
            reply_markup=reply_markup
        )
    
    async def _handle_withdraw_callback(self, query):
        """Handle withdraw button callback"""
        user_id = query.from_user.id
        
        # Check user balance
        user_data = self.db.get_user(user_id)
        if not user_data:
            await query.edit_message_text("❌ User not found. Please use /start first.")
            return
        
        current_balance = user_data['balance']
        
        if current_balance <= 0:
            await query.edit_message_text(
                f"❌ Insufficient Balance!\n\n"
                f"💵 Current Balance: ${current_balance:,.2f}\n\n"
                f"You need to deposit funds first before withdrawing.\n"
                f"Use the Deposit button to add funds to your account.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main")
                ]])
            )
            return
        
        # Get user wallets
        wallets = self.crypto.get_user_wallets(user_id)
        
        if not wallets:
            await query.edit_message_text(
                "💵 Withdraw Cryptocurrency\n\n"
                "You need to add a wallet address first.\n\n"
                "To add a wallet:\n"
                "1. Click 'Add Wallet' button below\n"
                "2. Select your cryptocurrency\n"
                "3. Enter your wallet address\n\n"
                "After adding a wallet, you can request withdrawals.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ Add Wallet", callback_data="cmd_add_wallet")],
                    [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main")]
                ])
            )
            return
        
        # Show withdrawal options
        keyboard = []
        for wallet in wallets:
            currency = wallet['currency']
            address = wallet['address']
            verified_badge = "✅" if wallet['is_verified'] else "⏳"
            keyboard.append([InlineKeyboardButton(
                f"{verified_badge} Withdraw {currency}", 
                callback_data=f"withdraw_currency_{currency}"
            )])
        
        keyboard.append([InlineKeyboardButton("➕ Add New Wallet", callback_data="cmd_add_wallet")])
        keyboard.append([InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"💵 Withdraw Cryptocurrency\n\n"
            f"💰 Available Balance: ${current_balance:,.2f}\n\n"
            f"Select a wallet to withdraw from:",
            reply_markup=reply_markup
        )
    
    async def _handle_help_callback(self, query):
        """Handle help button callback"""
        examples = self.bet_parser.get_bet_examples()
        examples_text = "\n".join(["• " + example for example in examples])
        
        help_message = f"""📋 Betting Guide

Bet Format:
Team Name BetType $Amount

Available Bet Types:
• ML - Money Line
• SPREAD - Point Spread  
• OVER - Over
• UNDER - Under
• TOTAL - Total Points

Examples:
{examples_text}

Voice Settings:
Use the Voice button to change your preferred voice for bet confirmations.

Need Help?
Contact support if you have any questions!"""
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(help_message, reply_markup=reply_markup)
    
    async def _handle_admin_callback(self, query):
        """Handle admin button callback"""
        user_id = query.from_user.id
        
        if not self.db.is_admin(user_id):
            await query.edit_message_text("❌ Access denied. Admin privileges required.")
            return
        
        admin_message = """🔧 Admin Panel

Available Actions:
• View payment requests
• Approve/reject payments
• Add admin wallets
• View all users
• Bot statistics

Select an action below:"""
        
        keyboard = [
            [InlineKeyboardButton("📋 Payment Requests", callback_data="cmd_payment_requests")],
            [InlineKeyboardButton("👥 View Users", callback_data="cmd_users")],
            [InlineKeyboardButton("📊 Bot Statistics", callback_data="cmd_bot_stats")],
            [InlineKeyboardButton("🏦 Manage Admin Wallets", callback_data="cmd_admin_wallets")],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(admin_message, reply_markup=reply_markup)
    
    async def _handle_back_to_main_callback(self, query):
        """Handle back to main menu callback"""
        user_id = query.from_user.id
        user_data = self.db.get_user(user_id)
        balance = user_data['balance'] if user_data else 0.0
        is_admin = user_data['is_admin'] if user_data else False
        
        welcome_message = f"""🎰 Welcome to Sports Betting Bot! 🎰

Hey {query.from_user.first_name}! I'm your personal sports betting assistant with real cryptocurrency support.

💰 Your Balance: ${balance:,.2f}

📱 BUTTON INTERFACE - Only /start Command Available
Use the buttons below to navigate and place bets.

How to place a bet:
Just send me a message like:
• Real Madrid ML $500
• Lakers SPREAD $250
• Over 2.5 TOTAL $100

Current Voice: {user_data['preferred_voice'] if user_data else 'Taylor Swift'}

Choose an option below:"""
        
        # Create inline keyboard with 3 buttons per row
        keyboard = [
            [InlineKeyboardButton("💰 Balance", callback_data="cmd_balance"),
             InlineKeyboardButton("📊 Stats", callback_data="cmd_stats"),
             InlineKeyboardButton("🎯 My Bets", callback_data="cmd_my_bets")],
            [InlineKeyboardButton("📈 Live Odds", callback_data="cmd_odds"),
             InlineKeyboardButton("🏆 Leaderboard", callback_data="cmd_leaderboard"),
             InlineKeyboardButton("💡 Tips", callback_data="cmd_tips")],
            [InlineKeyboardButton("🎤 Voice", callback_data="cmd_voice"),
             InlineKeyboardButton("🤖 Ask AI", callback_data="cmd_ask"),
             InlineKeyboardButton("🎲 AI Bet", callback_data="cmd_ai_bet")],
            [InlineKeyboardButton("💳 My Wallets", callback_data="cmd_my_wallets"),
             InlineKeyboardButton("📝 Payment History", callback_data="cmd_payment_history"),
             InlineKeyboardButton("💸 Deposit", callback_data="cmd_deposit")],
            [InlineKeyboardButton("💵 Withdraw", callback_data="cmd_withdraw"),
             InlineKeyboardButton("❓ Help", callback_data="cmd_help")]
        ]
        
        # Add admin buttons if user is admin
        if is_admin:
            keyboard.append([InlineKeyboardButton("🔧 Admin Panel", callback_data="cmd_admin")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(welcome_message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def _handle_deposit_currency_callback(self, query, currency: str):
        """Handle deposit currency selection"""
        user_id = query.from_user.id
        
        # Get admin wallet for this currency
        admin_wallets = self.crypto.get_admin_wallets(currency)
        
        if not admin_wallets:
            await query.edit_message_text(
                f"❌ No {currency} wallet available. Please contact admin."
            )
            return
        
        admin_wallet = admin_wallets[0]  # Get first available wallet
        
        # Get currency info
        currencies = self.crypto.get_supported_currencies()
        currency_info = next((c for c in currencies if c['currency'] == currency), None)
        
        if not currency_info:
            await query.edit_message_text("❌ Currency not supported.")
            return
        
        min_deposit = currency_info['min_deposit']
        
        deposit_message = f"""💰 {currency} Deposit Instructions

🏦 Admin Wallet Address:
{admin_wallet.address}

🌐 Network: {admin_wallet.network}
💵 Minimum Deposit: {min_deposit} {currency}

📋 Steps:
1. Send {currency} to the address above
2. Take a screenshot of the transaction
3. Click "I Have Paid" button below
4. Upload your transaction proof
5. Click "Complete" to submit

⚠️ Important:
• Only send {currency} to this address
• Minimum deposit: {min_deposit} {currency}
• Double-check the address before sending
• Keep your transaction proof safe

Need help? Contact support!"""
        
        keyboard = [
            [InlineKeyboardButton("✅ I Have Paid", callback_data=f"deposit_paid_{currency}")],
            [InlineKeyboardButton("🔙 Back to Deposit", callback_data="cmd_deposit")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(deposit_message, reply_markup=reply_markup)
    
    async def _handle_deposit_paid_callback(self, query, currency: str):
        """Handle deposit paid button - ask for proof"""
        user_id = query.from_user.id
        
        # Store the deposit state for this user
        if not hasattr(self, 'deposit_states'):
            self.deposit_states = {}
        
        self.deposit_states[user_id] = {
            'currency': currency,
            'step': 'waiting_for_proof'
        }
        
        proof_message = f"""📸 *Upload Your Payment Proof*

Please upload a screenshot or image of your {currency} transaction.

*What to include:*
• Transaction hash/ID
• Amount sent
• Wallet address (yours and admin's)
• Transaction status (confirmed)

*After uploading your proof:*
1. Type the amount you sent
2. Click "Complete Deposit" button

*Example:*
Send: `100` (if you sent 100 {currency})"""
        
        keyboard = [
            [InlineKeyboardButton("🔙 Back to Instructions", callback_data=f"deposit_currency_{currency}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(proof_message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def _handle_deposit_complete_callback(self, query, currency: str, amount: str):
        """Handle deposit complete button"""
        user_id = query.from_user.id
        
        try:
            deposit_amount = float(amount)
        except ValueError:
            await query.edit_message_text("❌ Invalid amount. Please try again.")
            return
        
        # Get admin wallet for this currency
        admin_wallets = self.crypto.get_admin_wallets(currency)
        if not admin_wallets:
            await query.edit_message_text(f"❌ No {currency} wallet available.")
            return
        
        admin_wallet = admin_wallets[0]
        
        # Get proof file ID from deposit state
        proof_file_id = None
        if hasattr(self, 'deposit_states') and user_id in self.deposit_states:
            proof_file_id = self.deposit_states[user_id].get('proof_file_id', 'Image uploaded by user')
        
        # Create payment request
        request_id = self.crypto.create_payment_request(
            user_id=user_id,
            request_type='deposit',
            currency=currency,
            amount=deposit_amount,
            wallet_address=admin_wallet.address,
            proof_image=proof_file_id or "Image uploaded by user"
        )
        
        if request_id:
            success_message = f"""✅ Deposit Request Submitted Successfully!

📋 Request ID: #{request_id}
💰 Currency: {currency}
💵 Amount: {deposit_amount}
🏦 Admin Wallet: {admin_wallet.address}

⏳ Status: Waiting for Admin Approval

What happens next:
• Admin will review your transaction
• You'll be notified when approved
• Balance will be added to your account
• Processing time: 1-24 hours

You can check status anytime using:
• /payment_history command
• Payment History button in main menu

Thank you for your deposit! 🎉"""
            
            keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(success_message, reply_markup=reply_markup)
            
            # Notify all admins about the new deposit request
            await self.notify_admins_deposit_request(request_id, user_id, currency, deposit_amount, admin_wallet.address)
            
            # Clear deposit state
            if hasattr(self, 'deposit_states') and user_id in self.deposit_states:
                del self.deposit_states[user_id]
        else:
            await query.edit_message_text("❌ Failed to submit deposit request. Please try again.")
    
    async def notify_admins_deposit_request(self, request_id: int, user_id: int, currency: str, amount: float, wallet_address: str):
        """Notify all admins about a new deposit request"""
        try:
            # Get all admin users
            admins = self.db.get_all_admins()
            print(f"🔔 DEBUG: Found {len(admins)} admins to notify for request #{request_id}")
            
            # Get user info
            user_data = self.db.get_user(user_id)
            username = user_data.get('username', 'Unknown') if user_data else 'Unknown'
            first_name = user_data.get('first_name', 'Unknown') if user_data else 'Unknown'
            
            notification_message = f"""🔔 NEW DEPOSIT REQUEST

📋 Request ID: #{request_id}
👤 User: {first_name} (@{username})
🆔 User ID: {user_id}
💰 Currency: {currency}
💵 Amount: {amount}
🏦 Wallet: {wallet_address}

⏳ Status: Pending Approval

Please verify the transaction and approve/reject using:
/approve_payment {request_id}
/reject_payment {request_id} [reason]"""
            
            # Create admin action buttons
            keyboard = [
                [
                    InlineKeyboardButton("✅ Approve", callback_data=f"admin_approve_{request_id}"),
                    InlineKeyboardButton("❌ Reject", callback_data=f"admin_reject_{request_id}")
                ],
                [InlineKeyboardButton("📋 View Details", callback_data=f"admin_view_{request_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Send notification to all admins
            for admin in admins:
                try:
                    print(f"🔔 DEBUG: Sending notification to admin {admin['user_id']} ({admin['first_name']})")
                    # Use the running application bot
                    if self.application and self.application.bot:
                        await self.application.bot.send_message(
                            chat_id=admin['user_id'],
                            text=notification_message,
                            reply_markup=reply_markup
                        )
                    else:
                        logger.error("Application bot not initialized; cannot notify admins.")
                    print(f"✅ DEBUG: Notification sent successfully to admin {admin['user_id']}")
                    logger.info(f"Admin notification sent to {admin['user_id']} for deposit request #{request_id}")
                except Exception as e:
                    print(f"❌ DEBUG: Failed to send notification to admin {admin['user_id']}: {e}")
                    logger.error(f"Failed to notify admin {admin['user_id']}: {e}")
            
            print(f"🔔 DEBUG: Completed sending notifications to {len(admins)} admins")
            logger.info(f"Deposit request #{request_id} notification sent to {len(admins)} admins")
                    
        except Exception as e:
            logger.error(f"Error notifying admins of deposit request: {e}")

    async def notify_deposit_approved(self, user_id: int, request_id: int, amount: float, currency: str):
        """Notify user when deposit is approved"""
        try:
            # Get user data
            user_data = self.db.get_user(user_id)
            if not user_data:
                return
        
            # Send notification message
            notification_message = f"""🎉 Deposit Approved!

✅ Request ID: #{request_id}
💰 Currency: {currency}
💵 Amount: {amount}
💳 Added to Balance: ${amount:,.2f}

Your deposit has been successfully approved and added to your account balance!

You can now use this balance for betting. Good luck! 🍀"""
            
            # Send notification message to user
            if self.application and self.application.bot:
                await self.application.bot.send_message(
                    chat_id=user_id,
                    text=notification_message
                )
            else:
                logger.error("Application bot not initialized; cannot notify user.")
            
            logger.info(f"Deposit approved for user {user_id}: {amount} {currency}")
            
        except Exception as e:
            logger.error(f"Error notifying user of deposit approval: {e}")
    
    async def notify_withdrawal_approved(self, user_id: int, request_id: int, amount: float, currency: str):
        """Notify user when withdrawal is approved"""
        try:
            approval_message = f"""✅ Withdrawal Request Approved

📋 Request ID: #{request_id}
💰 Amount: {amount} {currency}
📅 Approved: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Your withdrawal has been approved and will be processed shortly.
The amount has been deducted from your balance.

Thank you for using our service!"""
            
            # Use the running application bot
            if self.application and self.application.bot:
                await self.application.bot.send_message(chat_id=user_id, text=approval_message)
            else:
                logger.error("Application bot not initialized; cannot notify user.")
            
        except Exception as e:
            logger.error(f"Error notifying user of withdrawal approval: {e}")
    
    async def _handle_admin_approve_callback(self, query, request_id: int):
        """Handle admin approve button"""
        user_id = query.from_user.id
        
        if not self.db.is_admin(user_id):
            await query.edit_message_text("❌ Access denied. Admin privileges required.")
            return
        
        try:
            # Get payment request details
            request = self.crypto.get_payment_request(request_id)
            if not request:
                await query.edit_message_text("❌ Payment request not found.")
                return
        
            if request.status != 'pending':
                await query.edit_message_text("❌ This request has already been processed.")
                return
            
            # Approve the payment
            success = self.crypto.approve_payment_request(request_id, "Approved via admin panel")
            
            if success:
                # Balance is already updated by approve_payment_request method
                # No need to update again here
                
                # Notify user based on request type
                if request.type == 'deposit':
                    await self.notify_deposit_approved(request.user_id, request_id, request.amount, request.currency)
                elif request.type == 'withdraw':
                    await self.notify_withdrawal_approved(request.user_id, request_id, request.amount, request.currency)
                
                # Update admin message
                action = "credited" if request.type == 'deposit' else "debited"
                await query.edit_message_text(
                    f"✅ Payment request #{request_id} approved successfully!\n\n"
                    f"User {request.user_id} has been {action} {request.amount} {request.currency}",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="cmd_admin")
                    ]])
                )
            else:
                await query.edit_message_text("❌ Failed to approve payment request.")
                
        except Exception as e:
            logger.error(f"Error approving payment request: {e}")
            await query.edit_message_text("❌ An error occurred while approving the request.")
    
    async def _handle_admin_reject_callback(self, query, request_id: int):
        """Handle admin reject button"""
        user_id = query.from_user.id
        
        if not self.db.is_admin(user_id):
            await query.edit_message_text("❌ Access denied. Admin privileges required.")
            return
        
        try:
            # Get payment request details
            request = self.crypto.get_payment_request(request_id)
            if not request:
                await query.edit_message_text("❌ Payment request not found.")
                return
        
            if request.status != 'pending':
                await query.edit_message_text("❌ This request has already been processed.")
                return
            
            # Reject the payment
            success = self.crypto.reject_payment_request(request_id, "Rejected via admin panel")
            
            if success:
                # Notify user
                await self.notify_deposit_rejected(request.user_id, request_id, request.amount, request.currency)
                
                # Update admin message
                await query.edit_message_text(
                    f"❌ Payment request #{request_id} rejected.\n\n"
                    f"User {request.user_id} has been notified.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="cmd_admin")
                    ]])
                )
            else:
                await query.edit_message_text("❌ Failed to reject payment request.")
                
        except Exception as e:
            logger.error(f"Error rejecting payment request: {e}")
            await query.edit_message_text("❌ An error occurred while rejecting the request.")
    
    async def _handle_admin_view_callback(self, query, request_id: int):
        """Handle admin view details button"""
        user_id = query.from_user.id
        
        if not self.db.is_admin(user_id):
            await query.edit_message_text("❌ Access denied. Admin privileges required.")
            return
        
        try:
            # Get payment request details
            request = self.crypto.get_payment_request(request_id)
            if not request:
                await query.edit_message_text("❌ Payment request not found.")
                return
            
            # Get user info
            user_data = self.db.get_user(request.user_id)
            username = user_data.get('username', 'Unknown') if user_data else 'Unknown'
            first_name = user_data.get('first_name', 'Unknown') if user_data else 'Unknown'
            
            details_message = f"""📋 Payment Request Details

🆔 Request ID: #{request_id}
👤 User: {first_name} (@{username})
🆔 User ID: {request.user_id}
💰 Currency: {request.currency}
💵 Amount: {request.amount}
🏦 Wallet: {request.wallet_address}
📸 Proof: {request.proof_image}
📅 Created: {request.created_at}
⏳ Status: {request.status}

Admin Actions:"""
            
            keyboard = [
                [
                    InlineKeyboardButton("✅ Approve", callback_data=f"admin_approve_{request_id}"),
                    InlineKeyboardButton("❌ Reject", callback_data=f"admin_reject_{request_id}")
                ],
                [InlineKeyboardButton("🔙 Back", callback_data="cmd_admin")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(details_message, reply_markup=reply_markup)
                
        except Exception as e:
            logger.error(f"Error viewing payment request: {e}")
            await query.edit_message_text("❌ An error occurred while viewing the request.")
    
    async def _handle_add_wallet_callback(self, query):
        """Handle add wallet button callback"""
        # Get supported currencies
        currencies = self.crypto.get_supported_currencies()
        
        keyboard = []
        for currency_info in currencies:
            currency = currency_info['currency']
            name = currency_info['name']
            keyboard.append([InlineKeyboardButton(
                f"{currency} ({name})", 
                callback_data=f"add_wallet_currency_{currency}"
            )])
        
        keyboard.append([InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "➕ Add New Wallet\n\n"
            "Select a cryptocurrency to add wallet address:",
            reply_markup=reply_markup
        )
    
    async def _handle_withdraw_currency_callback(self, query, currency: str):
        """Handle withdraw currency selection"""
        user_id = query.from_user.id
        
        # Get user wallet for this currency
        wallets = self.crypto.get_user_wallets(user_id)
        user_wallet = next((w for w in wallets if w['currency'] == currency), None)
        
        if not user_wallet:
            await query.edit_message_text(f"❌ No {currency} wallet found.")
            return
        
        # Get user balance
        user_data = self.db.get_user(user_id)
        current_balance = user_data['balance'] if user_data else 0.0
        
        await query.edit_message_text(
            f"💵 Withdraw {currency}\n\n"
            f"💰 Available Balance: ${current_balance:,.2f}\n"
            f"🏦 Wallet Address: `{user_wallet['address']}`\n\n"
            f"To request withdrawal, send a message like:\n"
            f"`Withdraw {currency} 100`\n\n"
            f"Admin will process your request within 24 hours.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Withdraw", callback_data="cmd_withdraw")
            ]]),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _handle_add_wallet_currency_callback(self, query, currency: str):
        """Handle add wallet currency selection"""
        user_id = query.from_user.id
        
        await query.edit_message_text(
            f"➕ Add {currency} Wallet\n\n"
            f"To add your {currency} wallet address, send a message like:\n\n"
            f"`Add wallet {currency} YOUR_WALLET_ADDRESS`\n\n"
            f"Example:\n"
            f"`Add wallet {currency} TQn9Y2khEsLJW1ChVWFMSMeRDow5KcbLSE`\n\n"
            f"After adding your wallet, you can use it for withdrawals.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Add Wallet", callback_data="cmd_add_wallet")
            ]]),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _handle_payment_requests_callback(self, query):
        """Handle payment requests button callback"""
        user_id = query.from_user.id
        
        if not self.db.is_admin(user_id):
            await query.edit_message_text("❌ Access denied. Admin privileges required.")
            return
        
        # Get pending requests
        requests = self.crypto.get_pending_requests()
        
        if not requests:
            await query.edit_message_text(
                "📝 No pending payment requests.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="cmd_admin")
                ]])
            )
            return
        
        requests_text = "📋 Pending Payment Requests:\n\n"
        
        # Show only the first request with action buttons
        if requests:
            request = requests[0]  # Show first request
            requests_text += f"🆔 ID: {request.request_id}\n"
            requests_text += f"👤 User: {request.user_id}\n"
            requests_text += f"💰 Type: {request.type.upper()}\n"
            requests_text += f"💵 Amount: {request.amount} {request.currency}\n"
            requests_text += f"🏦 Wallet: {request.wallet_address}\n"
            if request.proof_image:
                requests_text += f"🔗 Proof: {request.proof_image}\n"
            requests_text += f"📅 Date: {request.created_at}\n\n"
            
            if len(requests) > 1:
                requests_text += f"... and {len(requests) - 1} more requests\n\n"
        
        keyboard = [
            [
                InlineKeyboardButton("✅ Approve", callback_data=f"admin_approve_{requests[0].request_id}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"admin_reject_{requests[0].request_id}")
            ],
            [InlineKeyboardButton("📋 View Details", callback_data=f"admin_view_{requests[0].request_id}")],
            [InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="cmd_admin")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(requests_text, reply_markup=reply_markup)
    
    async def _handle_users_callback(self, query):
        """Handle users button callback"""
        user_id = query.from_user.id
        
        if not self.db.is_admin(user_id):
            await query.edit_message_text("❌ Access denied. Admin privileges required.")
            return
        
        # Get all users
        users = self.db.get_all_users()
        
        if not users:
            await query.edit_message_text(
                "📊 No users found.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="cmd_admin")
                ]])
            )
            return
        
        users_message = "👥 All Users:\n\n"
        
        for user in users[:10]:  # Show first 10 users
            admin_badge = "👑" if user['is_admin'] else ""
            users_message += f"{admin_badge} {user['first_name']} (@{user['username'] or 'N/A'})\n"
            users_message += f"   ID: {user['user_id']}\n"
            users_message += f"   Balance: ${user['balance']:,.2f}\n"
            users_message += f"   Bets: {user['total_bets']}\n"
            users_message += f"   Joined: {user['created_at']}\n\n"
        
        keyboard = [
            [InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="cmd_admin")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
    
        await query.edit_message_text(users_message, reply_markup=reply_markup)
        
    async def _handle_bot_stats_callback(self, query):
        """Handle bot stats button callback"""
        user_id = query.from_user.id
        
        if not self.db.is_admin(user_id):
            await query.edit_message_text("❌ Access denied. Admin privileges required.")
            return
        
        # Get bot statistics
        users = self.db.get_all_users()
        total_users = len(users)
        total_balance = sum(user['balance'] for user in users)
        total_bets = sum(user['total_bets'] for user in users)
        total_wagered = sum(user['total_wagered'] for user in users)
        admin_count = sum(1 for user in users if user['is_admin'])
        
        stats_message = f"""📊 Bot Statistics

👥 Users:
• Total Users: {total_users}
• Admins: {admin_count}
• Regular Users: {total_users - admin_count}

💰 Financial:
• Total Balance: ${total_balance:,.2f}
• Total Wagered: ${total_wagered:,.2f}
• Average Balance: ${total_balance/total_users:,.2f}

🎯 Betting:
• Total Bets: {total_bets}
• Average Bets per User: {total_bets/total_users:.1f}

Note: Statistics are real-time."""
        
        keyboard = [
            [InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="cmd_admin")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(stats_message, reply_markup=reply_markup)
    
    async def _handle_admin_wallets_callback(self, query):
        """Handle admin wallets button callback"""
        user_id = query.from_user.id
        
        if not self.db.is_admin(user_id):
            await query.edit_message_text("❌ Access denied. Admin privileges required.")
            return
        
        # Get existing admin wallets
        wallets = self.crypto.get_admin_wallets()
        
        wallets_message = "🏦 Admin Wallet Management\n\n"
        
        if wallets:
            wallets_message += "Current Admin Wallets:\n\n"
            for wallet in wallets:
                wallets_message += f"💰 {wallet.currency}\n"
                wallets_message += f"🏦 {wallet.address}\n"
                wallets_message += f"🌐 {wallet.network}\n"
                wallets_message += f"✅ Active: {'Yes' if wallet.is_active else 'No'}\n\n"
        else:
            wallets_message += "No admin wallets configured yet.\n\n"
        
        wallets_message += "Use the buttons below to manage wallets:"
        
        keyboard = [
            [InlineKeyboardButton("➕ Add New Wallet", callback_data="cmd_add_admin_wallet")],
            [InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="cmd_admin")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(wallets_message, reply_markup=reply_markup)
    
    async def _handle_add_admin_wallet_callback(self, query):
        """Handle add admin wallet button callback"""
        user_id = query.from_user.id
        
        if not self.db.is_admin(user_id):
            await query.edit_message_text("❌ Access denied. Admin privileges required.")
            return
        
        add_wallet_message = """➕ Add New Admin Wallet

To add a new admin wallet, send a message in this format:

`Add admin wallet CURRENCY ADDRESS NETWORK`

Examples:
• `Add admin wallet USDT TQn9Y2khEsLJW1ChVWFMSMeRDow5KcbLSE TRC20`
• `Add admin wallet BTC 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa BTC`
• `Add admin wallet ETH 0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6 ERC20`

Supported currencies: USDT, BTC, ETH
Supported networks: TRC20, ERC20, BEP20, BTC, ETH

⚠️ Make sure the wallet address is correct!"""
        
        keyboard = [
            [InlineKeyboardButton("🔙 Back to Admin Wallets", callback_data="cmd_admin_wallets")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(add_wallet_message, reply_markup=reply_markup)
    
    async def notify_deposit_rejected(self, user_id: int, request_id: int, amount: float, currency: str):
        """Notify user when deposit is rejected"""
        try:
            rejection_message = f"""❌ Deposit Request Rejected

📋 Request ID: #{request_id}
💰 Amount: {amount} {currency}

Your deposit request has been rejected by admin.

Possible reasons:
• Invalid transaction proof
• Wrong wallet address
• Insufficient amount
• Other verification issues

Please contact support if you believe this is an error.

You can submit a new deposit request anytime."""
            
            await self.application.bot.send_message(
                chat_id=user_id,
                text=rejection_message
            )
            
            logger.info(f"Deposit rejected notification sent to user {user_id}: {amount} {currency}")
            
        except Exception as e:
            logger.error(f"Error notifying user of deposit rejection: {e}")
    
    async def _handle_game_bet_callback(self, query, data: str):
        """Handle game bet callback"""
        try:
            # Parse: bet_game_{game_id}_{team}_{bet_type}
            parts = data.split('_')
            if len(parts) >= 4:
                game_id = parts[2]
                team = parts[3]
                bet_type = parts[4]
                
                await self.ui.show_game_odds(query, None, game_id)
        except Exception as e:
            logger.error(f"Error handling game bet callback: {e}")
            await query.edit_message_text("Error processing bet. Please try again.")
    
    async def _handle_team_bet_callback(self, query, data: str):
        """Handle team bet callback"""
        try:
            # Parse: bet_team_{team}_{bet_type}_{game_id}
            parts = data.split('_')
            if len(parts) >= 4:
                team = parts[2]
                bet_type = parts[3]
                game_id = parts[4] if len(parts) > 4 else None
                
                await self.ui.show_bet_amount_input(query, None, team, bet_type, game_id)
        except Exception as e:
            logger.error(f"Error handling team bet callback: {e}")
            await query.edit_message_text("Error processing bet. Please try again.")
    
    async def _handle_total_bet_callback(self, query, data: str):
        """Handle total bet callback"""
        try:
            # Parse: bet_total_{over_under}_{point}_{game_id}
            parts = data.split('_')
            if len(parts) >= 4:
                over_under = parts[2]
                point = parts[3]
                game_id = parts[4] if len(parts) > 4 else None
                
                team = f"{over_under} {point}"
                await self.ui.show_bet_amount_input(query, None, team, "TOTAL", game_id)
        except Exception as e:
            logger.error(f"Error handling total bet callback: {e}")
            await query.edit_message_text("Error processing bet. Please try again.")
    
    async def _handle_bet_amount_callback(self, query, data: str):
        """Handle bet amount callback"""
        try:
            # Parse: bet_amount_{amount}
            parts = data.split('_')
            if len(parts) >= 3:
                amount_str = parts[2]
                
                if amount_str == "custom":
                    await query.edit_message_text(
                        "Please enter your custom bet amount (e.g., 75, 150, 300):",
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("Back", callback_data="cmd_live_games")
                        ]])
                    )
                else:
                    try:
                        amount = float(amount_str)
                        # Process the bet with the stored pending bet info
                        # This would need to be implemented with context storage
                        await query.edit_message_text(
                            f"Bet amount set to ${amount}. Processing bet...",
                            reply_markup=InlineKeyboardMarkup([[
                                InlineKeyboardButton("Back to Main Menu", callback_data="back_to_main")
                            ]])
                        )
                    except ValueError:
                        await query.edit_message_text("Invalid amount. Please try again.")
        except Exception as e:
            logger.error(f"Error handling bet amount callback: {e}")
            await query.edit_message_text("Error processing amount. Please try again.")
    
    async def _handle_quick_bet_callback(self, query, data: str):
        """Handle quick bet callback"""
        try:
            # Parse: quick_bet_{team}_{bet_type}
            parts = data.split('_')
            if len(parts) >= 3:
                team = parts[2]
                bet_type = parts[3]
                
                await self.ui.show_bet_amount_input(query, None, team, bet_type)
        except Exception as e:
            logger.error(f"Error handling quick bet callback: {e}")
            await query.edit_message_text("Error processing quick bet. Please try again.")
    
    async def handle_deposit_amount_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle deposit amount message from user"""
        user_id = update.effective_user.id
        message_text = update.message.text
        
        # Check if user is in deposit flow
        if not hasattr(self, 'deposit_states') or user_id not in self.deposit_states:
            return
        
        deposit_state = self.deposit_states[user_id]
        if deposit_state['step'] != 'waiting_for_proof':
            return
        
        try:
            amount = float(message_text)
            currency = deposit_state['currency']
            
            # Check if user has uploaded proof
            if 'proof_file_id' not in deposit_state:
                await update.message.reply_text(
                    "❌ Please upload your payment proof first before entering the amount.\n\nUpload a screenshot or image of your transaction."
                )
                return
            
            # Update state to waiting for completion
            self.deposit_states[user_id]['step'] = 'waiting_for_completion'
            self.deposit_states[user_id]['amount'] = amount
            
            # Show complete button
            complete_message = f"""✅ Amount Received: {amount} {currency}

Now click "Complete Deposit" to submit your request.

Your deposit details:
• Currency: {currency}
• Amount: {amount}
• Proof: Uploaded ✅
• Status: Ready to submit

Click the button below to complete your deposit request."""
            
            keyboard = [
                [InlineKeyboardButton("✅ Complete Deposit", callback_data=f"deposit_complete_{currency}_{amount}")],
                [InlineKeyboardButton("🔙 Back to Instructions", callback_data=f"deposit_currency_{currency}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(complete_message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
            
        except ValueError:
            await update.message.reply_text("❌ Invalid amount. Please enter a number (e.g., 100).")
    
    
    def _format_recent_performance(self, recent_results: list) -> str:
        """Format recent performance for display"""
        if not recent_results:
            return "No recent bets"
        
        performance_emojis = []
        for result in recent_results[:10]:  # Last 10 bets
            if result == 'won':
                performance_emojis.append('✅')
            elif result == 'lost':
                performance_emojis.append('❌')
            else:
                performance_emojis.append('⏳')
        
        return ' '.join(performance_emojis)
    
    
    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle photo uploads during deposit flow"""
        user_id = update.effective_user.id
        
        # Check if user is in deposit flow
        if hasattr(self, 'deposit_states') and user_id in self.deposit_states:
            # Store the photo file ID for the deposit
            photo = update.message.photo[-1]  # Get highest resolution
            self.deposit_states[user_id]['proof_file_id'] = photo.file_id
            
            await update.message.reply_text(
                "✅ Payment proof received!\n\nNow please type the amount you sent (e.g., 100 for 100 USDT):"
            )
        else:
            await update.message.reply_text("❌ Please start a deposit process first by clicking '💸 Deposit' button.")

    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle document uploads during deposit flow"""
        user_id = update.effective_user.id
        
        # Check if user is in deposit flow
        if hasattr(self, 'deposit_states') and user_id in self.deposit_states:
            # Store the document file ID for the deposit
            document = update.message.document
            self.deposit_states[user_id]['proof_file_id'] = document.file_id
            
            await update.message.reply_text(
                "✅ Payment proof received!\n\nNow please type the amount you sent (e.g., 100 for 100 USDT):"
            )
        else:
            await update.message.reply_text("❌ Please start a deposit process first by clicking '💸 Deposit' button.")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular messages (betting attempts, deposit amounts)"""
        user_id = update.effective_user.id
        message_text = update.message.text
        
        # Check rate limit
        if not self.check_rate_limit(user_id):
            await update.message.reply_text("⏰ Rate limit exceeded. Please wait a moment before trying again.")
            return
        
        # Check if user is in deposit flow
        if hasattr(self, 'deposit_states') and user_id in self.deposit_states:
            await self.handle_deposit_amount_message(update, context)
            return
        
        # If message is a command (like /start), show interface
        if message_text.startswith('/'):
            await self.start_command(update, context)
            return
        
        # Parse the bet
        bet_data = self.bet_parser.parse_bet(message_text)
        
        if not bet_data:
            # Check if it's a wallet-related message
            if message_text.lower().startswith("add wallet"):
                await self.handle_add_wallet_message(update, context)
                return
            elif message_text.lower().startswith("withdraw"):
                await self.handle_withdraw_message(update, context)
                return
            elif message_text.lower().startswith("add admin wallet"):
                await self.handle_add_admin_wallet_message(update, context)
                return
            
            await update.message.reply_text(
                "❌ *Invalid bet format!*\n\nUse: Team ML $500\n\nType /start to see the interface.",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Validate the bet
        is_valid, error_message = self.bet_parser.validate_bet(bet_data)
        if not is_valid:
            await update.message.reply_text(f"❌ {error_message}")
            return
        
        # Check user balance
        user_data = self.db.get_user(user_id)
        if not user_data:
            await update.message.reply_text("❌ User not found. Please use /start first.")
            return
        
        current_balance = user_data['balance']
        if current_balance < bet_data['amount']:
            await update.message.reply_text(f"❌ Insufficient balance! You have ${current_balance:,.2f} but need ${bet_data['amount']:,.2f}")
            return
        
        # Deduct bet amount from balance
        if not self.db.deduct_bet_amount(user_id, bet_data['amount']):
            await update.message.reply_text("❌ Failed to deduct bet amount from balance.")
            return
        
        # Calculate odds for this bet
        odds_data = await self.betting_engine.calculate_odds(
            bet_data['team'], 
            bet_data['bet_type']
        )
        
        # Create the bet in database with odds
        bet_id = self.db.create_bet(
            user_id=user_id,
            team=bet_data['team'],
            bet_type=bet_data['bet_type'],
            amount=bet_data['amount'],
            odds=odds_data.odds
        )
        
        # Get user's preferred voice
        user = self.db.get_user(user_id)
        preferred_voice = user['preferred_voice'] if user else 'Taylor Swift'
        
        # Simulate bet result (for demo purposes, we'll settle immediately)
        bet_info = {
            'bet_id': bet_id,
            'user_id': user_id,
            'team': bet_data['team'],
            'bet_type': bet_data['bet_type'],
            'amount': bet_data['amount'],
            'created_at': datetime.now()
        }
        
        bet_result = await self.betting_engine.simulate_bet_result(bet_info)
        
        # Update bet result in database
        self.db.update_bet_result(
            bet_id=bet_id,
            result=bet_result.result,
            payout=bet_result.payout,
            profit=bet_result.profit
        )
        
        # Add winnings to balance if bet won
        if bet_result.result == 'won':
            self.db.add_winnings(user_id, bet_result.payout)
        
        # Format confirmation message
        confirmation_text = """🎰 *Bet Placed Successfully!*

📋 *Bet ID:* #""" + str(bet_id) + """
🏆 *Team:* """ + bet_data['team'] + """
🎯 *Type:* """ + bet_data['bet_type'] + """
💰 *Amount:* $""" + f"{bet_data['amount']:,.2f}" + """
📊 *Odds:* """ + f"{odds_data.odds:.2f}" + """
🎤 *Voice:* """ + preferred_voice + """

Good luck! 🍀"""
        
        # Send confirmation message
        await update.message.reply_text(confirmation_text, parse_mode=ParseMode.MARKDOWN)
        
        # Send automatic result message
        await update.message.reply_text("🎲 *Calculating result automatically...*\n\n⚡ *Fair and unbiased system*\n🔄 *Processing...*", parse_mode=ParseMode.MARKDOWN)
        
        # Generate and send voice message
        try:
            voice_text = self.voice_generator.format_bet_message(
                bet_data['team'], 
                bet_data['bet_type'], 
                bet_data['amount']
            )
            
            voice_audio = await self.voice_generator.generate_voice(voice_text, preferred_voice)
            if voice_audio:
                await update.message.reply_voice(
                    voice=voice_audio,
                    caption=f"🎤 {preferred_voice} says:"
                )
            else:
                # Fallback message when voice generation fails
                fallback_message = """🎤 *Voice Message from """ + preferred_voice + """:*

""" + f'"{voice_text}"' + """

*Note:* Voice generation temporarily unavailable."""
                await update.message.reply_text(fallback_message, parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            logger.error(f"Error generating voice: {e}")
            await update.message.reply_text("🎤 Voice generation failed, but your bet was placed!")
        
        # Log the bet
        logger.info(f"Bet placed: User {user_id}, Team {bet_data['team']}, Type {bet_data['bet_type']}, Amount ${bet_data['amount']}, Odds {odds_data.odds:.2f}")
        
        # Send bet result after a short delay
        await asyncio.sleep(2)
        
        if bet_result.result == 'won':
            result_message = """🎉 *Congratulations! You Won!*

🏆 *""" + bet_data['team'] + " " + bet_data['bet_type'] + """*
💰 *Bet Amount:* $""" + f"{bet_data['amount']:,.2f}" + """
📊 *Odds:* """ + f"{odds_data.odds:.2f}" + """
💵 *Payout:* $""" + f"{bet_result.payout:,.2f}" + """
📈 *Profit:* $""" + f"{bet_result.profit:,.2f}" + """

🎲 *Result: Fair and automatically decided*
Great job! 🎯"""
            
            # Generate win voice message
            try:
                win_voice_text = self.voice_generator.format_win_message(
                    bet_data['team'],
                    bet_data['bet_type'],
                    bet_data['amount'],
                    bet_result.payout
                )
                
                win_voice_audio = await self.voice_generator.generate_voice(win_voice_text, preferred_voice)
                if win_voice_audio:
                    await update.message.reply_voice(
                        voice=win_voice_audio,
                        caption=f"🎤 {preferred_voice} celebrates:"
                    )
            except Exception as e:
                logger.error(f"Error generating win voice: {e}")
        else:
            result_message = """😔 *Better Luck Next Time!*

🏆 *""" + bet_data['team'] + " " + bet_data['bet_type'] + """*
💰 *Bet Amount:* $""" + f"{bet_data['amount']:,.2f}" + """
📊 *Odds:* """ + f"{odds_data.odds:.2f}" + """
💸 *Loss:* $""" + f"{bet_data['amount']:,.2f}" + """

🎲 *Result: Fair and automatically decided*
Don't give up! 🍀"""
            
            # Generate loss voice message
            try:
                loss_voice_text = self.voice_generator.format_loss_message(
                    bet_data['team'],
                    bet_data['bet_type'],
                    bet_data['amount']
                )
                
                loss_voice_audio = await self.voice_generator.generate_voice(loss_voice_text, preferred_voice)
                if loss_voice_audio:
                    await update.message.reply_voice(
                        voice=loss_voice_audio,
                        caption=f"🎤 {preferred_voice} says:"
                    )
            except Exception as e:
                logger.error(f"Error generating loss voice: {e}")
        
        await update.message.reply_text(result_message, parse_mode=ParseMode.MARKDOWN)
    
    async def handle_add_wallet_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle add wallet message"""
        user_id = update.effective_user.id
        message_text = update.message.text
        
        # Parse "Add wallet CURRENCY ADDRESS"
        parts = message_text.split()
        if len(parts) < 4:
            await update.message.reply_text(
                "❌ Invalid format!\n\n"
                "Use: Add wallet CURRENCY ADDRESS\n\n"
                "Example: Add wallet USDT TQn9Y2khEsLJW1ChVWFMSMeRDow5KcbLSE"
            )
            return
        
        currency = parts[2].upper()
        address = parts[3]
        
        # Validate currency
        currencies = self.crypto.get_supported_currencies()
        currency_info = next((c for c in currencies if c['currency'] == currency), None)
        
        if not currency_info:
            await update.message.reply_text(f"❌ {currency} is not supported.")
            return
        
        # Add wallet address
        if self.crypto.add_user_wallet(user_id, currency, address):
            await update.message.reply_text(
                f"✅ Wallet Address Added!\n\n"
                f"💰 Currency: {currency}\n"
                f"🏦 Address: `{address}`\n\n"
                f"Your wallet address has been saved for withdrawals.",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text("❌ Failed to add wallet address. Please try again.")
    
    async def handle_withdraw_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle withdraw message"""
        user_id = update.effective_user.id
        message_text = update.message.text
        
        # Parse "Withdraw CURRENCY AMOUNT"
        parts = message_text.split()
        if len(parts) < 3:
            await update.message.reply_text(
                "❌ Invalid format!\n\n"
                "Use: Withdraw CURRENCY AMOUNT\n\n"
                "Example: Withdraw USDT 100"
            )
            return
        
        try:
            currency = parts[1].upper()
            amount = float(parts[2])
        except ValueError:
            await update.message.reply_text("❌ Invalid amount. Please enter a number.")
            return
        
        # Check user balance
        user_data = self.db.get_user(user_id)
        if not user_data:
            await update.message.reply_text("❌ User not found. Please use /start first.")
            return
        
        current_balance = user_data['balance']
        if current_balance < amount:
            await update.message.reply_text(
                f"❌ Insufficient Balance!\n\n"
                f"💵 Current Balance: ${current_balance:,.2f}\n"
                f"💰 Withdrawal Amount: ${amount:,.2f}\n"
                f"📉 Shortfall: ${amount - current_balance:,.2f}",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Get user wallet for this currency
        user_wallets = self.crypto.get_user_wallets(user_id)
        user_wallet = next((w for w in user_wallets if w['currency'] == currency), None)
        
        if not user_wallet:
            await update.message.reply_text(
                f"❌ No {currency} wallet address found.\n"
                f"Use the 'Add Wallet' button to add your {currency} address first."
            )
            return
        
        # Create withdrawal request
        request_id = self.crypto.create_payment_request(
            user_id=user_id,
            request_type='withdraw',
            currency=currency,
            amount=amount,
            wallet_address=user_wallet['address']
        )
        
        if request_id:
            await update.message.reply_text(
                f"✅ Withdrawal Request Submitted!\n\n"
                f"📋 Request ID: #{request_id}\n"
                f"💰 Currency: {currency}\n"
                f"💵 Amount: {amount}\n"
                f"🏦 Wallet: `{user_wallet['address']}`\n\n"
                f"⏳ Status: Pending Admin Approval\n\n"
                f"Your withdrawal will be processed within 24 hours.\n"
                f"Use the Payment History button to check status.",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text("❌ Failed to submit withdrawal request. Please try again.")
    
    async def handle_add_admin_wallet_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle add admin wallet message"""
        user_id = update.effective_user.id
        
        # Check if user is admin
        if not self.db.is_admin(user_id):
            await update.message.reply_text("❌ Access denied. Admin privileges required.")
            return
        
        message_text = update.message.text
        
        # Parse "Add admin wallet CURRENCY ADDRESS NETWORK"
        parts = message_text.split()
        if len(parts) < 5:
            await update.message.reply_text(
                "❌ Invalid format!\n\n"
                "Use: Add admin wallet CURRENCY ADDRESS NETWORK\n\n"
                "Example: Add admin wallet USDT TQn9Y2khEsLJW1ChVWFMSMeRDow5KcbLSE TRC20"
            )
            return
        
        try:
            currency = parts[3].upper()
            address = parts[4]
            network = parts[5] if len(parts) > 5 else currency
            
            # Validate currency
            if currency not in ['USDT', 'BTC', 'ETH']:
                await update.message.reply_text(
                    "❌ Unsupported currency!\n\n"
                    "Supported currencies: USDT, BTC, ETH"
                )
                return
            
            # Add admin wallet
            success = self.crypto.add_admin_wallet(currency, address, network)
            
            if success:
                await update.message.reply_text(
                    f"✅ Admin wallet added successfully!\n\n"
                    f"💰 Currency: {currency}\n"
                    f"🏦 Address: `{address}`\n"
                    f"🌐 Network: {network}\n\n"
                    f"This wallet is now available for {currency} deposits.",
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                await update.message.reply_text("❌ Failed to add admin wallet. Please check the address and try again.")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Error adding admin wallet: {str(e)}")
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        logger.error(f"Update {update} caused error {context.error}")
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ An error occurred. Please try again or contact support."
            )

def main():
    """Main function to run the bot"""
    if not TELEGRAM_BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN not found in environment variables!")
        return
    
    # Create bot instance
    betting_bot = BettingBot()
    
    # Create application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Bind application to bot instance for later notifications
    betting_bot.application = application

    # Add handlers - BUTTON INTERFACE (Only /start command)
    application.add_handler(CommandHandler("start", betting_bot.start_command))
    application.add_handler(CallbackQueryHandler(betting_bot.voice_callback, pattern="^voice_"))
    application.add_handler(CallbackQueryHandler(betting_bot.button_callback, pattern="^cmd_|^back_to_main|^deposit_|^admin_|^withdraw_|^add_wallet_|^bet_|^quick_bet_"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, betting_bot.handle_message))
    application.add_handler(MessageHandler(filters.PHOTO, betting_bot.handle_photo))
    application.add_handler(MessageHandler(filters.Document.ALL, betting_bot.handle_document))
    
    # Add error handler
    application.add_error_handler(betting_bot.error_handler)
    
    # Start the bot
    print("🚀 Starting Sports Betting Bot...")
    print("📱 BUTTON INTERFACE - Only /start Command Available")
    print("Press Ctrl+C to stop the bot")
    
    try:
        application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Error running bot: {e}")

if __name__ == '__main__':
    main()

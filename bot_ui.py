import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from sports_api import SportsAPIService
from betting_engine import BettingEngine
import logging

logger = logging.getLogger(__name__)

class BotUI:
    """Enhanced UI components for the betting bot"""
    
    def __init__(self, sports_api: SportsAPIService, betting_engine: BettingEngine):
        self.sports_api = sports_api
        self.betting_engine = betting_engine
    
    async def show_live_games(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show live games with betting options"""
        try:
            # Get live soccer games
            games = await self.sports_api.get_games("soccer", regions="us", markets="h2h,spreads,totals")
            
            if not games:
                await update.callback_query.edit_message_text(
                    "No live games available right now. Check back later!",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("Back to Main Menu", callback_data="back_to_main")
                    ]])
                )
                return
            
            # Show first 5 games with real odds
            games_to_show = games[:5]
            message = "⚽ *Live Soccer Games with Real Odds*\n\n"
            
            keyboard = []
            for i, game in enumerate(games_to_show):
                # Format game time
                game_time = game.commence_time.strftime("%H:%M")
                message += f"*{i+1}.* {game.home_team} vs {game.away_team}\n"
                message += f"   🕐 {game_time} UTC\n"
                
                # Show real odds if available
                if game.bookmakers:
                    bookmaker = game.bookmakers[0]
                    markets = self._parse_markets([bookmaker])
                    
                    # Show Money Line odds
                    if "ML" in markets:
                        ml_markets = markets["ML"]
                        for team, data in list(ml_markets.items())[:2]:  # Show first 2 teams
                            message += f"   💰 {team}: {data['odds']:.2f}\n"
                
                message += "\n"
                
                # Add bet buttons for this game
                keyboard.append([
                    InlineKeyboardButton(f"🏆 {game.home_team}", callback_data=f"bet_team_{game.home_team}_ML_{game.id}"),
                    InlineKeyboardButton(f"🏆 {game.away_team}", callback_data=f"bet_team_{game.away_team}_ML_{game.id}")
                ])
                keyboard.append([
                    InlineKeyboardButton(f"📊 View All Odds", callback_data=f"view_odds_{game.id}"),
                    InlineKeyboardButton(f"📈 Over/Under", callback_data=f"bet_total_OVER_2.5_{game.id}")
                ])
                keyboard.append([InlineKeyboardButton("─" * 20, callback_data="noop")])
            
            keyboard.append([InlineKeyboardButton("Back to Main Menu", callback_data="back_to_main")])
            
            await update.callback_query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"Error showing live games: {e}")
            await update.callback_query.edit_message_text(
                "Error loading live games. Please try again.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Back to Main Menu", callback_data="back_to_main")
                ]])
            )
    
    def _parse_markets(self, bookmakers: List[Dict]) -> Dict[str, Any]:
        """Parse betting markets from bookmaker data"""
        markets = {}
        
        for bookmaker in bookmakers:
            for market in bookmaker.get("markets", []):
                market_key = market.get("key")
                if market_key == "h2h":  # Money Line
                    markets["ML"] = self._parse_moneyline(market)
                elif market_key == "spreads":  # Point Spread
                    markets["SPREAD"] = self._parse_spreads(market)
                elif market_key == "totals":  # Over/Under
                    markets["TOTAL"] = self._parse_totals(market)
        
        return markets
    
    def _parse_moneyline(self, market: Dict) -> Dict[str, Any]:
        """Parse moneyline odds"""
        outcomes = market.get("outcomes", [])
        result = {}
        
        for outcome in outcomes:
            team = outcome.get("name")
            price = outcome.get("price")
            if team and price:
                result[team] = {
                    "odds": self._american_to_decimal(price),
                    "price": price
                }
        
        return result
    
    def _parse_spreads(self, market: Dict) -> Dict[str, Any]:
        """Parse spread odds"""
        outcomes = market.get("outcomes", [])
        result = {}
        
        for outcome in outcomes:
            team = outcome.get("name")
            price = outcome.get("price")
            point = outcome.get("point")
            if team and price and point:
                result[team] = {
                    "odds": self._american_to_decimal(price),
                    "price": price,
                    "point": point
                }
        
        return result
    
    def _parse_totals(self, market: Dict) -> Dict[str, Any]:
        """Parse over/under odds"""
        outcomes = market.get("outcomes", [])
        result = {}
        
        for outcome in outcomes:
            name = outcome.get("name")
            price = outcome.get("price")
            point = outcome.get("point")
            if name and price and point:
                result[name] = {
                    "odds": self._american_to_decimal(price),
                    "price": price,
                    "point": point
                }
        
        return result
    
    def _american_to_decimal(self, american_odds: int) -> float:
        """Convert American odds to decimal odds"""
        if american_odds > 0:
            return (american_odds / 100) + 1
        else:
            return (100 / abs(american_odds)) + 1
    
    async def show_game_odds(self, update: Update, context: ContextTypes.DEFAULT_TYPE, game_id: str):
        """Show detailed odds for a specific game"""
        try:
            # Get game odds
            odds = await self.sports_api.get_game_odds("soccer", game_id)
            
            if not odds:
                await update.callback_query.edit_message_text(
                    "No odds available for this game.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("Back to Games", callback_data="cmd_live_games")
                    ]])
                )
                return
            
            message = f"📊 *{odds.home_team} vs {odds.away_team}*\n"
            message += f"🕐 {odds.commence_time.strftime('%Y-%m-%d %H:%M')} UTC\n\n"
            
            keyboard = []
            
            # Money Line odds
            if "ML" in odds.markets:
                message += "*💰 Money Line:*\n"
                ml_markets = odds.markets["ML"]
                for team, data in ml_markets.items():
                    message += f"• {team}: {data['odds']:.2f} ({data['price']})\n"
                    keyboard.append([
                        InlineKeyboardButton(f"{team} ML", callback_data=f"bet_team_{team}_ML_{game_id}")
                    ])
                message += "\n"
            
            # Spread odds
            if "SPREAD" in odds.markets:
                message += "*📊 Point Spread:*\n"
                spread_markets = odds.markets["SPREAD"]
                for team, data in spread_markets.items():
                    point = data.get('point', 0)
                    message += f"• {team} {point:+.1f}: {data['odds']:.2f} ({data['price']})\n"
                    keyboard.append([
                        InlineKeyboardButton(f"{team} {point:+.1f}", callback_data=f"bet_team_{team}_SPREAD_{game_id}")
                    ])
                message += "\n"
            
            # Total odds
            if "TOTAL" in odds.markets:
                message += "*📈 Over/Under:*\n"
                total_markets = odds.markets["TOTAL"]
                for name, data in total_markets.items():
                    point = data.get('point', 0)
                    message += f"• {name} {point}: {data['odds']:.2f} ({data['price']})\n"
                    keyboard.append([
                        InlineKeyboardButton(f"{name} {point}", callback_data=f"bet_total_{name}_{point}_{game_id}")
                    ])
                message += "\n"
            
            keyboard.append([InlineKeyboardButton("Back to Games", callback_data="cmd_live_games")])
            
            await update.callback_query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"Error showing game odds: {e}")
            await update.callback_query.edit_message_text(
                "Error loading game odds. Please try again.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Back to Games", callback_data="cmd_live_games")
                ]])
            )
    
    async def show_bet_amount_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                  team: str, bet_type: str, game_id: str = None):
        """Show bet amount input interface"""
        try:
            # Get current odds for this bet
            odds_data = await self.betting_engine.calculate_odds(team, bet_type)
            
            message = f"💰 *Place Your Bet*\n\n"
            message += f"🏆 *Team:* {team}\n"
            message += f"🎯 *Type:* {bet_type}\n"
            message += f"📊 *Odds:* {odds_data.odds:.2f}\n"
            message += f"💵 *Potential Payout:* ${100 * odds_data.odds:.2f} (for $100 bet)\n\n"
            message += f"*Enter your bet amount:*\n"
            message += f"Examples: 50, 100, 250, 500"
            
            # Store bet info in context for amount processing
            context.user_data['pending_bet'] = {
                'team': team,
                'bet_type': bet_type,
                'game_id': game_id,
                'odds': odds_data.odds
            }
            
            keyboard = [
                [InlineKeyboardButton("$50", callback_data="bet_amount_50")],
                [InlineKeyboardButton("$100", callback_data="bet_amount_100")],
                [InlineKeyboardButton("$250", callback_data="bet_amount_250")],
                [InlineKeyboardButton("$500", callback_data="bet_amount_500")],
                [InlineKeyboardButton("Custom Amount", callback_data="bet_amount_custom")],
                [InlineKeyboardButton("Back", callback_data="cmd_live_games")]
            ]
            
            await update.callback_query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"Error showing bet amount input: {e}")
            await update.callback_query.edit_message_text(
                "Error loading bet interface. Please try again.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Back to Main Menu", callback_data="back_to_main")
                ]])
            )
    
    async def show_quick_bet_interface(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show quick bet interface with popular teams"""
        try:
            # Show loading state first
            await update.callback_query.edit_message_text(
                "⚡ Loading live odds...",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_to_main")]])
            )

            # Get popular teams with fast ML odds
            popular_teams = ["Real Madrid", "Barcelona", "Manchester City", "Liverpool", "Bayern Munich"]
            live_odds = await self.betting_engine.get_live_odds(popular_teams)

            message = "⚡ *Quick Bet Interface*\n\n"
            message += "Select a team to place a quick bet:\n\n"

            keyboard = []
            shown_any = False
            for team in popular_teams:
                team_odds = live_odds.get(team, [])
                if team_odds:
                    ml_odds = next((odds for odds in team_odds if odds.bet_type == "ML"), None)
                    if ml_odds:
                        shown_any = True
                        message += f"🏆 *{team}* - ML: {ml_odds.odds:.2f}\n"
                        keyboard.append([InlineKeyboardButton(f"{team} ML", callback_data=f"quick_bet_{team}_ML")])

            if not shown_any:
                message += "No live odds available right now. Please try again later.\n"
            
            keyboard.extend([
                [InlineKeyboardButton("📊 Live Games", callback_data="cmd_live_games")],
                [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main")]
            ])
            
            await update.callback_query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"Error showing quick bet interface: {e}")
            await update.callback_query.edit_message_text(
                "Error loading quick bet interface. Please try again.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Back to Main Menu", callback_data="back_to_main")
                ]])
            )
    
    async def show_betting_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show enhanced betting statistics"""
        try:
            # Get user stats (this would need to be passed from the main bot)
            user_id = update.callback_query.from_user.id
            
            message = "📊 *Enhanced Betting Statistics*\n\n"
            message += "🏆 *Live Performance:*\n"
            message += "• Active Bets: 0\n"
            message += "• Pending Settlements: 0\n"
            message += "• Today's P&L: $0.00\n\n"
            
            message += "📈 *Market Overview:*\n"
            message += "• Available Games: 10+\n"
            message += "• Live Odds: Real-time\n"
            message += "• Settlement: Automatic\n\n"
            
            message += "🎯 *Quick Actions:*\n"
            
            keyboard = [
                [InlineKeyboardButton("⚡ Quick Bet", callback_data="cmd_quick_bet")],
                [InlineKeyboardButton("📊 Live Games", callback_data="cmd_live_games")],
                [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main")]
            ]
            
            await update.callback_query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"Error showing betting stats: {e}")
            await update.callback_query.edit_message_text(
                "Error loading statistics. Please try again.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Back to Main Menu", callback_data="back_to_main")
                ]])
            )
    
    def create_enhanced_main_menu(self, user_data: Dict[str, Any]) -> tuple[str, InlineKeyboardMarkup]:
        """Create enhanced main menu with new UI features"""
        balance = user_data.get('balance', 0.0)
        is_admin = user_data.get('is_admin', False)
        preferred_voice = user_data.get('preferred_voice', 'Taylor Swift')
        
        welcome_message = f"""🎰 *Sports Betting Bot - Enhanced UI* 🎰

Hey! Welcome to the ultimate sports betting experience with real odds and live games.

💰 *Your Balance:* ${balance:,.2f}
🎤 *Voice:* {preferred_voice}

*🚀 NEW FEATURES:*
• Live soccer games with real odds
• Quick bet interface
• Real-time market data
• Automatic bet settlement

Choose an option below:"""
        
        # Enhanced keyboard with 3 buttons per row
        keyboard = [
            [InlineKeyboardButton("⚡ Quick Bet", callback_data="cmd_quick_bet"),
             InlineKeyboardButton("📊 Live Games", callback_data="cmd_live_games"),
             InlineKeyboardButton("💰 Balance", callback_data="cmd_balance")],
            [InlineKeyboardButton("📈 Enhanced Stats", callback_data="cmd_enhanced_stats"),
             InlineKeyboardButton("🎯 My Bets", callback_data="cmd_my_bets"),
             InlineKeyboardButton("🏆 Leaderboard", callback_data="cmd_leaderboard")],
            [InlineKeyboardButton("🎤 Voice", callback_data="cmd_voice"),
             InlineKeyboardButton("💡 Tips", callback_data="cmd_tips"),
             InlineKeyboardButton("🤖 Ask AI", callback_data="cmd_ask")],
            [InlineKeyboardButton("🎲 AI Bet", callback_data="cmd_ai_bet"),
             InlineKeyboardButton("💳 My Wallets", callback_data="cmd_my_wallets"),
             InlineKeyboardButton("📝 Payment History", callback_data="cmd_payment_history")],
            [InlineKeyboardButton("💸 Deposit", callback_data="cmd_deposit"),
             InlineKeyboardButton("💵 Withdraw", callback_data="cmd_withdraw"),
             InlineKeyboardButton("❓ Help", callback_data="cmd_help")]
        ]
        
        # Add admin buttons if user is admin
        if is_admin:
            keyboard.append([InlineKeyboardButton("🔧 Admin Panel", callback_data="cmd_admin")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        return welcome_message, reply_markup

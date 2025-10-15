import random
import math
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from sports_api import SportsAPIService

@dataclass
class BettingOdds:
    """Represents betting odds for a team/event"""
    team: str
    bet_type: str
    odds: float
    probability: float
    payout_multiplier: float

@dataclass
class BetResult:
    """Represents the result of a bet"""
    bet_id: int
    user_id: int
    team: str
    bet_type: str
    amount: float
    odds: float
    result: str  # 'won', 'lost', 'pending'
    payout: float
    profit: float
    created_at: datetime
    settled_at: Optional[datetime] = None

class BettingEngine:
    """Advanced betting engine with real odds calculation and result simulation"""
    
    def __init__(self):
        self.odds_cache = {}
        self.cache_duration = 300  # 5 minutes
        self.house_edge = 0.05  # 5% house edge
        self.sports_api = SportsAPIService()
        
    async def calculate_odds(self, team: str, bet_type: str, market_data: Dict = None) -> BettingOdds:
        """Calculate odds for a bet - try real API first, fallback to simulation"""
        cache_key = f"{team}_{bet_type}"
        
        # Check cache
        if cache_key in self.odds_cache:
            cached_odds, timestamp = self.odds_cache[cache_key]
            if datetime.now().timestamp() - timestamp < self.cache_duration:
                return cached_odds
        
        # Try to get real odds from The Odds API
        try:
            real_odds = await self._get_real_odds(team, bet_type)
            if real_odds:
                # Apply house edge to real odds
                adjusted_odds = real_odds.odds * (1 - self.house_edge)
                payout_multiplier = adjusted_odds - 1
                probability = 1 / adjusted_odds if adjusted_odds > 0 else 0.1
                
                betting_odds = BettingOdds(
                    team=team,
                    bet_type=bet_type,
                    odds=adjusted_odds,
                    probability=probability,
                    payout_multiplier=payout_multiplier
                )
                
                # Cache the result
                self.odds_cache[cache_key] = (betting_odds, datetime.now().timestamp())
                return betting_odds
        except Exception as e:
            print(f"Error getting real odds: {e}")
        
        # Fallback to simulated odds
        return self._calculate_simulated_odds(team, bet_type, market_data)
    
    def _calculate_simulated_odds(self, team: str, bet_type: str, market_data: Dict = None) -> BettingOdds:
        """Calculate simulated odds (fallback method)"""
        # Base probability calculation
        base_probability = self._get_base_probability(team, bet_type, market_data)
        
        # Apply market factors
        market_factor = self._get_market_factor(team, bet_type)
        adjusted_probability = base_probability * market_factor
        
        # Apply house edge
        true_probability = adjusted_probability * (1 - self.house_edge)
        
        # Convert to odds
        if true_probability > 0:
            odds = 1 / true_probability
        else:
            odds = 10.0  # Default high odds
        
        # Round odds to reasonable values
        odds = self._round_odds(odds)
        
        # Calculate payout multiplier
        payout_multiplier = odds - 1
        
        betting_odds = BettingOdds(
            team=team,
            bet_type=bet_type,
            odds=odds,
            probability=true_probability,
            payout_multiplier=payout_multiplier
        )
        
        return betting_odds
    
    async def _get_real_odds(self, team: str, bet_type: str) -> Optional[BettingOdds]:
        """Get real odds from The Odds API"""
        try:
            # Find games for the team
            team_odds = await self.sports_api.get_live_odds_for_team(team, "soccer")
            
            if not team_odds:
                return None
            
            # Get the most recent game
            latest_odds = team_odds[0]
            
            # Extract odds for the specific bet type
            markets = latest_odds.markets
            
            if bet_type == "ML" and "ML" in markets:
                ml_markets = markets["ML"]
                for team_name, odds_data in ml_markets.items():
                    if team.lower() in team_name.lower():
                        return BettingOdds(
                            team=team,
                            bet_type=bet_type,
                            odds=odds_data["odds"],
                            probability=1/odds_data["odds"],
                            payout_multiplier=odds_data["odds"] - 1
                        )
            
            elif bet_type == "SPREAD" and "SPREAD" in markets:
                spread_markets = markets["SPREAD"]
                for team_name, odds_data in spread_markets.items():
                    if team.lower() in team_name.lower():
                        return BettingOdds(
                            team=team,
                            bet_type=bet_type,
                            odds=odds_data["odds"],
                            probability=1/odds_data["odds"],
                            payout_multiplier=odds_data["odds"] - 1
                        )
            
            elif bet_type in ["OVER", "UNDER"] and "TOTAL" in markets:
                total_markets = markets["TOTAL"]
                for name, odds_data in total_markets.items():
                    if bet_type.lower() in name.lower():
                        return BettingOdds(
                            team=team,
                            bet_type=bet_type,
                            odds=odds_data["odds"],
                            probability=1/odds_data["odds"],
                            payout_multiplier=odds_data["odds"] - 1
                        )
            
            return None
            
        except Exception as e:
            print(f"Error in _get_real_odds: {e}")
            return None
    
    def _get_base_probability(self, team: str, bet_type: str, market_data: Dict = None) -> float:
        """Get base probability for a team/bet type"""
        # Simulate realistic probabilities based on team strength
        team_strength = self._get_team_strength(team)
        
        if bet_type == "ML":
            # Money line probability
            if team_strength > 0.6:
                return 0.65  # Strong team
            elif team_strength > 0.4:
                return 0.50  # Average team
            else:
                return 0.35  # Weak team
        elif bet_type == "SPREAD":
            return 0.50  # Spread bets are typically 50/50
        elif bet_type in ["OVER", "UNDER"]:
            return 0.50  # Over/under typically 50/50
        elif bet_type == "TOTAL":
            return 0.50  # Total bets typically 50/50
        else:
            return 0.50  # Default
    
    def _get_team_strength(self, team: str) -> float:
        """Get team strength rating (0.0 to 1.0)"""
        # Simulate team strength based on team name patterns
        team_lower = team.lower()
        
        # Strong teams (higher probability)
        strong_teams = ['real madrid', 'barcelona', 'manchester city', 'liverpool', 'bayern', 
                       'lakers', 'warriors', 'celtics', 'heat', 'bucks']
        
        # Weak teams (lower probability)
        weak_teams = ['tottenham', 'arsenal', 'chelsea', 'manchester united', 'psg',
                     'knicks', 'pistons', 'magic', 'hornets', 'wizards']
        
        if any(strong in team_lower for strong in strong_teams):
            return 0.7 + random.uniform(0, 0.2)
        elif any(weak in team_lower for weak in weak_teams):
            return 0.2 + random.uniform(0, 0.2)
        else:
            return 0.4 + random.uniform(0, 0.4)
    
    def _get_market_factor(self, team: str, bet_type: str) -> float:
        """Get market factor affecting odds"""
        # Simulate market movement
        return 0.9 + random.uniform(0, 0.2)
    
    def _round_odds(self, odds: float) -> float:
        """Round odds to realistic values"""
        if odds < 1.1:
            return 1.1
        elif odds < 2.0:
            return round(odds, 1)
        elif odds < 10.0:
            return round(odds, 2)
        else:
            return round(odds, 1)
    
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
    
    async def simulate_bet_result(self, bet: Dict) -> BetResult:
        """Simulate the result of a bet - try real results first, fallback to simulation"""
        team = bet['team']
        bet_type = bet['bet_type']
        amount = bet['amount']
        bet_id = bet['bet_id']
        user_id = bet['user_id']
        created_at = bet['created_at']
        
        # Get odds for this bet
        odds_data = await self.calculate_odds(team, bet_type)
        odds = odds_data.odds
        
        # Try to get real game result
        try:
            real_result = await self._check_real_game_result(team, bet_type, odds_data)
            if real_result:
                if real_result["result"] == "won":
                    result = 'won'
                    payout = amount * odds
                    profit = payout - amount
                elif real_result["result"] == "lost":
                    result = 'lost'
                    payout = 0
                    profit = -amount
                else:  # push or pending
                    result = 'pending'
                    payout = amount  # Return original bet
                    profit = 0
                
                return BetResult(
                    bet_id=bet_id,
                    user_id=user_id,
                    team=team,
                    bet_type=bet_type,
                    amount=amount,
                    odds=odds,
                    result=result,
                    payout=payout,
                    profit=profit,
                    created_at=created_at,
                    settled_at=datetime.now()
                )
        except Exception as e:
            print(f"Error checking real game result: {e}")
        
        # Fallback to simulated result
        return self._simulate_bet_result_fallback(bet, odds)
    
    def _simulate_bet_result_fallback(self, bet: Dict, odds: float) -> BetResult:
        """Fallback simulation method"""
        team = bet['team']
        bet_type = bet['bet_type']
        amount = bet['amount']
        bet_id = bet['bet_id']
        user_id = bet['user_id']
        created_at = bet['created_at']
        
        # Simulate result with 10% win rate (hard mode)
        random_value = random.random()
        win_threshold = 0.10  # 10% chance to win
        
        if random_value < win_threshold:
            result = 'won'
            payout = amount * odds
            profit = payout - amount
        else:
            result = 'lost'
            payout = 0
            profit = -amount
        
        return BetResult(
            bet_id=bet_id,
            user_id=user_id,
            team=team,
            bet_type=bet_type,
            amount=amount,
            odds=odds,
            result=result,
            payout=payout,
            profit=profit,
            created_at=created_at,
            settled_at=datetime.now()
        )
    
    async def _check_real_game_result(self, team: str, bet_type: str, odds_data: BettingOdds) -> Optional[Dict[str, Any]]:
        """Check real game result from The Odds API"""
        try:
            # Find the game for this team
            game = await self.sports_api.find_game_by_teams(team, "", "soccer")
            if not game:
                return None
            
            # Get the game result
            game_result = await self.sports_api.get_game_result("soccer", game.id)
            if not game_result or not game_result.completed:
                return None
            
            # Calculate bet result using real game data
            bet_result = self.sports_api.calculate_bet_result(
                bet_type, team, game_result, 
                type('Odds', (), {
                    'markets': {
                        'ML': odds_data.markets.get('ML', {}),
                        'SPREAD': odds_data.markets.get('SPREAD', {}),
                        'TOTAL': odds_data.markets.get('TOTAL', {})
                    }
                })()
            )
            
            return bet_result
            
        except Exception as e:
            print(f"Error in _check_real_game_result: {e}")
            return None
    
    async def get_live_odds(self, teams: List[str]) -> Dict[str, List[BettingOdds]]:
        """Get live odds for multiple teams quickly (ML only, timeouts, concurrent)."""
        import asyncio
        live_odds: Dict[str, List[BettingOdds]] = {}

        async def fetch_team_ml(team_name: str) -> tuple[str, Optional[BettingOdds]]:
            try:
                # Cap per-call time to avoid UI hangs
                odds: BettingOdds = await asyncio.wait_for(self.calculate_odds(team_name, "ML"), timeout=4.0)
                return team_name, odds
            except Exception:
                # On timeout or API failure, fall back to simulated odds fast
                try:
                    fallback = self._calculate_simulated_odds(team_name, "ML")
                    return team_name, fallback
                except Exception:
                    return team_name, None

        tasks = [fetch_team_ml(team) for team in teams]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for res in results:
            if isinstance(res, tuple):
                team_name, odds = res
                if odds:
                    live_odds[team_name] = [odds]

        return live_odds
    
    def get_popular_teams(self) -> List[str]:
        """Get list of popular teams for live odds"""
        return [
            "Real Madrid", "Barcelona", "Manchester City", "Liverpool", "Bayern Munich",
            "Lakers", "Warriors", "Celtics", "Heat", "Bucks",
            "PSG", "Chelsea", "Arsenal", "Tottenham", "Manchester United"
        ]
    
    def calculate_parlay_odds(self, bets: List[Dict]) -> float:
        """Calculate odds for a parlay bet"""
        total_odds = 1.0
        
        for bet in bets:
            odds_data = self.calculate_odds(bet['team'], bet['bet_type'])
            total_odds *= odds_data.odds
        
        return total_odds
    
    def get_betting_tips(self) -> List[str]:
        """Get betting tips and advice"""
        tips = [
            "💡 Always bet within your budget - never bet more than you can afford to lose",
            "📊 Research team form and head-to-head records before placing bets",
            "🎯 Focus on value bets rather than just favorites",
            "⏰ Consider timing - odds can change throughout the day",
            "📈 Track your betting history to identify patterns",
            "🔄 Don't chase losses with bigger bets",
            "📱 Use the /odds command to check current odds before betting",
            "🏆 Consider live betting for better value opportunities"
        ]
        return random.sample(tips, 3)  # Return 3 random tips

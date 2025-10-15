import httpx
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from config import THE_ODDS_API_KEY, THE_ODDS_API_BASE_URL
import logging

logger = logging.getLogger(__name__)

@dataclass
class Game:
    """Represents a sports game"""
    id: str
    sport_key: str
    sport_title: str
    commence_time: datetime
    home_team: str
    away_team: str
    home_team_id: str
    away_team_id: str
    bookmakers: List[Dict]

@dataclass
class Odds:
    """Represents betting odds for a game"""
    game_id: str
    sport_key: str
    home_team: str
    away_team: str
    commence_time: datetime
    bookmaker: str
    markets: Dict[str, Any]

@dataclass
class GameResult:
    """Represents the result of a completed game"""
    game_id: str
    sport_key: str
    home_team: str
    away_team: str
    commence_time: datetime
    completed: bool
    scores: Optional[Dict[str, int]] = None
    winner: Optional[str] = None

class SportsAPIService:
    """Service for interacting with The Odds API"""
    
    def __init__(self):
        self.api_key = THE_ODDS_API_KEY
        self.base_url = THE_ODDS_API_BASE_URL
        self.timeout = 30.0
        
    async def get_available_sports(self) -> List[Dict[str, Any]]:
        """Get list of available sports"""
        url = f"{self.base_url}/sports"
        params = {"apiKey": self.api_key}
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error fetching sports: {e}")
            return []
    
    async def get_games(self, sport_key: str = "soccer", 
                       regions: str = "us", 
                       markets: str = "h2h,spreads,totals") -> List[Game]:
        """Get upcoming games for a sport"""
        url = f"{self.base_url}/sports/{sport_key}/odds"
        params = {
            "apiKey": self.api_key,
            "regions": regions,
            "markets": markets,
            "oddsFormat": "american",
            "dateFormat": "iso"
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                games = []
                for game_data in data:
                    game = Game(
                        id=game_data.get("id"),
                        sport_key=game_data.get("sport_key"),
                        sport_title=game_data.get("sport_title"),
                        commence_time=datetime.fromisoformat(game_data.get("commence_time").replace("Z", "+00:00")),
                        home_team=game_data.get("home_team"),
                        away_team=game_data.get("away_team"),
                        home_team_id=game_data.get("home_team_id"),
                        away_team_id=game_data.get("away_team_id"),
                        bookmakers=game_data.get("bookmakers", [])
                    )
                    games.append(game)
                
                return games
        except Exception as e:
            logger.error(f"Error fetching games: {e}")
            return []
    
    async def get_game_odds(self, sport_key: str, game_id: str) -> Optional[Odds]:
        """Get odds for a specific game - use the games list instead of individual game API"""
        try:
            # Get all games and find the specific one
            games = await self.get_games(sport_key, regions="us", markets="h2h,spreads,totals")
            
            for game in games:
                if game.id == game_id:
                    # Get the first bookmaker's odds
                    if game.bookmakers:
                        bookmaker = game.bookmakers[0]
                        return Odds(
                            game_id=game.id,
                            sport_key=game.sport_key,
                            home_team=game.home_team,
                            away_team=game.away_team,
                            commence_time=game.commence_time,
                            bookmaker=bookmaker.get("title", "Unknown"),
                            markets=self._parse_markets([bookmaker])
                        )
            return None
        except Exception as e:
            logger.error(f"Error fetching game odds: {e}")
            return None
    
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
    
    async def get_game_result(self, sport_key: str, game_id: str) -> Optional[GameResult]:
        """Get result for a completed game"""
        url = f"{self.base_url}/sports/{sport_key}/scores"
        params = {
            "apiKey": self.api_key,
            "daysFrom": 1,  # Check last 1 day
            "dateFormat": "iso",
            "eventIds": game_id  # Filter to specific game
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                for game_data in data:
                    if game_data.get("id") == game_id:
                        scores = game_data.get("scores")
                        home_score = None
                        away_score = None
                        winner = None
                        
                        if scores:
                            for score in scores:
                                if score.get("name") == game_data.get("home_team"):
                                    home_score = score.get("score")
                                elif score.get("name") == game_data.get("away_team"):
                                    away_score = score.get("score")
                            
                            if home_score is not None and away_score is not None:
                                if home_score > away_score:
                                    winner = game_data.get("home_team")
                                elif away_score > home_score:
                                    winner = game_data.get("away_team")
                        
                        return GameResult(
                            game_id=game_data.get("id"),
                            sport_key=game_data.get("sport_key"),
                            home_team=game_data.get("home_team"),
                            away_team=game_data.get("away_team"),
                            commence_time=datetime.fromisoformat(game_data.get("commence_time").replace("Z", "+00:00")),
                            completed=game_data.get("completed", False),
                            scores={"home": home_score, "away": away_score} if home_score is not None else None,
                            winner=winner
                        )
                
                return None
        except Exception as e:
            logger.error(f"Error fetching game result: {e}")
            return None
    
    async def find_game_by_teams(self, team1: str, team2: str, sport_key: str = "soccer") -> Optional[Game]:
        """Find a game by team names"""
        games = await self.get_games(sport_key)
        
        for game in games:
            home_team = game.home_team.lower()
            away_team = game.away_team.lower()
            team1_lower = team1.lower()
            team2_lower = team2.lower()
            
            # Check if either team matches either side
            if ((team1_lower in home_team or team1_lower in away_team) and 
                (team2_lower in home_team or team2_lower in away_team)):
                return game
        
        return None
    
    async def get_live_odds_for_team(self, team_name: str, sport_key: str = "soccer") -> List[Odds]:
        """Get live odds for a specific team"""
        games = await self.get_games(sport_key)
        team_odds = []
        
        for game in games:
            if (team_name.lower() in game.home_team.lower() or 
                team_name.lower() in game.away_team.lower()):
                odds = await self.get_game_odds(sport_key, game.id)
                if odds:
                    team_odds.append(odds)
        
        return team_odds
    
    def calculate_bet_result(self, bet_type: str, bet_team: str, 
                           game_result: GameResult, odds_data: Odds) -> Dict[str, Any]:
        """Calculate if a bet won or lost based on real game results"""
        if not game_result.completed or not game_result.scores:
            return {"result": "pending", "reason": "Game not completed"}
        
        home_score = game_result.scores.get("home", 0)
        away_score = game_result.scores.get("away", 0)
        home_team = game_result.home_team
        away_team = game_result.away_team
        
        # Determine which team the bet was on
        if bet_team.lower() in home_team.lower():
            bet_side = "home"
            opponent_side = "away"
            bet_score = home_score
            opponent_score = away_score
        elif bet_team.lower() in away_team.lower():
            bet_side = "away"
            opponent_side = "home"
            bet_score = away_score
            opponent_score = home_score
        else:
            return {"result": "error", "reason": "Team not found in game"}
        
        # Check bet result based on type
        if bet_type == "ML":  # Money Line
            if bet_score > opponent_score:
                return {"result": "won", "reason": f"{bet_team} won {bet_score}-{opponent_score}"}
            elif bet_score < opponent_score:
                return {"result": "lost", "reason": f"{bet_team} lost {bet_score}-{opponent_score}"}
            else:
                return {"result": "push", "reason": "Game ended in tie"}
        
        elif bet_type == "SPREAD":  # Point Spread
            # Get spread from odds data
            spread_markets = odds_data.markets.get("SPREAD", {})
            spread_point = 0
            
            for team, data in spread_markets.items():
                if bet_team.lower() in team.lower():
                    spread_point = data.get("point", 0)
                    break
            
            adjusted_bet_score = bet_score + spread_point
            if adjusted_bet_score > opponent_score:
                return {"result": "won", "reason": f"{bet_team} covered spread ({bet_score}+{spread_point} vs {opponent_score})"}
            elif adjusted_bet_score < opponent_score:
                return {"result": "lost", "reason": f"{bet_team} didn't cover spread ({bet_score}+{spread_point} vs {opponent_score})"}
            else:
                return {"result": "push", "reason": "Spread push"}
        
        elif bet_type in ["OVER", "UNDER"]:  # Total Points
            total_points = bet_score + opponent_score
            total_markets = odds_data.markets.get("TOTAL", {})
            total_line = 0
            
            for name, data in total_markets.items():
                if bet_type.lower() in name.lower():
                    total_line = data.get("point", 0)
                    break
            
            if bet_type == "OVER":
                if total_points > total_line:
                    return {"result": "won", "reason": f"Total {total_points} > {total_line}"}
                elif total_points < total_line:
                    return {"result": "lost", "reason": f"Total {total_points} < {total_line}"}
                else:
                    return {"result": "push", "reason": "Total push"}
            else:  # UNDER
                if total_points < total_line:
                    return {"result": "won", "reason": f"Total {total_points} < {total_line}"}
                elif total_points > total_line:
                    return {"result": "lost", "reason": f"Total {total_points} > {total_line}"}
                else:
                    return {"result": "push", "reason": "Total push"}
        
        return {"result": "error", "reason": "Unknown bet type"}

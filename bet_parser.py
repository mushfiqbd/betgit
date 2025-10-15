import re
from typing import Optional, Dict, Any
from config import BET_TYPES

class BetParser:
    def __init__(self):
        self.bet_types = BET_TYPES
        # Regex patterns for different bet formats
        self.patterns = [
            # "Team ML $500" format
            r'^(.+?)\s+(ML|SPREAD|OVER|UNDER|TOTAL)\s+\$?(\d+(?:\.\d+)?)$',
            # "Team Money Line $500" format
            r'^(.+?)\s+(Money\s+Line|Point\s+Spread|Over|Under|Total\s+Points)\s+\$?(\d+(?:\.\d+)?)$',
            # "Team ML 500" format (without $)
            r'^(.+?)\s+(ML|SPREAD|OVER|UNDER|TOTAL)\s+(\d+(?:\.\d+)?)$',
        ]
    
    def parse_bet(self, message: str) -> Optional[Dict[str, Any]]:
        """Parse a betting message and extract team, bet type, and amount"""
        message = message.strip()
        
        for pattern in self.patterns:
            match = re.match(pattern, message, re.IGNORECASE)
            if match:
                team = match.group(1).strip()
                bet_type_raw = match.group(2).strip().upper()
                amount_str = match.group(3)
                
                # Convert bet type to standard format
                bet_type = self._normalize_bet_type(bet_type_raw)
                
                try:
                    amount = float(amount_str)
                    if amount <= 0:
                        return None
                    
                    return {
                        'team': team,
                        'bet_type': bet_type,
                        'amount': amount,
                        'original_message': message
                    }
                except ValueError:
                    continue
        
        return None
    
    def _normalize_bet_type(self, bet_type_raw: str) -> str:
        """Normalize bet type to standard format"""
        bet_type_raw = bet_type_raw.upper().replace(' ', '')
        
        # Direct mappings
        if bet_type_raw in ['ML', 'MONEYLINE', 'MONEYLINE']:
            return 'ML'
        elif bet_type_raw in ['SPREAD', 'POINTSPREAD', 'POINTSPREAD']:
            return 'SPREAD'
        elif bet_type_raw in ['OVER', 'O']:
            return 'OVER'
        elif bet_type_raw in ['UNDER', 'U']:
            return 'UNDER'
        elif bet_type_raw in ['TOTAL', 'TOTALPOINTS']:
            return 'TOTAL'
        
        return bet_type_raw
    
    def validate_bet(self, bet_data: Dict[str, Any]) -> tuple[bool, str]:
        """Validate parsed bet data"""
        if not bet_data:
            return False, "Invalid bet format. Use: 'Team ML $500'"
        
        team = bet_data.get('team', '')
        bet_type = bet_data.get('bet_type', '')
        amount = bet_data.get('amount', 0)
        
        if not team or len(team) < 2:
            return False, "Team name too short"
        
        if bet_type not in self.bet_types:
            return False, f"Invalid bet type. Use: {', '.join(self.bet_types.keys())}"
        
        if amount < 1:
            return False, "Minimum bet amount is $1"
        
        if amount > 10000:
            return False, "Maximum bet amount is $10,000"
        
        return True, "Valid bet"
    
    def get_bet_examples(self) -> list:
        """Get example bet formats for help"""
        return [
            "Real Madrid ML $500",
            "Lakers SPREAD $250",
            "Over 2.5 TOTAL $100",
            "Barcelona Money Line $750",
            "Warriors Point Spread $300"
        ]

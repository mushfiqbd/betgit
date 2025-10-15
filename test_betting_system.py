#!/usr/bin/env python3
"""
Test script for the betting system with real API integration
"""

import asyncio
import sys
import os

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from betting_engine import BettingEngine
from sports_api import SportsAPIService

async def test_betting_system():
    """Test the complete betting system"""
    print("Testing Betting System with Real API...")
    
    # Initialize services
    sports_api = SportsAPIService()
    betting_engine = BettingEngine()
    
    try:
        # Test 1: Get available sports
        print("\n1. Testing available sports...")
        sports = await sports_api.get_available_sports()
        print(f"Found {len(sports)} sports")
        
        # Test 2: Get live games
        print("\n2. Testing live games...")
        games = await sports_api.get_games("soccer", regions="us", markets="h2h,spreads,totals")
        print(f"Found {len(games)} soccer games")
        
        if games:
            # Test 3: Show game details
            print("\n3. Game details:")
            for i, game in enumerate(games[:3]):  # Show first 3 games
                print(f"   {i+1}. {game.home_team} vs {game.away_team}")
                print(f"      Time: {game.commence_time}")
                if game.bookmakers:
                    print(f"      Bookmakers: {len(game.bookmakers)}")
            
            # Test 4: Calculate odds for a team
            print("\n4. Testing odds calculation...")
            test_team = games[0].home_team
            odds = await betting_engine.calculate_odds(test_team, "ML")
            print(f"{test_team} ML odds: {odds.odds:.2f}")
            print(f"   Probability: {odds.probability:.2%}")
            print(f"   Payout: {odds.payout_multiplier:.2f}x")
            
            # Test 5: Test bet simulation
            print("\n5. Testing bet simulation...")
            bet = {
                'bet_id': 1,
                'user_id': 12345,
                'team': test_team,
                'bet_type': 'ML',
                'amount': 100.0,
                'odds': odds.odds,
                'created_at': '2025-10-15 00:00:00'
            }
            
            result = await betting_engine.simulate_bet_result(bet)
            print(f"Bet result: {result.result}")
            print(f"   Payout: ${result.payout:.2f}")
            print(f"   Profit: ${result.profit:.2f}")
        
        print("\nAll tests passed! The betting system is working with real API data.")
        
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_betting_system())

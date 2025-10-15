import requests
import asyncio
from typing import Optional
import httpx
from config import ELEVENLABS_API_KEY, VOICE_OPTIONS

class VoiceGenerator:
    def __init__(self):
        self.api_key = ELEVENLABS_API_KEY
        self.base_url = "https://api.elevenlabs.io/v1"
        self.voice_options = VOICE_OPTIONS
    
    async def generate_voice(self, text: str, voice_name: str = "Taylor Swift") -> Optional[bytes]:
        """Generate voice audio from text using ElevenLabs API"""
        if not self.api_key or self.api_key == 'your_elevenlabs_api_key_here':
            print("ElevenLabs API key not configured")
            return None
        
        # Use a default voice ID if the selected voice is not found
        voice_id = self.voice_options.get(voice_name, "21m00Tcm4TlvDq8ikWAM")
        
        url = f"{self.base_url}/text-to-speech/{voice_id}"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key
        }
        
        data = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.5
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=data, headers=headers)
                if response.status_code == 200:
                    return response.content
                else:
                    print(f"Error generating voice: {response.status_code} - {response.text}")
                    return None
        except Exception as e:
            print(f"Error in voice generation: {e}")
            return None
    
    def get_available_voices(self) -> dict:
        """Get list of available voices"""
        return self.voice_options
    
    def format_bet_message(self, team: str, bet_type: str, amount: float) -> str:
        """Format the bet message for voice generation"""
        bet_type_full = {
            "ML": "Money Line",
            "SPREAD": "Point Spread",
            "OVER": "Over",
            "UNDER": "Under",
            "TOTAL": "Total Points"
        }.get(bet_type.upper(), bet_type)
        
        return f"Bet placed! {team} {bet_type_full} for ${amount:,.0f}. Good luck!"

    def format_win_message(self, team: str, bet_type: str, amount: float, payout: float) -> str:
        """Format the win message for voice generation"""
        bet_type_full = {
            "ML": "Money Line",
            "SPREAD": "Point Spread",
            "OVER": "Over",
            "UNDER": "Under",
            "TOTAL": "Total Points"
        }.get(bet_type.upper(), bet_type)
        
        return f"Congratulations! You won! {team} {bet_type_full} for ${amount:,.0f}. You earned ${payout:,.0f}! Great job!"

    def format_loss_message(self, team: str, bet_type: str, amount: float) -> str:
        """Format the loss message for voice generation"""
        bet_type_full = {
            "ML": "Money Line",
            "SPREAD": "Point Spread",
            "OVER": "Over",
            "UNDER": "Under",
            "TOTAL": "Total Points"
        }.get(bet_type.upper(), bet_type)
        
        return f"Better luck next time! {team} {bet_type_full} for ${amount:,.0f} didn't work out this time. Keep trying!"

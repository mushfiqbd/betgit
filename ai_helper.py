import os
from typing import Optional, List, Dict
from config import OPENAI_API_KEY
import httpx


class AIHelper:
    """Lightweight helper around OpenAI Chat Completions API via HTTPX."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key or OPENAI_API_KEY
        self.model = model
        self.base_url = "https://api.openai.com/v1/chat/completions"

    async def ask(self, prompt: str, system: str = "You are a helpful assistant.") -> Optional[str]:
        if not self.api_key:
            return None
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload: Dict = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.7,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(self.base_url, headers=headers, json=payload)
            if resp.status_code != 200:
                return None
            data = resp.json()
            try:
                return data["choices"][0]["message"]["content"].strip()
            except Exception:
                return None

    async def suggest_bet(self, team_hint: str) -> Optional[Dict[str, str]]:
        """Return a structured bet suggestion dict: {team, bet_type, reason}"""
        system = "You are a sports betting assistant. Suggest safe, fun, simulated bets."
        user = (
            "Suggest one simulated bet as JSON with keys team, bet_type, reason. "
            f"Team hint: {team_hint}. Bet types: ML, SPREAD, OVER, UNDER, TOTAL."
        )
        answer = await self.ask(user, system)
        if not answer:
            return None
        # Best-effort JSON extraction
        import json, re
        match = re.search(r"\{[\s\S]*\}", answer)
        if not match:
            return None
        try:
            obj = json.loads(match.group(0))
            team = str(obj.get("team") or team_hint).strip()
            bet_type = str(obj.get("bet_type") or "ML").upper().strip()
            reason = str(obj.get("reason") or "Fun pick").strip()
            return {"team": team, "bet_type": bet_type, "reason": reason}
        except Exception:
            return None



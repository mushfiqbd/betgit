import sqlite3
import json
from typing import Optional, Dict, Any, List
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_path: str = "betting_bot.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                preferred_voice TEXT DEFAULT 'Taylor Swift',
                balance REAL DEFAULT 0.0,
                total_bets INTEGER DEFAULT 0,
                total_wagered REAL DEFAULT 0.0,
                total_winnings REAL DEFAULT 0.0,
                is_admin BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Bets table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bets (
                bet_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                team TEXT NOT NULL,
                bet_type TEXT NOT NULL,
                amount REAL NOT NULL,
                odds REAL DEFAULT 1.0,
                status TEXT DEFAULT 'pending',
                result TEXT DEFAULT 'pending',
                payout REAL DEFAULT 0.0,
                profit REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                settled_at TIMESTAMP NULL,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Live odds cache table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS live_odds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team TEXT NOT NULL,
                bet_type TEXT NOT NULL,
                odds REAL NOT NULL,
                probability REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Betting tips table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS betting_tips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tip_text TEXT NOT NULL,
                category TEXT DEFAULT 'general',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        # Run lightweight migrations to add any missing columns
        self._migrate_schema(conn)
        conn.close()

    def _migrate_schema(self, conn: sqlite3.Connection) -> None:
        """Ensure required columns exist; add them if missing (idempotent)."""
        cursor = conn.cursor()
        # Helper to fetch existing columns
        def existing_columns(table: str) -> set:
            cursor.execute(f"PRAGMA table_info({table})")
            return {row[1] for row in cursor.fetchall()}

        # users table required columns and their SQL definitions
        users_cols = existing_columns('users')
        add_statements = []
        if 'preferred_voice' not in users_cols:
            add_statements.append("ALTER TABLE users ADD COLUMN preferred_voice TEXT DEFAULT 'Taylor Swift'")
        if 'balance' not in users_cols:
            add_statements.append("ALTER TABLE users ADD COLUMN balance REAL DEFAULT 0.0")
        if 'total_bets' not in users_cols:
            add_statements.append("ALTER TABLE users ADD COLUMN total_bets INTEGER DEFAULT 0")
        if 'total_wagered' not in users_cols:
            add_statements.append("ALTER TABLE users ADD COLUMN total_wagered REAL DEFAULT 0.0")
        if 'total_winnings' not in users_cols:
            add_statements.append("ALTER TABLE users ADD COLUMN total_winnings REAL DEFAULT 0.0")
        if 'is_admin' not in users_cols:
            add_statements.append("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT FALSE")
        if 'created_at' not in users_cols:
            add_statements.append("ALTER TABLE users ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        if 'updated_at' not in users_cols:
            add_statements.append("ALTER TABLE users ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")

        for stmt in add_statements:
            try:
                cursor.execute(stmt)
            except Exception:
                # Ignore if already exists or other benign migration races
                pass
        conn.commit()
    
    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user information by user_id"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_id, username, first_name, last_name, preferred_voice, 
                   balance, total_bets, total_wagered, is_admin, created_at
            FROM users WHERE user_id = ?
        ''', (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'user_id': result[0],
                'username': result[1],
                'first_name': result[2],
                'last_name': result[3],
                'preferred_voice': result[4],
                'balance': result[5],
                'total_bets': result[6],
                'total_wagered': result[7],
                'is_admin': result[8],
                'created_at': result[9]
            }
        return None
    
    def create_user(self, user_id: int, username: str = None, 
                   first_name: str = None, last_name: str = None) -> bool:
        """Create a new user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO users (user_id, username, first_name, last_name)
                VALUES (?, ?, ?, ?)
            ''', (user_id, username, first_name, last_name))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()
    
    def update_user_voice(self, user_id: int, voice: str) -> bool:
        """Update user's preferred voice"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE users SET preferred_voice = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (voice, user_id))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    def create_bet(self, user_id: int, team: str, bet_type: str, amount: float, odds: float = 1.0) -> int:
        """Create a new bet and return bet_id"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO bets (user_id, team, bet_type, amount, odds)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, team, bet_type, amount, odds))
            
            bet_id = cursor.lastrowid
            
            # Update user's total bets and wagered amount
            cursor.execute('''
                UPDATE users 
                SET total_bets = total_bets + 1, 
                    total_wagered = total_wagered + ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (amount, user_id))
            
            conn.commit()
            return bet_id
        finally:
            conn.close()
    
    def update_bet_result(self, bet_id: int, result: str, payout: float, profit: float) -> bool:
        """Update bet result and payout"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE bets 
                SET result = ?, payout = ?, profit = ?, settled_at = CURRENT_TIMESTAMP
                WHERE bet_id = ?
            ''', (result, payout, profit, bet_id))
            
            # Note: total_winnings is calculated from bets table, not stored in users table
            
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Get comprehensive user statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Basic user info
            cursor.execute('''
                SELECT total_bets, total_wagered, created_at
                FROM users WHERE user_id = ?
            ''', (user_id,))
            user_data = cursor.fetchone()
            
            if not user_data:
                return {}
            
            # Betting statistics
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_bets,
                    SUM(amount) as total_wagered,
                    SUM(CASE WHEN result = 'won' THEN payout ELSE 0 END) as total_winnings,
                    SUM(CASE WHEN result = 'won' THEN profit ELSE 0 END) as total_profit,
                    SUM(CASE WHEN result = 'lost' THEN amount ELSE 0 END) as total_losses,
                    COUNT(CASE WHEN result = 'won' THEN 1 END) as wins,
                    COUNT(CASE WHEN result = 'lost' THEN 1 END) as losses
                FROM bets WHERE user_id = ?
            ''', (user_id,))
            
            stats = cursor.fetchone()
            
            # Recent performance (last 10 bets)
            cursor.execute('''
                SELECT result FROM bets 
                WHERE user_id = ? AND result != 'pending'
                ORDER BY created_at DESC LIMIT 10
            ''', (user_id,))
            recent_results = [row[0] for row in cursor.fetchall()]
            
            return {
                'total_bets': stats[0] or 0,
                'total_wagered': stats[1] or 0,
                'total_winnings': stats[2] or 0,
                'total_profit': stats[3] or 0,
                'total_losses': stats[4] or 0,
                'wins': stats[5] or 0,
                'losses': stats[6] or 0,
                'win_rate': (stats[5] / (stats[5] + stats[6]) * 100) if (stats[5] + stats[6]) > 0 else 0,
                'recent_performance': recent_results,
                'member_since': user_data[2]
            }
        finally:
            conn.close()
    
    def get_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get betting leaderboard"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT 
                    u.username, u.first_name, u.last_name,
                    COUNT(b.bet_id) as total_bets,
                    SUM(b.amount) as total_wagered,
                    SUM(CASE WHEN b.result = 'won' THEN b.payout ELSE 0 END) as total_winnings,
                    SUM(CASE WHEN b.result = 'won' THEN b.profit ELSE 0 END) as total_profit
                FROM users u
                LEFT JOIN bets b ON u.user_id = b.user_id
                GROUP BY u.user_id
                HAVING total_bets > 0
                ORDER BY total_profit DESC
                LIMIT ?
            ''', (limit,))
            
            results = cursor.fetchall()
            return [
                {
                    'username': row[0] or 'Unknown',
                    'first_name': row[1] or 'Unknown',
                    'last_name': row[2] or '',
                    'total_bets': row[3],
                    'total_wagered': row[4] or 0,
                    'total_winnings': row[5] or 0,
                    'total_profit': row[6] or 0
                }
                for row in results
            ]
        finally:
            conn.close()
    
    def save_live_odds(self, team: str, bet_type: str, odds: float, probability: float):
        """Save live odds to cache"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO live_odds (team, bet_type, odds, probability)
                VALUES (?, ?, ?, ?)
            ''', (team, bet_type, odds, probability))
            conn.commit()
        finally:
            conn.close()
    
    def get_live_odds(self, team: str = None) -> List[Dict[str, Any]]:
        """Get live odds from cache"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            if team:
                cursor.execute('''
                    SELECT team, bet_type, odds, probability, created_at
                    FROM live_odds 
                    WHERE team = ? AND created_at > datetime('now', '-5 minutes')
                    ORDER BY created_at DESC
                ''', (team,))
            else:
                cursor.execute('''
                    SELECT team, bet_type, odds, probability, created_at
                    FROM live_odds 
                    WHERE created_at > datetime('now', '-5 minutes')
                    ORDER BY created_at DESC
                ''')
            
            results = cursor.fetchall()
            return [
                {
                    'team': row[0],
                    'bet_type': row[1],
                    'odds': row[2],
                    'probability': row[3],
                    'created_at': row[4]
                }
                for row in results
            ]
        finally:
            conn.close()
    
    def update_user_balance(self, user_id: int, amount: float) -> bool:
        """Update user balance (add or subtract)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE users 
                SET balance = balance + ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (amount, user_id))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    def deduct_bet_amount(self, user_id: int, amount: float) -> bool:
        """Deduct bet amount from user balance"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check if user has sufficient balance
            cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
            result = cursor.fetchone()
            if not result or result[0] < amount:
                return False
            
            # Deduct the amount
            cursor.execute('''
                UPDATE users 
                SET balance = balance - ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (amount, user_id))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    def add_winnings(self, user_id: int, amount: float) -> bool:
        """Add winnings to user balance"""
        return self.update_user_balance(user_id, amount)
    
    def set_admin(self, user_id: int, is_admin: bool = True) -> bool:
        """Set user as admin"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE users 
                SET is_admin = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (is_admin, user_id))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    def is_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT is_admin FROM users WHERE user_id = ?', (user_id,))
            result = cursor.fetchone()
            return result[0] if result else False
        finally:
            conn.close()
    
    def get_all_admins(self) -> List[Dict[str, Any]]:
        """Get all admin users"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT user_id, username, first_name, last_name, balance, 
                       total_winnings, is_admin, created_at
                FROM users 
                WHERE is_admin = 1
                ORDER BY created_at ASC
            ''')
            
            columns = [description[0] for description in cursor.description]
            results = []
            
            for row in cursor.fetchall():
                user_dict = dict(zip(columns, row))
                results.append(user_dict)
            
            return results
        finally:
            conn.close()
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all users (admin only)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT user_id, username, first_name, last_name, balance, 
                       total_bets, total_wagered, is_admin, created_at
                FROM users
                ORDER BY created_at DESC
            ''')
            
            results = cursor.fetchall()
            return [
                {
                    'user_id': row[0],
                    'username': row[1],
                    'first_name': row[2],
                    'last_name': row[3],
                    'balance': row[4],
                    'total_bets': row[5],
                    'total_wagered': row[6],
                    'is_admin': row[7],
                    'created_at': row[8]
                }
                for row in results
            ]
        finally:
            conn.close()
    
    def get_user_bets(self, user_id: int, limit: int = 10) -> list:
        """Get user's recent bets"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT bet_id, team, bet_type, amount, status, created_at
            FROM bets 
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (user_id, limit))
        
        results = cursor.fetchall()
        conn.close()
        
        return [
            {
                'bet_id': row[0],
                'team': row[1],
                'bet_type': row[2],
                'amount': row[3],
                'status': row[4],
                'created_at': row[5]
            }
            for row in results
        ]
    
    def get_betting_tips(self) -> List[str]:
        """Get betting tips"""
        return [
            "Always bet within your means - never bet more than you can afford to lose",
            "Research teams and players before placing bets",
            "Don't chase losses with bigger bets",
            "Keep track of your betting history",
            "Set a budget and stick to it",
            "Don't bet when emotional or under influence",
            "Diversify your bets across different sports and markets",
            "Take breaks from betting regularly"
        ]
    
    def get_popular_teams(self) -> List[str]:
        """Get popular teams for odds display"""
        return [
            "Real Madrid", "Barcelona", "Manchester United", "Liverpool", 
            "Chelsea", "Arsenal", "Manchester City", "Bayern Munich",
            "PSG", "Juventus", "AC Milan", "Inter Milan"
        ]
    
    def get_live_odds_for_teams(self, teams: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """Get live odds for multiple teams"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            placeholders = ','.join(['?' for _ in teams])
            cursor.execute(f'''
                SELECT team, bet_type, odds, probability, created_at
                FROM live_odds 
                WHERE team IN ({placeholders}) AND created_at > datetime('now', '-5 minutes')
                ORDER BY created_at DESC
            ''', teams)
            
            results = cursor.fetchall()
            odds_by_team = {}
            
            for row in results:
                team = row[0]
                if team not in odds_by_team:
                    odds_by_team[team] = []
                
                odds_by_team[team].append({
                    'team': row[0],
                    'bet_type': row[1],
                    'odds': row[2],
                    'probability': row[3],
                    'created_at': row[4]
                })
            
            return odds_by_team
        finally:
            conn.close()

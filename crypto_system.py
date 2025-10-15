import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

@dataclass
class WalletAddress:
    """Cryptocurrency wallet address"""
    currency: str  # BTC, USDT, ETH
    address: str
    network: str  # TRC20, ERC20, BEP20
    is_active: bool = True

@dataclass
class PaymentRequest:
    """Payment request for deposit/withdrawal"""
    request_id: int
    user_id: int
    type: str  # 'deposit' or 'withdraw'
    currency: str
    amount: float
    wallet_address: str
    proof_image: str = None
    status: str = 'pending'  # pending, approved, rejected
    admin_notes: str = None
    created_at: datetime = None
    processed_at: datetime = None

class CryptoSystem:
    """Cryptocurrency deposit/withdrawal system"""
    
    def __init__(self, db_path: str = "betting_bot.db"):
        self.db_path = db_path
        self.init_crypto_tables()
    
    def init_crypto_tables(self):
        """Initialize cryptocurrency related tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Admin wallet addresses table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_wallets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                currency TEXT NOT NULL,
                address TEXT NOT NULL,
                network TEXT NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # User wallet addresses table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_wallets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                currency TEXT NOT NULL,
                address TEXT NOT NULL,
                is_verified BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Payment requests table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payment_requests (
                request_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                currency TEXT NOT NULL,
                amount REAL NOT NULL,
                wallet_address TEXT NOT NULL,
                proof_image TEXT,
                status TEXT DEFAULT 'pending',
                admin_notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed_at TIMESTAMP NULL,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Payment history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payment_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                currency TEXT NOT NULL,
                amount REAL NOT NULL,
                transaction_hash TEXT,
                status TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_admin_wallet(self, currency: str, address: str, network: str) -> bool:
        """Add admin wallet address"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO admin_wallets (currency, address, network)
                VALUES (?, ?, ?)
            ''', (currency, address, network))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error adding admin wallet: {e}")
            return False
        finally:
            conn.close()
    
    def get_admin_wallets(self, currency: str = None) -> List[WalletAddress]:
        """Get admin wallet addresses"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            if currency:
                cursor.execute('''
                    SELECT currency, address, network, is_active
                    FROM admin_wallets 
                    WHERE currency = ? AND is_active = TRUE
                    ORDER BY created_at DESC
                ''', (currency,))
            else:
                cursor.execute('''
                    SELECT currency, address, network, is_active
                    FROM admin_wallets 
                    WHERE is_active = TRUE
                    ORDER BY created_at DESC
                ''')
            
            results = cursor.fetchall()
            return [
                WalletAddress(
                    currency=row[0],
                    address=row[1],
                    network=row[2],
                    is_active=row[3]
                )
                for row in results
            ]
        finally:
            conn.close()
    
    def create_payment_request(self, user_id: int, request_type: str, 
                              currency: str, amount: float, 
                              wallet_address: str, proof_image: str = None) -> int:
        """Create a payment request"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO payment_requests 
                (user_id, type, currency, amount, wallet_address, proof_image)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, request_type, currency, amount, wallet_address, proof_image))
            
            request_id = cursor.lastrowid
            conn.commit()
            return request_id
        except Exception as e:
            print(f"Error creating payment request: {e}")
            return None
        finally:
            conn.close()
    
    def get_pending_requests(self) -> List[PaymentRequest]:
        """Get all pending payment requests"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT request_id, user_id, type, currency, amount, 
                       wallet_address, proof_image, status, admin_notes,
                       created_at, processed_at
                FROM payment_requests 
                WHERE status = 'pending'
                ORDER BY created_at DESC
            ''')
            
            results = cursor.fetchall()
            return [
                PaymentRequest(
                    request_id=row[0],
                    user_id=row[1],
                    type=row[2],
                    currency=row[3],
                    amount=row[4],
                    wallet_address=row[5],
                    proof_image=row[6],
                    status=row[7],
                    admin_notes=row[8],
                    created_at=row[9],
                    processed_at=row[10]
                )
                for row in results
            ]
        finally:
            conn.close()
    
    def get_payment_request(self, request_id: int) -> PaymentRequest:
        """Get a specific payment request by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT request_id, user_id, type, currency, amount, 
                       wallet_address, proof_image, status, admin_notes,
                       created_at, processed_at
                FROM payment_requests 
                WHERE request_id = ?
            ''', (request_id,))
            
            result = cursor.fetchone()
            if not result:
                return None
            
            return PaymentRequest(
                request_id=result[0],
                user_id=result[1],
                type=result[2],
                currency=result[3],
                amount=result[4],
                wallet_address=result[5],
                proof_image=result[6],
                status=result[7],
                admin_notes=result[8],
                created_at=result[9],
                processed_at=result[10]
            )
        finally:
            conn.close()
    
    def approve_payment_request(self, request_id: int, admin_notes: str = None) -> bool:
        """Approve a payment request"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get request details
            cursor.execute('''
                SELECT user_id, type, amount FROM payment_requests 
                WHERE request_id = ?
            ''', (request_id,))
            result = cursor.fetchone()
            
            if not result:
                return False
            
            user_id, request_type, amount = result
            
            # Update request status
            cursor.execute('''
                UPDATE payment_requests 
                SET status = 'approved', admin_notes = ?, processed_at = CURRENT_TIMESTAMP
                WHERE request_id = ?
            ''', (admin_notes, request_id))
            
            # Update user balance
            if request_type == 'deposit':
                cursor.execute('''
                    UPDATE users 
                    SET balance = balance + ?, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                ''', (amount, user_id))
            elif request_type == 'withdraw':
                cursor.execute('''
                    UPDATE users 
                    SET balance = balance - ?, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                ''', (amount, user_id))
            
            # Add to payment history
            cursor.execute('''
                INSERT INTO payment_history 
                (user_id, type, currency, amount, status)
                SELECT user_id, type, currency, amount, 'completed'
                FROM payment_requests WHERE request_id = ?
            ''', (request_id,))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error approving payment request: {e}")
            return False
        finally:
            conn.close()
    
    def reject_payment_request(self, request_id: int, admin_notes: str) -> bool:
        """Reject a payment request"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE payment_requests 
                SET status = 'rejected', admin_notes = ?, processed_at = CURRENT_TIMESTAMP
                WHERE request_id = ?
            ''', (admin_notes, request_id))
            
            # Add to payment history
            cursor.execute('''
                INSERT INTO payment_history 
                (user_id, type, currency, amount, status)
                SELECT user_id, type, currency, amount, 'rejected'
                FROM payment_requests WHERE request_id = ?
            ''', (request_id,))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error rejecting payment request: {e}")
            return False
        finally:
            conn.close()
    
    def get_user_payment_requests(self, user_id: int) -> List[PaymentRequest]:
        """Get user's payment requests"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT request_id, user_id, type, currency, amount, 
                       wallet_address, proof_image, status, admin_notes,
                       created_at, processed_at
                FROM payment_requests 
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT 10
            ''', (user_id,))
            
            results = cursor.fetchall()
            return [
                PaymentRequest(
                    request_id=row[0],
                    user_id=row[1],
                    type=row[2],
                    currency=row[3],
                    amount=row[4],
                    wallet_address=row[5],
                    proof_image=row[6],
                    status=row[7],
                    admin_notes=row[8],
                    created_at=row[9],
                    processed_at=row[10]
                )
                for row in results
            ]
        finally:
            conn.close()
    
    def add_user_wallet(self, user_id: int, currency: str, address: str) -> bool:
        """Add user wallet address"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO user_wallets (user_id, currency, address)
                VALUES (?, ?, ?)
            ''', (user_id, currency, address))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error adding user wallet: {e}")
            return False
        finally:
            conn.close()
    
    def get_user_wallets(self, user_id: int) -> List[Dict[str, Any]]:
        """Get user's wallet addresses"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT currency, address, is_verified, created_at
                FROM user_wallets 
                WHERE user_id = ?
                ORDER BY created_at DESC
            ''', (user_id,))
            
            results = cursor.fetchall()
            return [
                {
                    'currency': row[0],
                    'address': row[1],
                    'is_verified': row[2],
                    'created_at': row[3]
                }
                for row in results
            ]
        finally:
            conn.close()
    
    def get_supported_currencies(self) -> List[Dict[str, Any]]:
        """Get supported cryptocurrencies"""
        return [
            {
                'currency': 'USDT',
                'name': 'Tether USD',
                'networks': ['TRC20', 'ERC20', 'BEP20'],
                'min_deposit': 10.0,
                'min_withdraw': 20.0
            },
            {
                'currency': 'BTC',
                'name': 'Bitcoin',
                'networks': ['BTC'],
                'min_deposit': 0.001,
                'min_withdraw': 0.002
            },
            {
                'currency': 'ETH',
                'name': 'Ethereum',
                'networks': ['ERC20'],
                'min_deposit': 0.01,
                'min_withdraw': 0.02
            }
        ]

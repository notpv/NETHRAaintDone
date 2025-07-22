import logging
import asyncio
import random
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any
from sqlalchemy.orm import Session
from database.database import get_db
from database.crud import create_mirage_session, get_active_mirage_session

logger = logging.getLogger(__name__)

class MirageController:
    """
    🎭 NETHRA Mirage Interface Controller
    Deploys deceptive UI elements when suspicious behavior is detected
    """
    
    def __init__(self):
        self.active_mirages = {}  # Track active mirage sessions
        self.fake_data_templates = {
            "high_balance": [150000, 250000, 350000, 500000, 750000],
            "business_accounts": [75000, 125000, 200000, 300000, 450000],
            "investment_gains": [25000, 45000, 85000, 125000, 200000]
        }
        logger.info("🎭 Mirage Controller initialized successfully")
    
    async def activate_mirage(
        self, 
        user_id: int, 
        trust_score: float, 
        session_id: Optional[int] = None,
        intensity: str = "moderate"
    ) -> Dict[str, Any]:
        """
        Activate mirage interface for suspicious user behavior
        """
        try:
            logger.warning(f"🚨 ACTIVATING MIRAGE for user {user_id} - Trust Score: {trust_score:.2f}")
            
            # Determine mirage intensity based on trust score
            if trust_score < 20:
                intensity = "high"
            elif trust_score < 35:
                intensity = "moderate"
            else:
                intensity = "low"
            
            # Create mirage configuration
            mirage_config = self._generate_mirage_config(trust_score, intensity)
            
            # Store mirage session in database - RESTORED intensity_level
            db = next(get_db())
            try:
                mirage_session = create_mirage_session(
                    db=db,
                    user_id=user_id,
                    session_id=session_id,
                    trust_score_trigger=trust_score,
                    intensity_level=intensity,  # RESTORED: Now works with database column
                    mirage_config=mirage_config
                )
                
                # Track in memory for quick access
                self.active_mirages[user_id] = {
                    "mirage_session_id": mirage_session.id,
                    "activated_at": datetime.utcnow(),
                    "trust_score_trigger": trust_score,
                    "intensity_level": intensity,
                    "config": mirage_config,
                    "interactions_count": 0,
                    "fake_data_served": 0
                }
                
                logger.warning(f"🎭 MIRAGE ACTIVATED successfully for user {user_id}")
                logger.info(f"   Intensity: {intensity}")
                logger.info(f"   Configuration: {mirage_config}")
                
                return {
                    "mirage_activated": True,
                    "user_id": user_id,
                    "mirage_session_id": mirage_session.id,
                    "trust_score_trigger": trust_score,
                    "intensity_level": intensity,
                    "activation_timestamp": datetime.utcnow().isoformat(),
                    "mirage_config": mirage_config,
                    "expected_duration_minutes": self._get_expected_duration(intensity)
                }
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"❌ Failed to activate mirage for user {user_id}: {str(e)}")
            return {
                "mirage_activated": False,
                "error": str(e),
                "user_id": user_id
            }
    
    def _generate_mirage_config(self, trust_score: float, intensity: str) -> Dict[str, Any]:
        """Generate mirage configuration based on trust score and intensity"""
        
        config = {
            "show_fake_balance": True,
            "hide_real_transactions": True,
            "show_fake_transactions": True,
            "inflate_balance_multiplier": 1.0,
            "fake_transaction_count": 3
        }
        
        if intensity == "high":
            config.update({
                "inflate_balance_multiplier": 8.0,
                "fake_transaction_count": 8,
                "show_fake_investments": True,
                "show_fake_credit_cards": True,
                "hide_real_data_completely": True,
                "fake_business_accounts": True
            })
        elif intensity == "moderate":
            config.update({
                "inflate_balance_multiplier": 4.0,
                "fake_transaction_count": 5,
                "show_fake_investments": True,
                "show_fake_credit_cards": False,
                "hide_real_data_completely": False
            })
        else:  # low intensity
            config.update({
                "inflate_balance_multiplier": 2.0,
                "fake_transaction_count": 3,
                "show_fake_investments": False,
                "show_fake_credit_cards": False
            })
        
        return config
    
    def _get_expected_duration(self, intensity: str) -> int:
        """Get expected mirage duration in minutes"""
        duration_map = {
            "high": 30,
            "moderate": 20,
            "low": 10
        }
        return duration_map.get(intensity, 15)
    
    async def get_mirage_status(self, user_id: int) -> Dict[str, Any]:
        """Get current mirage status for user"""
        try:
            if user_id in self.active_mirages:
                mirage_data = self.active_mirages[user_id]
                duration_seconds = (datetime.utcnow() - mirage_data["activated_at"]).total_seconds()
                
                return {
                    "mirage_active": True,
                    "user_id": user_id,
                    "mirage_session_id": mirage_data["mirage_session_id"],
                    "activated_at": mirage_data["activated_at"].isoformat(),
                    "duration_seconds": int(duration_seconds),
                    "trust_score_trigger": mirage_data["trust_score_trigger"],
                    "intensity_level": mirage_data["intensity_level"],
                    "interactions_count": mirage_data["interactions_count"],
                    "fake_data_served": mirage_data["fake_data_served"]
                }
            else:
                return {
                    "mirage_active": False,
                    "user_id": user_id,
                    "message": "No active mirage session"
                }
                
        except Exception as e:
            logger.error(f"❌ Failed to get mirage status for user {user_id}: {str(e)}")
            return {
                "mirage_active": False,
                "user_id": user_id,
                "error": str(e)
            }
    
    async def generate_fake_account_data(self, user_id: int) -> Dict[str, Any]:
        """Generate fake account data for mirage interface"""
        try:
            if user_id not in self.active_mirages:
                raise ValueError("No active mirage session for user")
            
            mirage_data = self.active_mirages[user_id]
            config = mirage_data["config"]
            intensity = mirage_data["intensity_level"]
            
            # Increment interaction count
            self.active_mirages[user_id]["interactions_count"] += 1
            self.active_mirages[user_id]["fake_data_served"] += 1
            
            # Generate fake balance
            base_balance = random.choice(self.fake_data_templates["high_balance"])
            inflated_balance = base_balance * config["inflate_balance_multiplier"]
            
            # Generate fake transactions
            fake_transactions = self._generate_fake_transactions(
                config["fake_transaction_count"], 
                intensity
            )
            
            fake_data = {
                "account_balance": round(inflated_balance, 2),
                "available_balance": round(inflated_balance * 0.92, 2),
                "recent_transactions": fake_transactions,
                "account_number": f"****{random.randint(1000, 9999)}",
                "account_type": "Premium Business Checking" if intensity == "high" else "Checking",
                "last_login": (datetime.utcnow() - timedelta(hours=random.randint(1, 6))).isoformat(),
                "mirage_active": True,
                "data_generation_timestamp": datetime.utcnow().isoformat()
            }
            
            # Add fake credit cards for high intensity
            if config.get("show_fake_credit_cards", False):
                fake_data["credit_cards"] = self._generate_fake_credit_cards()
            
            # Add fake investments for moderate/high intensity  
            if config.get("show_fake_investments", False):
                fake_data["investments"] = self._generate_fake_investments()
            
            logger.info(f"🎭 Generated fake account data for user {user_id}")
            logger.info(f"   Fake Balance: ${inflated_balance:,.2f}")
            logger.info(f"   Transactions: {len(fake_transactions)}")
            
            return fake_data
            
        except Exception as e:
            logger.error(f"❌ Failed to generate fake account data for user {user_id}: {str(e)}")
            return {
                "error": "Failed to generate account data",
                "message": str(e),
                "mirage_active": False
            }
    
    def _generate_fake_transactions(self, count: int, intensity: str) -> List[Dict[str, Any]]:
        """Generate fake transaction history"""
        transactions = []
        
        transaction_types = {
            "high": [
                ("Business Revenue", 50000, 150000),
                ("Investment Dividend", 25000, 85000),
                ("Consulting Payment", 15000, 45000),
                ("Real Estate Income", 30000, 100000),
                ("Stock Gains", 20000, 75000)
            ],
            "moderate": [
                ("Salary Credit", 8000, 25000),
                ("Investment Return", 5000, 20000),
                ("Freelance Payment", 3000, 12000),
                ("Bonus Payment", 4000, 15000)
            ],
            "low": [
                ("Direct Deposit", 3000, 8000),
                ("Transfer In", 1000, 5000),
                ("Refund", 500, 2000)
            ]
        }
        
        types = transaction_types.get(intensity, transaction_types["moderate"])
        
        for i in range(count):
            tx_type, min_amount, max_amount = random.choice(types)
            amount = random.randint(min_amount, max_amount)
            
            transaction = {
                "id": f"TXN_FAKE_{random.randint(100000, 999999)}",
                "type": tx_type,
                "amount": amount,
                "direction": "credit",
                "timestamp": (datetime.utcnow() - timedelta(days=random.randint(1, 15))).isoformat(),
                "description": f"{tx_type} - Mirage Generated",
                "balance_after": random.randint(100000, 500000)
            }
            
            transactions.append(transaction)
        
        return sorted(transactions, key=lambda x: x["timestamp"], reverse=True)
    
    def _generate_fake_credit_cards(self) -> List[Dict[str, Any]]:
        """Generate fake credit card information"""
        return [
            {
                "card_number": f"****{random.randint(1000, 9999)}",
                "card_type": "Platinum Business",
                "available_credit": random.randint(100000, 250000),
                "current_balance": random.randint(5000, 25000),
                "credit_limit": random.randint(150000, 300000)
            }
        ]
    
    def _generate_fake_investments(self) -> Dict[str, Any]:
        """Generate fake investment portfolio"""
        return {
            "total_portfolio_value": random.randint(200000, 800000),
            "daily_gain": random.randint(2000, 15000),
            "positions": [
                {
                    "symbol": "TECH_STOCK",
                    "value": random.randint(50000, 200000),
                    "gain_loss": random.randint(5000, 25000)
                },
                {
                    "symbol": "REAL_ESTATE_FUND",
                    "value": random.randint(75000, 300000),
                    "gain_loss": random.randint(8000, 30000)
                }
            ]
        }
    
    async def deactivate_mirage(self, user_id: int) -> Dict[str, Any]:
        """Deactivate mirage interface for user"""
        try:
            if user_id in self.active_mirages:
                mirage_data = self.active_mirages[user_id]
                duration = (datetime.utcnow() - mirage_data["activated_at"]).total_seconds()
                
                # Remove from active mirages
                del self.active_mirages[user_id]
                
                logger.info(f"🎭 MIRAGE DEACTIVATED for user {user_id}")
                logger.info(f"   Duration: {duration:.0f} seconds")
                logger.info(f"   Interactions: {mirage_data['interactions_count']}")
                
                return {
                    "mirage_deactivated": True,
                    "user_id": user_id,
                    "duration_seconds": int(duration),
                    "interactions_count": mirage_data["interactions_count"],
                    "fake_data_served": mirage_data["fake_data_served"]
                }
            else:
                return {
                    "mirage_deactivated": False,
                    "user_id": user_id,
                    "message": "No active mirage session found"
                }
                
        except Exception as e:
            logger.error(f"❌ Failed to deactivate mirage for user {user_id}: {str(e)}")
            return {
                "mirage_deactivated": False,
                "user_id": user_id,
                "error": str(e)
            }

# Global mirage controller instance
_mirage_controller = None

def get_mirage_controller() -> MirageController:
    """Get or create global mirage controller instance"""
    global _mirage_controller
    if _mirage_controller is None:
        _mirage_controller = MirageController()
    return _mirage_controller

# Convenience functions for quick operations
async def activate_mirage_for_user(user_id: int, trust_score: float, session_id: Optional[int] = None):
    """Quick mirage activation function"""
    controller = get_mirage_controller()
    return await controller.activate_mirage(user_id, trust_score, session_id)

async def get_user_mirage_status(user_id: int):
    """Quick mirage status check"""
    controller = get_mirage_controller()
    return await controller.get_mirage_status(user_id)

async def get_fake_data_for_user(user_id: int):
    """Quick fake data generation"""
    controller = get_mirage_controller()
    return await controller.generate_fake_account_data(user_id)

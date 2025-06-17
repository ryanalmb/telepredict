"""User management for Telegram bot."""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import aiofiles
import asyncio
from ..utils.logger import get_logger
from ..config.settings import settings

logger = get_logger(__name__)


class UserManager:
    """Manages user data and preferences."""
    
    def __init__(self):
        self.users_file = Path("data/users.json")
        self.users_file.parent.mkdir(parents=True, exist_ok=True)
        self.users_data = {}
        self.lock = asyncio.Lock()
        
        # Initialize users data
        asyncio.create_task(self._load_users_data())
    
    async def _load_users_data(self) -> None:
        """Load users data from file."""
        try:
            if self.users_file.exists():
                async with aiofiles.open(self.users_file, 'r') as f:
                    content = await f.read()
                    self.users_data = json.loads(content)
                logger.info(f"Loaded {len(self.users_data)} users from file")
            else:
                self.users_data = {}
                await self._save_users_data()
        except Exception as e:
            logger.error(f"Error loading users data: {e}")
            self.users_data = {}
    
    async def _save_users_data(self) -> None:
        """Save users data to file."""
        try:
            async with aiofiles.open(self.users_file, 'w') as f:
                await f.write(json.dumps(self.users_data, indent=2, default=str))
        except Exception as e:
            logger.error(f"Error saving users data: {e}")
    
    async def register_user(self, user_id: int, username: Optional[str] = None, 
                           first_name: Optional[str] = None) -> bool:
        """Register a new user or update existing user."""
        async with self.lock:
            user_key = str(user_id)
            
            if user_key not in self.users_data:
                # New user
                self.users_data[user_key] = {
                    'user_id': user_id,
                    'username': username,
                    'first_name': first_name,
                    'registered_at': datetime.now().isoformat(),
                    'last_active': datetime.now().isoformat(),
                    'preferences': {
                        'preferred_sport': None,
                        'notifications_enabled': True,
                        'confidence_threshold': 0.6,
                        'timezone': 'UTC'
                    },
                    'subscriptions': [],
                    'activity_log': [],
                    'stats': {
                        'predictions_requested': 0,
                        'commands_used': 0,
                        'last_prediction': None
                    }
                }
                logger.info(f"Registered new user: {user_id}")
            else:
                # Update existing user
                self.users_data[user_key]['username'] = username
                self.users_data[user_key]['first_name'] = first_name
                self.users_data[user_key]['last_active'] = datetime.now().isoformat()
            
            await self._save_users_data()
            return True
    
    async def get_user_preferences(self, user_id: int) -> Dict[str, Any]:
        """Get user preferences."""
        user_key = str(user_id)
        
        if user_key in self.users_data:
            return self.users_data[user_key].get('preferences', {})
        
        # Return default preferences for new users
        return {
            'preferred_sport': None,
            'notifications_enabled': True,
            'confidence_threshold': 0.6,
            'timezone': 'UTC'
        }
    
    async def update_user_preferences(self, user_id: int, preferences: Dict[str, Any]) -> bool:
        """Update user preferences."""
        async with self.lock:
            user_key = str(user_id)
            
            if user_key not in self.users_data:
                await self.register_user(user_id)
            
            current_prefs = self.users_data[user_key].get('preferences', {})
            current_prefs.update(preferences)
            self.users_data[user_key]['preferences'] = current_prefs
            self.users_data[user_key]['last_active'] = datetime.now().isoformat()
            
            await self._save_users_data()
            return True
    
    async def subscribe_user_to_sport(self, user_id: int, sport: str) -> bool:
        """Subscribe user to sport notifications."""
        async with self.lock:
            user_key = str(user_id)
            
            if user_key not in self.users_data:
                await self.register_user(user_id)
            
            subscriptions = self.users_data[user_key].get('subscriptions', [])
            
            if sport not in subscriptions:
                subscriptions.append(sport)
                self.users_data[user_key]['subscriptions'] = subscriptions
                self.users_data[user_key]['last_active'] = datetime.now().isoformat()
                
                await self._save_users_data()
                logger.info(f"User {user_id} subscribed to {sport}")
                return True
            
            return False  # Already subscribed
    
    async def unsubscribe_user_from_sport(self, user_id: int, sport: str) -> bool:
        """Unsubscribe user from sport notifications."""
        async with self.lock:
            user_key = str(user_id)
            
            if user_key not in self.users_data:
                return False
            
            subscriptions = self.users_data[user_key].get('subscriptions', [])
            
            if sport in subscriptions:
                subscriptions.remove(sport)
                self.users_data[user_key]['subscriptions'] = subscriptions
                self.users_data[user_key]['last_active'] = datetime.now().isoformat()
                
                await self._save_users_data()
                logger.info(f"User {user_id} unsubscribed from {sport}")
                return True
            
            return False  # Not subscribed
    
    async def get_user_subscriptions(self, user_id: int) -> List[str]:
        """Get user's sport subscriptions."""
        user_key = str(user_id)
        
        if user_key in self.users_data:
            return self.users_data[user_key].get('subscriptions', [])
        
        return []
    
    async def get_users_by_sport_subscription(self, sport: str) -> List[Dict[str, Any]]:
        """Get all users subscribed to a specific sport."""
        subscribed_users = []
        
        for user_key, user_data in self.users_data.items():
            subscriptions = user_data.get('subscriptions', [])
            if sport in subscriptions and user_data.get('preferences', {}).get('notifications_enabled', True):
                subscribed_users.append(user_data)
        
        return subscribed_users
    
    async def get_all_subscribed_users(self) -> List[Dict[str, Any]]:
        """Get all users with any subscriptions."""
        subscribed_users = []
        
        for user_key, user_data in self.users_data.items():
            subscriptions = user_data.get('subscriptions', [])
            if subscriptions and user_data.get('preferences', {}).get('notifications_enabled', True):
                subscribed_users.append(user_data)
        
        return subscribed_users
    
    async def log_user_activity(self, user_id: int, activity_type: str, details: Dict[str, Any] = None) -> None:
        """Log user activity."""
        async with self.lock:
            user_key = str(user_id)
            
            if user_key not in self.users_data:
                await self.register_user(user_id)
            
            activity_log = self.users_data[user_key].get('activity_log', [])
            
            activity_entry = {
                'timestamp': datetime.now().isoformat(),
                'type': activity_type,
                'details': details or {}
            }
            
            activity_log.append(activity_entry)
            
            # Keep only last 100 activities
            if len(activity_log) > 100:
                activity_log = activity_log[-100:]
            
            self.users_data[user_key]['activity_log'] = activity_log
            self.users_data[user_key]['last_active'] = datetime.now().isoformat()
            
            # Update stats
            stats = self.users_data[user_key].get('stats', {})
            stats['commands_used'] = stats.get('commands_used', 0) + 1
            
            if activity_type == 'prediction':
                stats['predictions_requested'] = stats.get('predictions_requested', 0) + 1
                stats['last_prediction'] = datetime.now().isoformat()
            
            self.users_data[user_key]['stats'] = stats
            
            # Save periodically (every 10 activities)
            if len(activity_log) % 10 == 0:
                await self._save_users_data()
    
    async def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Get user statistics."""
        user_key = str(user_id)
        
        if user_key in self.users_data:
            return self.users_data[user_key].get('stats', {})
        
        return {}
    
    async def get_user_count(self) -> int:
        """Get total number of users."""
        return len(self.users_data)
    
    async def get_active_user_count(self, days: int = 7) -> int:
        """Get number of active users in the last N days."""
        cutoff_date = datetime.now() - timedelta(days=days)
        active_count = 0
        
        for user_data in self.users_data.values():
            last_active_str = user_data.get('last_active')
            if last_active_str:
                try:
                    last_active = datetime.fromisoformat(last_active_str)
                    if last_active >= cutoff_date:
                        active_count += 1
                except ValueError:
                    pass
        
        return active_count
    
    async def get_sport_subscription_count(self, sport: str) -> int:
        """Get number of users subscribed to a sport."""
        count = 0
        
        for user_data in self.users_data.values():
            subscriptions = user_data.get('subscriptions', [])
            if sport in subscriptions:
                count += 1
        
        return count
    
    async def cleanup_inactive_users(self, days: int = 90) -> int:
        """Remove users inactive for more than N days."""
        cutoff_date = datetime.now() - timedelta(days=days)
        users_to_remove = []
        
        for user_key, user_data in self.users_data.items():
            last_active_str = user_data.get('last_active')
            if last_active_str:
                try:
                    last_active = datetime.fromisoformat(last_active_str)
                    if last_active < cutoff_date:
                        users_to_remove.append(user_key)
                except ValueError:
                    users_to_remove.append(user_key)
            else:
                users_to_remove.append(user_key)
        
        async with self.lock:
            for user_key in users_to_remove:
                del self.users_data[user_key]
            
            if users_to_remove:
                await self._save_users_data()
                logger.info(f"Cleaned up {len(users_to_remove)} inactive users")
        
        return len(users_to_remove)
    
    async def export_user_data(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Export user data (for GDPR compliance)."""
        user_key = str(user_id)
        
        if user_key in self.users_data:
            return self.users_data[user_key].copy()
        
        return None
    
    async def delete_user_data(self, user_id: int) -> bool:
        """Delete user data (for GDPR compliance)."""
        async with self.lock:
            user_key = str(user_id)
            
            if user_key in self.users_data:
                del self.users_data[user_key]
                await self._save_users_data()
                logger.info(f"Deleted data for user {user_id}")
                return True
            
            return False
    
    async def get_user_activity_summary(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Get user activity summary for the last N days."""
        user_key = str(user_id)
        
        if user_key not in self.users_data:
            return {}
        
        activity_log = self.users_data[user_key].get('activity_log', [])
        cutoff_date = datetime.now() - timedelta(days=days)
        
        recent_activities = []
        activity_counts = {}
        
        for activity in activity_log:
            try:
                activity_date = datetime.fromisoformat(activity['timestamp'])
                if activity_date >= cutoff_date:
                    recent_activities.append(activity)
                    
                    activity_type = activity['type']
                    activity_counts[activity_type] = activity_counts.get(activity_type, 0) + 1
            except ValueError:
                pass
        
        return {
            'total_activities': len(recent_activities),
            'activity_breakdown': activity_counts,
            'most_active_day': self._get_most_active_day(recent_activities),
            'recent_activities': recent_activities[-10:]  # Last 10 activities
        }
    
    def _get_most_active_day(self, activities: List[Dict[str, Any]]) -> Optional[str]:
        """Get the most active day from activities."""
        if not activities:
            return None
        
        day_counts = {}
        
        for activity in activities:
            try:
                activity_date = datetime.fromisoformat(activity['timestamp'])
                day = activity_date.strftime('%Y-%m-%d')
                day_counts[day] = day_counts.get(day, 0) + 1
            except ValueError:
                pass
        
        if day_counts:
            return max(day_counts, key=day_counts.get)
        
        return None

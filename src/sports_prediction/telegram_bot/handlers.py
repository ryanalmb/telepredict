"""Telegram bot command and callback handlers."""

import re
from typing import Dict, List, Any, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from ..prediction_engine.predictor import SportsPredictor
from .user_manager import UserManager
from .formatters import MessageFormatter
from ..utils.logger import get_logger
from ..config.settings import settings

logger = get_logger(__name__)


class CommandHandlers:
    """Handles bot commands."""
    
    def __init__(self, predictors: Dict[str, SportsPredictor], 
                 user_manager: UserManager, formatter: MessageFormatter):
        self.predictors = predictors
        self.user_manager = user_manager
        self.formatter = formatter
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command."""
        user = update.effective_user
        chat_id = update.effective_chat.id
        
        # Register user
        await self.user_manager.register_user(user.id, user.username, user.first_name)
        
        welcome_message = self.formatter.format_welcome_message(user.first_name)
        
        # Create sport selection keyboard
        keyboard = self._create_sport_selection_keyboard()
        
        await update.message.reply_text(
            welcome_message,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    
    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /help command."""
        help_message = self.formatter.format_help_message()
        
        await update.message.reply_text(
            help_message,
            parse_mode='HTML'
        )
    
    async def list_sports(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /sports command."""
        keyboard = self._create_sport_selection_keyboard()
        
        await update.message.reply_text(
            "🏆 <b>Available Sports:</b>\n\nSelect a sport to get predictions:",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    
    async def predict(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /predict command."""
        user_id = update.effective_user.id
        
        # Parse command arguments
        args = context.args
        
        if not args:
            await update.message.reply_text(
                "❓ Please specify a sport and teams.\n\n"
                "Usage: /predict <sport> <home_team> vs <away_team>\n"
                "Example: /predict nba lakers vs warriors"
            )
            return
        
        try:
            # Parse sport and teams
            sport = args[0].lower()
            
            if sport not in settings.supported_sports:
                await update.message.reply_text(
                    f"❌ Sport '{sport}' not supported.\n\n"
                    f"Supported sports: {', '.join(settings.supported_sports)}"
                )
                return
            
            # Parse teams (simplified)
            text = ' '.join(args[1:])
            if ' vs ' not in text.lower():
                await update.message.reply_text(
                    "❓ Please use format: <home_team> vs <away_team>\n"
                    "Example: lakers vs warriors"
                )
                return
            
            teams = text.lower().split(' vs ')
            if len(teams) != 2:
                await update.message.reply_text(
                    "❓ Please specify exactly two teams separated by 'vs'"
                )
                return
            
            home_team = teams[0].strip()
            away_team = teams[1].strip()
            
            # Send "typing" indicator
            await context.bot.send_chat_action(
                chat_id=update.effective_chat.id,
                action="typing"
            )
            
            # Get prediction
            predictor = self.predictors.get(sport)
            if not predictor or not predictor.ensemble.is_trained:
                await update.message.reply_text(
                    f"❌ Prediction model for {sport} is not available or not trained."
                )
                return
            
            # For demo purposes, use simplified team IDs
            prediction = await predictor.predict_match(home_team, away_team)
            
            # Format and send prediction
            message = self.formatter.format_prediction(prediction, sport, home_team, away_team)
            
            await update.message.reply_text(
                message,
                parse_mode='HTML'
            )
            
            # Log prediction request
            await self.user_manager.log_user_activity(user_id, 'prediction', {
                'sport': sport,
                'home_team': home_team,
                'away_team': away_team
            })
        
        except Exception as e:
            logger.error(f"Error in predict command: {e}")
            await update.message.reply_text(
                "❌ Sorry, an error occurred while generating the prediction. Please try again."
            )
    
    async def upcoming_matches(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /upcoming command."""
        user_id = update.effective_user.id
        
        # Get user's preferred sport or ask them to select
        user_prefs = await self.user_manager.get_user_preferences(user_id)
        preferred_sport = user_prefs.get('preferred_sport')
        
        if not preferred_sport:
            keyboard = self._create_sport_selection_keyboard(callback_prefix="upcoming_")
            await update.message.reply_text(
                "🗓️ Select a sport to see upcoming matches:",
                reply_markup=keyboard
            )
            return
        
        await self._send_upcoming_matches(update, preferred_sport)
    
    async def _send_upcoming_matches(self, update: Update, sport: str) -> None:
        """Send upcoming matches for a sport."""
        try:
            # Send "typing" indicator
            await update.message.reply_text("🔍 Fetching upcoming matches...")
            
            predictor = self.predictors.get(sport)
            if not predictor:
                await update.message.reply_text(
                    f"❌ Predictor for {sport} is not available."
                )
                return
            
            # Get upcoming matches
            upcoming_matches = await predictor.predict_upcoming_matches(days_ahead=3)
            
            if not upcoming_matches:
                await update.message.reply_text(
                    f"📅 No upcoming matches found for {sport.upper()} in the next 3 days."
                )
                return
            
            # Format and send matches
            message = self.formatter.format_upcoming_matches(sport, upcoming_matches)
            
            await update.message.reply_text(
                message,
                parse_mode='HTML'
            )
        
        except Exception as e:
            logger.error(f"Error fetching upcoming matches: {e}")
            await update.message.reply_text(
                "❌ Error fetching upcoming matches. Please try again."
            )
    
    async def user_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /settings command."""
        user_id = update.effective_user.id
        
        # Get current preferences
        prefs = await self.user_manager.get_user_preferences(user_id)
        
        # Create settings keyboard
        keyboard = self._create_settings_keyboard(prefs)
        
        message = self.formatter.format_user_settings(prefs)
        
        await update.message.reply_text(
            message,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    
    async def subscribe(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /subscribe command."""
        user_id = update.effective_user.id
        args = context.args
        
        if not args:
            keyboard = self._create_sport_selection_keyboard(callback_prefix="subscribe_")
            await update.message.reply_text(
                "📢 Select sports to subscribe to daily predictions:",
                reply_markup=keyboard
            )
            return
        
        sport = args[0].lower()
        
        if sport not in settings.supported_sports:
            await update.message.reply_text(
                f"❌ Sport '{sport}' not supported.\n\n"
                f"Supported sports: {', '.join(settings.supported_sports)}"
            )
            return
        
        success = await self.user_manager.subscribe_user_to_sport(user_id, sport)
        
        if success:
            await update.message.reply_text(
                f"✅ Successfully subscribed to {sport.upper()} daily predictions!"
            )
        else:
            await update.message.reply_text(
                f"❌ Error subscribing to {sport.upper()}. You may already be subscribed."
            )
    
    async def unsubscribe(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /unsubscribe command."""
        user_id = update.effective_user.id
        args = context.args
        
        if not args:
            # Show current subscriptions
            subscriptions = await self.user_manager.get_user_subscriptions(user_id)
            
            if not subscriptions:
                await update.message.reply_text(
                    "📭 You have no active subscriptions."
                )
                return
            
            keyboard = self._create_unsubscribe_keyboard(subscriptions)
            await update.message.reply_text(
                "📭 Select sports to unsubscribe from:",
                reply_markup=keyboard
            )
            return
        
        sport = args[0].lower()
        
        success = await self.user_manager.unsubscribe_user_from_sport(user_id, sport)
        
        if success:
            await update.message.reply_text(
                f"✅ Successfully unsubscribed from {sport.upper()} predictions."
            )
        else:
            await update.message.reply_text(
                f"❌ Error unsubscribing from {sport.upper()}."
            )
    
    async def bot_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /stats command (admin only)."""
        user_id = update.effective_user.id
        
        # Simple admin check (in practice, use proper admin system)
        if user_id not in [123456789]:  # Replace with actual admin IDs
            await update.message.reply_text("❌ Access denied.")
            return
        
        # Get bot stats (would be implemented in the main bot class)
        stats_message = "📊 <b>Bot Statistics</b>\n\n" \
                       "👥 Total Users: N/A\n" \
                       "🔥 Active Users: N/A\n" \
                       "📈 Predictions Made: N/A\n" \
                       "⏱️ Uptime: N/A"
        
        await update.message.reply_text(
            stats_message,
            parse_mode='HTML'
        )
    
    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle text messages."""
        text = update.message.text.lower()
        
        # Simple natural language processing
        if any(word in text for word in ['predict', 'prediction', 'forecast']):
            await update.message.reply_text(
                "🔮 To get a prediction, use:\n"
                "/predict <sport> <home_team> vs <away_team>\n\n"
                "Example: /predict nba lakers vs warriors"
            )
        elif any(word in text for word in ['upcoming', 'matches', 'games']):
            await update.message.reply_text(
                "📅 To see upcoming matches, use:\n/upcoming"
            )
        elif any(word in text for word in ['help', 'commands']):
            await self.help(update, context)
        else:
            await update.message.reply_text(
                "❓ I didn't understand that. Type /help to see available commands."
            )
    
    def _create_sport_selection_keyboard(self, callback_prefix: str = "sport_") -> InlineKeyboardMarkup:
        """Create sport selection keyboard."""
        keyboard = []
        row = []
        
        for i, sport in enumerate(settings.supported_sports):
            sport_name = sport.replace('_', ' ').title()
            row.append(InlineKeyboardButton(
                sport_name, 
                callback_data=f"{callback_prefix}{sport}"
            ))
            
            # Create new row every 2 sports
            if len(row) == 2 or i == len(settings.supported_sports) - 1:
                keyboard.append(row)
                row = []
        
        return InlineKeyboardMarkup(keyboard)
    
    def _create_settings_keyboard(self, prefs: Dict[str, Any]) -> InlineKeyboardMarkup:
        """Create settings keyboard."""
        keyboard = [
            [InlineKeyboardButton("🏆 Preferred Sport", callback_data="setting_sport")],
            [InlineKeyboardButton("📢 Notifications", callback_data="setting_notifications")],
            [InlineKeyboardButton("🎯 Confidence Threshold", callback_data="setting_confidence")],
            [InlineKeyboardButton("❌ Close", callback_data="setting_close")]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    def _create_unsubscribe_keyboard(self, subscriptions: List[str]) -> InlineKeyboardMarkup:
        """Create unsubscribe keyboard."""
        keyboard = []
        
        for sport in subscriptions:
            sport_name = sport.replace('_', ' ').title()
            keyboard.append([InlineKeyboardButton(
                f"❌ {sport_name}", 
                callback_data=f"unsubscribe_{sport}"
            )])
        
        keyboard.append([InlineKeyboardButton("✅ Done", callback_data="unsubscribe_done")])
        
        return InlineKeyboardMarkup(keyboard)


class CallbackHandlers:
    """Handles callback queries from inline keyboards."""
    
    def __init__(self, predictors: Dict[str, SportsPredictor], 
                 user_manager: UserManager, formatter: MessageFormatter):
        self.predictors = predictors
        self.user_manager = user_manager
        self.formatter = formatter
    
    async def handle_sport_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle sport selection callbacks."""
        query = update.callback_query
        await query.answer()
        
        callback_data = query.data
        sport = callback_data.replace("sport_", "")
        
        user_id = update.effective_user.id
        
        # Update user's preferred sport
        await self.user_manager.update_user_preferences(user_id, {'preferred_sport': sport})
        
        # Send sport-specific menu or information
        message = f"🏆 You selected <b>{sport.replace('_', ' ').title()}</b>\n\n" \
                 f"What would you like to do?\n\n" \
                 f"• /predict {sport} <team1> vs <team2> - Get match prediction\n" \
                 f"• /upcoming - See upcoming matches\n" \
                 f"• /subscribe {sport} - Get daily predictions"
        
        await query.edit_message_text(
            message,
            parse_mode='HTML'
        )
    
    async def handle_match_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle match selection callbacks."""
        query = update.callback_query
        await query.answer()
        
        # Parse match data from callback
        callback_data = query.data
        match_id = callback_data.replace("match_", "")
        
        # This would fetch and display detailed match prediction
        await query.edit_message_text(
            f"🔮 Loading prediction for match {match_id}...",
            parse_mode='HTML'
        )
    
    async def handle_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle settings callbacks."""
        query = update.callback_query
        await query.answer()
        
        callback_data = query.data
        setting = callback_data.replace("setting_", "")
        
        if setting == "close":
            await query.edit_message_text("✅ Settings closed.")
        elif setting == "sport":
            keyboard = self._create_sport_preference_keyboard()
            await query.edit_message_text(
                "🏆 Select your preferred sport:",
                reply_markup=keyboard
            )
        elif setting == "notifications":
            # Toggle notifications
            user_id = update.effective_user.id
            prefs = await self.user_manager.get_user_preferences(user_id)
            
            current_notifications = prefs.get('notifications_enabled', True)
            new_notifications = not current_notifications
            
            await self.user_manager.update_user_preferences(
                user_id, 
                {'notifications_enabled': new_notifications}
            )
            
            status = "enabled" if new_notifications else "disabled"
            await query.edit_message_text(
                f"📢 Notifications {status}!"
            )
    
    def _create_sport_preference_keyboard(self) -> InlineKeyboardMarkup:
        """Create sport preference keyboard."""
        keyboard = []
        row = []
        
        for i, sport in enumerate(settings.supported_sports):
            sport_name = sport.replace('_', ' ').title()
            row.append(InlineKeyboardButton(
                sport_name, 
                callback_data=f"pref_sport_{sport}"
            ))
            
            if len(row) == 2 or i == len(settings.supported_sports) - 1:
                keyboard.append(row)
                row = []
        
        keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="setting_back")])
        
        return InlineKeyboardMarkup(keyboard)

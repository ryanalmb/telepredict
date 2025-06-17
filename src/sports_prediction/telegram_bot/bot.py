"""Main Telegram bot class."""

import asyncio
from typing import Dict, List, Any, Optional
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from telegram.error import TelegramError

from .handlers import CommandHandlers, CallbackHandlers
from .user_manager import UserManager
from .formatters import MessageFormatter
from ..prediction_engine.predictor import SportsPredictor
from ..utils.logger import get_logger
from ..config.settings import settings

logger = get_logger(__name__)


class SportsPredictionBot:
    """Main Telegram bot for sports predictions."""
    
    def __init__(self):
        self.token = settings.telegram_bot_token
        self.application = None
        self.predictors = {}
        self.user_manager = UserManager()
        self.formatter = MessageFormatter()
        self.command_handlers = None
        self.callback_handlers = None
        
        # Initialize predictors for supported sports
        for sport in settings.supported_sports:
            self.predictors[sport] = SportsPredictor(sport)
    
    async def initialize(self) -> None:
        """Initialize the bot and handlers."""
        logger.info("Initializing Telegram bot")
        
        # Create application
        self.application = Application.builder().token(self.token).build()
        
        # Initialize handlers
        self.command_handlers = CommandHandlers(self.predictors, self.user_manager, self.formatter)
        self.callback_handlers = CallbackHandlers(self.predictors, self.user_manager, self.formatter)
        
        # Register handlers
        await self._register_handlers()
        
        # Initialize predictors
        for sport, predictor in self.predictors.items():
            try:
                await predictor.__aenter__()
                logger.info(f"Initialized predictor for {sport}")
            except Exception as e:
                logger.error(f"Error initializing predictor for {sport}: {e}")
    
    async def _register_handlers(self) -> None:
        """Register all bot handlers."""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.command_handlers.start))
        self.application.add_handler(CommandHandler("help", self.command_handlers.help))
        self.application.add_handler(CommandHandler("sports", self.command_handlers.list_sports))
        self.application.add_handler(CommandHandler("predict", self.command_handlers.predict))
        self.application.add_handler(CommandHandler("upcoming", self.command_handlers.upcoming_matches))
        self.application.add_handler(CommandHandler("settings", self.command_handlers.user_settings))
        self.application.add_handler(CommandHandler("subscribe", self.command_handlers.subscribe))
        self.application.add_handler(CommandHandler("unsubscribe", self.command_handlers.unsubscribe))
        self.application.add_handler(CommandHandler("stats", self.command_handlers.bot_stats))
        
        # Callback query handlers
        self.application.add_handler(CallbackQueryHandler(
            self.callback_handlers.handle_sport_selection, 
            pattern="^sport_"
        ))
        self.application.add_handler(CallbackQueryHandler(
            self.callback_handlers.handle_match_selection, 
            pattern="^match_"
        ))
        self.application.add_handler(CallbackQueryHandler(
            self.callback_handlers.handle_settings, 
            pattern="^setting_"
        ))
        
        # Message handlers
        self.application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, 
            self.command_handlers.handle_text_message
        ))
        
        # Error handler
        self.application.add_error_handler(self._error_handler)
    
    async def start_polling(self) -> None:
        """Start the bot with polling."""
        logger.info("Starting bot with polling")
        
        try:
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            
            logger.info("Bot is running...")
            
            # Keep the bot running
            while True:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
        except Exception as e:
            logger.error(f"Error running bot: {e}")
        finally:
            await self.stop()
    
    async def start_webhook(self, webhook_url: str, port: int = 8443) -> None:
        """Start the bot with webhook."""
        logger.info(f"Starting bot with webhook: {webhook_url}")
        
        try:
            await self.application.initialize()
            await self.application.start()
            
            # Set webhook
            await self.application.bot.set_webhook(
                url=webhook_url,
                allowed_updates=["message", "callback_query"]
            )
            
            # Start webhook
            await self.application.updater.start_webhook(
                listen="0.0.0.0",
                port=port,
                url_path="webhook",
                webhook_url=webhook_url
            )
            
            logger.info(f"Bot webhook started on port {port}")
            
        except Exception as e:
            logger.error(f"Error starting webhook: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop the bot and cleanup."""
        logger.info("Stopping bot")
        
        try:
            if self.application:
                await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
            
            # Cleanup predictors
            for predictor in self.predictors.values():
                try:
                    await predictor.__aexit__(None, None, None)
                except Exception as e:
                    logger.error(f"Error cleaning up predictor: {e}")
            
            logger.info("Bot stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping bot: {e}")
    
    async def _error_handler(self, update: Update, context) -> None:
        """Handle errors."""
        logger.error(f"Update {update} caused error {context.error}")
        
        # Try to send error message to user
        if update and update.effective_chat:
            try:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="❌ Sorry, an error occurred. Please try again later."
                )
            except TelegramError:
                pass  # Ignore if we can't send the error message
    
    async def send_notification(self, user_id: int, message: str) -> bool:
        """Send notification to a specific user."""
        try:
            await self.application.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode='HTML'
            )
            return True
        except TelegramError as e:
            logger.error(f"Error sending notification to {user_id}: {e}")
            return False
    
    async def broadcast_message(self, message: str, sport: Optional[str] = None) -> Dict[str, int]:
        """Broadcast message to all subscribed users."""
        logger.info(f"Broadcasting message to users (sport: {sport})")
        
        # Get subscribed users
        if sport:
            users = await self.user_manager.get_users_by_sport_subscription(sport)
        else:
            users = await self.user_manager.get_all_subscribed_users()
        
        success_count = 0
        error_count = 0
        
        for user in users:
            try:
                success = await self.send_notification(user['user_id'], message)
                if success:
                    success_count += 1
                else:
                    error_count += 1
            except Exception as e:
                logger.error(f"Error broadcasting to user {user['user_id']}: {e}")
                error_count += 1
        
        return {
            'total_users': len(users),
            'success_count': success_count,
            'error_count': error_count
        }
    
    async def schedule_predictions(self) -> None:
        """Schedule daily predictions for upcoming matches."""
        logger.info("Scheduling daily predictions")
        
        try:
            for sport in settings.supported_sports:
                predictor = self.predictors.get(sport)
                if predictor and predictor.ensemble.is_trained:
                    # Get upcoming matches
                    upcoming_matches = await predictor.predict_upcoming_matches(days_ahead=1)
                    
                    if upcoming_matches:
                        # Format predictions message
                        message = self.formatter.format_daily_predictions(sport, upcoming_matches)
                        
                        # Broadcast to subscribed users
                        await self.broadcast_message(message, sport)
                        
                        logger.info(f"Sent daily predictions for {sport} to subscribed users")
        
        except Exception as e:
            logger.error(f"Error scheduling predictions: {e}")
    
    async def get_bot_stats(self) -> Dict[str, Any]:
        """Get bot statistics."""
        stats = {
            'total_users': await self.user_manager.get_user_count(),
            'active_users': await self.user_manager.get_active_user_count(),
            'subscriptions_by_sport': {},
            'predictions_made': 0,  # Would track this in practice
            'uptime': "N/A"  # Would track this in practice
        }
        
        # Get subscription stats by sport
        for sport in settings.supported_sports:
            count = await self.user_manager.get_sport_subscription_count(sport)
            stats['subscriptions_by_sport'][sport] = count
        
        return stats
    
    def get_bot_info(self) -> Dict[str, Any]:
        """Get bot information."""
        return {
            'bot_username': self.application.bot.username if self.application else None,
            'supported_sports': settings.supported_sports,
            'predictors_initialized': len(self.predictors),
            'webhook_url': settings.telegram_webhook_url
        }

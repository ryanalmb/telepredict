"""Message formatters for Telegram bot."""

from typing import Dict, List, Any, Optional
from datetime import datetime
import numpy as np
from ..utils.logger import get_logger

logger = get_logger(__name__)


class MessageFormatter:
    """Formats messages for Telegram bot."""
    
    def __init__(self):
        self.sport_emojis = {
            'mls': '⚽',
            'premier_league': '⚽',
            'la_liga': '⚽',
            'bundesliga': '⚽',
            'serie_a': '⚽',
            'champions_league': '⚽',
            'nba': '🏀',
            'nfl': '🏈',
            'nhl': '🏒',
            'mlb': '⚾',
            'tennis': '🎾',
            'ufc': '🥊',
            'boxing': '🥊',
            'rugby': '🏉'
        }
        
        self.confidence_emojis = {
            'high': '🟢',
            'medium': '🟡',
            'low': '🔴'
        }
    
    def format_welcome_message(self, user_name: str) -> str:
        """Format welcome message."""
        return f"""
🏆 <b>Welcome to Sports Prediction Bot, {user_name}!</b>

I provide AI-powered predictions for multiple sports using advanced machine learning models.

<b>🎯 What I can do:</b>
• Predict match outcomes with confidence scores
• Analyze team performance and head-to-head records
• Identify betting value opportunities
• Send daily prediction updates

<b>🏅 Supported Sports:</b>
⚽ Soccer (MLS, Premier League, La Liga, etc.)
🏀 Basketball (NBA)
🏈 American Football (NFL)
🏒 Hockey (NHL)
⚾ Baseball (MLB)
🎾 Tennis
🥊 Combat Sports (UFC, Boxing)

<b>🚀 Quick Start:</b>
• /predict nba lakers vs warriors
• /upcoming - See upcoming matches
• /subscribe nba - Get daily predictions
• /help - Full command list

Select a sport below to get started! 👇
"""
    
    def format_help_message(self) -> str:
        """Format help message."""
        return """
<b>🤖 Sports Prediction Bot Commands</b>

<b>🔮 Predictions:</b>
/predict &lt;sport&gt; &lt;team1&gt; vs &lt;team2&gt; - Get match prediction
/upcoming - Show upcoming matches

<b>📢 Subscriptions:</b>
/subscribe &lt;sport&gt; - Subscribe to daily predictions
/unsubscribe &lt;sport&gt; - Unsubscribe from sport
/sports - List all supported sports

<b>⚙️ Settings:</b>
/settings - Manage your preferences

<b>📊 Examples:</b>
• <code>/predict nba lakers vs warriors</code>
• <code>/predict premier_league arsenal vs chelsea</code>
• <code>/subscribe nfl</code>

<b>🏆 Supported Sports:</b>
⚽ mls, premier_league, la_liga, bundesliga, serie_a, champions_league
🏀 nba
🏈 nfl
🏒 nhl
⚾ mlb
🎾 tennis
🥊 ufc, boxing
🏉 rugby

Need help? Just type your question and I'll try to assist! 💬
"""
    
    def format_prediction(self, prediction: Dict[str, Any], sport: str, 
                         home_team: str, away_team: str) -> str:
        """Format match prediction."""
        sport_emoji = self.sport_emojis.get(sport, '🏆')
        
        # Extract prediction data
        final_rec = prediction.get('final_recommendation', {})
        ml_pred = prediction.get('ml_prediction', {})
        
        probabilities = final_rec.get('probabilities', {})
        confidence = final_rec.get('confidence', 0.5)
        recommendation = final_rec.get('recommendation', 'unknown')
        
        # Format confidence
        confidence_level = self._get_confidence_level(confidence)
        confidence_emoji = self.confidence_emojis.get(confidence_level, '🟡')
        
        # Format probabilities
        home_prob = probabilities.get('home_win', 0) * 100
        draw_prob = probabilities.get('draw', 0) * 100
        away_prob = probabilities.get('away_win', 0) * 100
        
        # Create prediction message
        message = f"""
{sport_emoji} <b>{sport.upper()} PREDICTION</b>

🏠 <b>{home_team.title()}</b> vs 🛫 <b>{away_team.title()}</b>

<b>🎯 PREDICTION:</b>
{self._format_recommendation(recommendation, home_team, away_team)}

<b>📊 PROBABILITIES:</b>
🏠 Home Win: <b>{home_prob:.1f}%</b>
🤝 Draw: <b>{draw_prob:.1f}%</b>
🛫 Away Win: <b>{away_prob:.1f}%</b>

<b>🎯 CONFIDENCE:</b>
{confidence_emoji} <b>{confidence_level.title()}</b> ({confidence:.1f})

<b>📈 KEY FACTORS:</b>
"""
        
        # Add key factors
        key_factors = final_rec.get('key_factors', [])
        for i, factor in enumerate(key_factors[:5], 1):
            message += f"{i}. {factor}\n"
        
        # Add risk assessment
        risk = final_rec.get('risk_assessment', 'Medium Risk')
        risk_emoji = '🟢' if 'low' in risk.lower() else ('🟡' if 'medium' in risk.lower() else '🔴')
        message += f"\n<b>⚠️ RISK LEVEL:</b>\n{risk_emoji} {risk}"
        
        # Add betting recommendation if available
        betting_rec = final_rec.get('betting_recommendation', {})
        if betting_rec.get('recommended'):
            message += f"\n\n<b>💰 BETTING INSIGHT:</b>\n"
            message += f"✅ Recommended: {betting_rec.get('bet_type', 'N/A')}\n"
            message += f"📈 Expected Value: {betting_rec.get('expected_value', 0):.1%}\n"
            message += f"💵 Suggested Stake: {betting_rec.get('recommended_stake', 'N/A')}"
        else:
            message += f"\n\n<b>💰 BETTING INSIGHT:</b>\n❌ No value bets identified"
        
        message += f"\n\n<i>⏰ Generated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}</i>"
        
        return message
    
    def format_upcoming_matches(self, sport: str, matches: List[Dict[str, Any]]) -> str:
        """Format upcoming matches."""
        sport_emoji = self.sport_emojis.get(sport, '🏆')
        
        message = f"{sport_emoji} <b>{sport.upper()} - UPCOMING MATCHES</b>\n\n"
        
        if not matches:
            message += "📅 No upcoming matches found in the next few days."
            return message
        
        for i, match in enumerate(matches[:10], 1):  # Limit to 10 matches
            match_info = match.get('match_info', {})
            final_rec = match.get('final_recommendation', {})
            
            home_team = match_info.get('home_team_name', 'Home Team')
            away_team = match_info.get('away_team_name', 'Away Team')
            match_date = match_info.get('match_date', 'TBD')
            venue = match_info.get('venue', 'TBD')
            
            # Format date
            try:
                if match_date != 'TBD':
                    date_obj = datetime.fromisoformat(match_date.replace('Z', '+00:00'))
                    formatted_date = date_obj.strftime('%m/%d %H:%M')
                else:
                    formatted_date = 'TBD'
            except:
                formatted_date = match_date
            
            # Get prediction
            recommendation = final_rec.get('recommendation', 'TBD')
            confidence = final_rec.get('confidence', 0)
            
            confidence_level = self._get_confidence_level(confidence)
            confidence_emoji = self.confidence_emojis.get(confidence_level, '🟡')
            
            message += f"<b>{i}. {home_team} vs {away_team}</b>\n"
            message += f"📅 {formatted_date}\n"
            message += f"🏟️ {venue}\n"
            message += f"🎯 Prediction: <b>{self._format_simple_recommendation(recommendation)}</b>\n"
            message += f"📊 Confidence: {confidence_emoji} {confidence_level.title()}\n\n"
        
        if len(matches) > 10:
            message += f"<i>... and {len(matches) - 10} more matches</i>\n\n"
        
        message += f"<i>Use /predict {sport} &lt;team1&gt; vs &lt;team2&gt; for detailed analysis</i>"
        
        return message
    
    def format_daily_predictions(self, sport: str, predictions: List[Dict[str, Any]]) -> str:
        """Format daily predictions broadcast."""
        sport_emoji = self.sport_emojis.get(sport, '🏆')
        
        message = f"🌅 <b>DAILY {sport.upper()} PREDICTIONS</b> {sport_emoji}\n\n"
        
        if not predictions:
            message += f"📅 No {sport.upper()} matches today."
            return message
        
        message += f"📊 <b>{len(predictions)} matches analyzed</b>\n\n"
        
        for i, prediction in enumerate(predictions[:5], 1):  # Top 5 predictions
            match_info = prediction.get('match_info', {})
            final_rec = prediction.get('final_recommendation', {})
            
            home_team = match_info.get('home_team_name', 'Home')
            away_team = match_info.get('away_team_name', 'Away')
            
            recommendation = final_rec.get('recommendation', 'TBD')
            confidence = final_rec.get('confidence', 0)
            
            confidence_emoji = self.confidence_emojis.get(self._get_confidence_level(confidence), '🟡')
            
            message += f"<b>{i}. {home_team} vs {away_team}</b>\n"
            message += f"🎯 {self._format_simple_recommendation(recommendation)}\n"
            message += f"📊 {confidence_emoji} {confidence:.1f}\n\n"
        
        message += f"💡 <i>Use /predict {sport} for detailed analysis</i>\n"
        message += f"⚙️ <i>Manage subscriptions with /settings</i>"
        
        return message
    
    def format_user_settings(self, preferences: Dict[str, Any]) -> str:
        """Format user settings."""
        preferred_sport = preferences.get('preferred_sport', 'None')
        notifications = preferences.get('notifications_enabled', True)
        confidence_threshold = preferences.get('confidence_threshold', 0.6)
        
        sport_display = preferred_sport.replace('_', ' ').title() if preferred_sport != 'None' else 'None'
        notifications_display = "✅ Enabled" if notifications else "❌ Disabled"
        
        message = f"""
⚙️ <b>YOUR SETTINGS</b>

<b>🏆 Preferred Sport:</b> {sport_display}
<b>📢 Notifications:</b> {notifications_display}
<b>🎯 Confidence Threshold:</b> {confidence_threshold:.1f}

<i>Use the buttons below to modify your settings:</i>
"""
        
        return message
    
    def _format_recommendation(self, recommendation: str, home_team: str, away_team: str) -> str:
        """Format recommendation with team names."""
        if recommendation == 'home_win':
            return f"🏠 <b>{home_team.title()} Win</b>"
        elif recommendation == 'away_win':
            return f"🛫 <b>{away_team.title()} Win</b>"
        elif recommendation == 'draw':
            return f"🤝 <b>Draw</b>"
        else:
            return f"❓ <b>Uncertain</b>"
    
    def _format_simple_recommendation(self, recommendation: str) -> str:
        """Format simple recommendation."""
        if recommendation == 'home_win':
            return "🏠 Home Win"
        elif recommendation == 'away_win':
            return "🛫 Away Win"
        elif recommendation == 'draw':
            return "🤝 Draw"
        else:
            return "❓ Uncertain"
    
    def _get_confidence_level(self, confidence: float) -> str:
        """Get confidence level from score."""
        if confidence >= 0.8:
            return 'high'
        elif confidence >= 0.6:
            return 'medium'
        else:
            return 'low'
    
    def format_error_message(self, error_type: str, details: str = "") -> str:
        """Format error messages."""
        error_messages = {
            'sport_not_supported': "❌ Sport not supported. Use /sports to see available options.",
            'invalid_format': "❓ Invalid format. Use /help for command examples.",
            'prediction_error': "🔧 Prediction service temporarily unavailable. Please try again later.",
            'no_data': "📭 No data available for this request.",
            'rate_limit': "⏱️ Too many requests. Please wait a moment and try again."
        }
        
        base_message = error_messages.get(error_type, "❌ An error occurred.")
        
        if details:
            return f"{base_message}\n\n<i>{details}</i>"
        
        return base_message
    
    def format_subscription_message(self, sport: str, action: str) -> str:
        """Format subscription confirmation."""
        sport_emoji = self.sport_emojis.get(sport, '🏆')
        sport_name = sport.replace('_', ' ').title()
        
        if action == 'subscribe':
            return f"✅ <b>Subscribed to {sport_name}</b> {sport_emoji}\n\n" \
                   f"You'll receive daily predictions and match updates.\n\n" \
                   f"Use /unsubscribe {sport} to stop notifications."
        elif action == 'unsubscribe':
            return f"📭 <b>Unsubscribed from {sport_name}</b>\n\n" \
                   f"You won't receive daily predictions anymore.\n\n" \
                   f"Use /subscribe {sport} to re-enable notifications."
        else:
            return "✅ Subscription updated."

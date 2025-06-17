"""Main CLI interface for sports prediction system."""

import asyncio
import click
import sys
from pathlib import Path
from typing import Optional

from ..config.settings import settings
from ..telegram_bot.bot import SportsPredictionBot
from ..prediction_engine.predictor import SportsPredictor
from ..data_collection.data_manager import DataManager
from ..utils.logger import get_logger

logger = get_logger(__name__)


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """Sports Prediction Bot CLI."""
    pass


@cli.command()
@click.option('--webhook-url', help='Webhook URL for production deployment')
@click.option('--port', default=8443, help='Port for webhook server')
@click.option('--production', is_flag=True, help='Run in production mode')
def run_bot(webhook_url: Optional[str], port: int, production: bool):
    """Run the Telegram bot."""
    click.echo("🤖 Starting Sports Prediction Bot...")
    
    async def start_bot():
        bot = SportsPredictionBot()
        
        try:
            await bot.initialize()
            
            if production and webhook_url:
                click.echo(f"🌐 Starting bot with webhook: {webhook_url}")
                await bot.start_webhook(webhook_url, port)
            else:
                click.echo("🔄 Starting bot with polling...")
                await bot.start_polling()
                
        except KeyboardInterrupt:
            click.echo("\n⏹️ Bot stopped by user")
        except Exception as e:
            click.echo(f"❌ Error running bot: {e}")
            logger.error(f"Bot error: {e}")
        finally:
            await bot.stop()
    
    try:
        asyncio.run(start_bot())
    except KeyboardInterrupt:
        click.echo("\n👋 Goodbye!")


@cli.command()
@click.option('--sport', required=True, help='Sport to collect data for')
@click.option('--days', default=7, help='Number of days to collect data for')
@click.option('--continuous', is_flag=True, help='Run continuous data collection')
def collect_data(sport: str, days: int, continuous: bool):
    """Collect sports data."""
    click.echo(f"📊 Collecting data for {sport}...")
    
    async def collect():
        async with DataManager() as data_manager:
            if continuous:
                click.echo("🔄 Starting continuous data collection...")
                # Implement continuous collection logic
                while True:
                    try:
                        # Collect data for all supported sports
                        for sport_name in settings.supported_sports:
                            click.echo(f"Collecting data for {sport_name}...")
                            data = await data_manager.collect_comprehensive_data(sport_name, [])
                            click.echo(f"✅ Collected {len(data.get('teams', {}))} teams data for {sport_name}")
                        
                        # Wait before next collection
                        await asyncio.sleep(3600)  # 1 hour
                        
                    except Exception as e:
                        logger.error(f"Error in continuous collection: {e}")
                        await asyncio.sleep(300)  # 5 minutes on error
            else:
                # Single collection
                data = await data_manager.collect_comprehensive_data(sport, [])
                click.echo(f"✅ Data collection completed for {sport}")
                click.echo(f"📈 Collected data for {len(data.get('teams', {}))} teams")
    
    try:
        asyncio.run(collect())
    except KeyboardInterrupt:
        click.echo("\n⏹️ Data collection stopped")


@cli.command()
@click.option('--sport', required=True, help='Sport to train models for')
@click.option('--start-date', required=True, help='Start date for training data (YYYY-MM-DD)')
@click.option('--end-date', required=True, help='End date for training data (YYYY-MM-DD)')
@click.option('--schedule', is_flag=True, help='Run scheduled model training')
def train_models(sport: str, start_date: str, end_date: str, schedule: bool):
    """Train prediction models."""
    click.echo(f"🧠 Training models for {sport}...")
    
    async def train():
        async with SportsPredictor(sport) as predictor:
            if schedule:
                click.echo("⏰ Starting scheduled model training...")
                # Implement scheduled training logic
                while True:
                    try:
                        click.echo(f"Training models for {sport}...")
                        results = await predictor.train_models(start_date, end_date)
                        click.echo(f"✅ Training completed: {results['training_samples']} samples")
                        
                        # Wait 24 hours before next training
                        await asyncio.sleep(86400)
                        
                    except Exception as e:
                        logger.error(f"Error in scheduled training: {e}")
                        await asyncio.sleep(3600)  # 1 hour on error
            else:
                # Single training
                results = await predictor.train_models(start_date, end_date)
                click.echo(f"✅ Model training completed for {sport}")
                click.echo(f"📊 Training samples: {results['training_samples']}")
                click.echo(f"📁 Model saved to: {results['model_path']}")
    
    try:
        asyncio.run(train())
    except KeyboardInterrupt:
        click.echo("\n⏹️ Model training stopped")


@cli.command()
@click.option('--sport', required=True, help='Sport to predict')
@click.option('--home-team', required=True, help='Home team name or ID')
@click.option('--away-team', required=True, help='Away team name or ID')
@click.option('--date', help='Match date (YYYY-MM-DD)')
def predict(sport: str, home_team: str, away_team: str, date: Optional[str]):
    """Make a match prediction."""
    click.echo(f"🔮 Predicting {home_team} vs {away_team} ({sport})...")
    
    async def make_prediction():
        async with SportsPredictor(sport) as predictor:
            try:
                prediction = await predictor.predict_match(home_team, away_team, date)
                
                # Display prediction results
                final_rec = prediction.get('final_recommendation', {})
                probabilities = final_rec.get('probabilities', {})
                confidence = final_rec.get('confidence', 0)
                recommendation = final_rec.get('recommendation', 'unknown')
                
                click.echo("\n🎯 PREDICTION RESULTS:")
                click.echo(f"Recommendation: {recommendation}")
                click.echo(f"Confidence: {confidence:.2f}")
                click.echo("\n📊 PROBABILITIES:")
                click.echo(f"Home Win: {probabilities.get('home_win', 0):.1%}")
                click.echo(f"Draw: {probabilities.get('draw', 0):.1%}")
                click.echo(f"Away Win: {probabilities.get('away_win', 0):.1%}")
                
                key_factors = final_rec.get('key_factors', [])
                if key_factors:
                    click.echo("\n📈 KEY FACTORS:")
                    for i, factor in enumerate(key_factors, 1):
                        click.echo(f"{i}. {factor}")
                
            except Exception as e:
                click.echo(f"❌ Prediction failed: {e}")
                logger.error(f"Prediction error: {e}")
    
    try:
        asyncio.run(make_prediction())
    except KeyboardInterrupt:
        click.echo("\n⏹️ Prediction cancelled")


@cli.command()
@click.option('--sport', help='Specific sport to show upcoming matches for')
@click.option('--days', default=7, help='Number of days ahead to look')
def upcoming(sport: Optional[str], days: int):
    """Show upcoming matches."""
    sports_to_check = [sport] if sport else settings.supported_sports
    
    async def show_upcoming():
        for sport_name in sports_to_check:
            click.echo(f"\n🏆 {sport_name.upper()} - Upcoming Matches:")
            
            async with SportsPredictor(sport_name) as predictor:
                try:
                    matches = await predictor.predict_upcoming_matches(days)
                    
                    if not matches:
                        click.echo("📅 No upcoming matches found")
                        continue
                    
                    for i, match in enumerate(matches[:10], 1):
                        match_info = match.get('match_info', {})
                        home_team = match_info.get('home_team_name', 'Home')
                        away_team = match_info.get('away_team_name', 'Away')
                        match_date = match_info.get('match_date', 'TBD')
                        
                        click.echo(f"{i}. {home_team} vs {away_team} - {match_date}")
                
                except Exception as e:
                    click.echo(f"❌ Error fetching matches for {sport_name}: {e}")
    
    try:
        asyncio.run(show_upcoming())
    except KeyboardInterrupt:
        click.echo("\n⏹️ Cancelled")


@cli.command()
def setup():
    """Setup the sports prediction system."""
    click.echo("🔧 Setting up Sports Prediction System...")
    
    # Create necessary directories
    directories = [
        settings.data_dir,
        settings.raw_data_dir,
        settings.processed_data_dir,
        settings.models_dir,
        settings.cache_dir,
        Path("logs")
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        click.echo(f"📁 Created directory: {directory}")
    
    # Check configuration
    click.echo("\n⚙️ Checking configuration...")
    
    required_settings = [
        'telegram_bot_token',
        'supported_sports'
    ]
    
    missing_settings = []
    for setting in required_settings:
        if not getattr(settings, setting, None):
            missing_settings.append(setting)
    
    if missing_settings:
        click.echo("❌ Missing required settings:")
        for setting in missing_settings:
            click.echo(f"  - {setting}")
        click.echo("\nPlease check your .env file or environment variables.")
    else:
        click.echo("✅ Configuration looks good!")
    
    # Test API connections (optional)
    click.echo("\n🔗 Testing API connections...")
    
    if settings.espn_api_key:
        click.echo("✅ ESPN API key configured")
    else:
        click.echo("⚠️ ESPN API key not configured")
    
    if settings.sportradar_api_key:
        click.echo("✅ SportRadar API key configured")
    else:
        click.echo("⚠️ SportRadar API key not configured")
    
    if settings.odds_api_key:
        click.echo("✅ Odds API key configured")
    else:
        click.echo("⚠️ Odds API key not configured")
    
    click.echo("\n🎉 Setup completed!")


@cli.command()
def status():
    """Show system status."""
    click.echo("📊 Sports Prediction System Status\n")
    
    # Check directories
    click.echo("📁 Directories:")
    directories = [
        ("Data", settings.data_dir),
        ("Models", settings.models_dir),
        ("Cache", settings.cache_dir),
        ("Logs", Path("logs"))
    ]
    
    for name, path in directories:
        status = "✅" if path.exists() else "❌"
        click.echo(f"  {status} {name}: {path}")
    
    # Check configuration
    click.echo("\n⚙️ Configuration:")
    config_items = [
        ("Telegram Bot Token", bool(settings.telegram_bot_token)),
        ("ESPN API Key", bool(settings.espn_api_key)),
        ("SportRadar API Key", bool(settings.sportradar_api_key)),
        ("Odds API Key", bool(settings.odds_api_key)),
        ("Redis URL", bool(settings.redis_url)),
    ]
    
    for name, configured in config_items:
        status = "✅" if configured else "❌"
        click.echo(f"  {status} {name}")
    
    # Show supported sports
    click.echo(f"\n🏆 Supported Sports: {', '.join(settings.supported_sports)}")
    
    # Check model files
    click.echo("\n🧠 Trained Models:")
    model_files = list(settings.models_dir.glob("*.joblib"))
    if model_files:
        for model_file in model_files:
            click.echo(f"  ✅ {model_file.name}")
    else:
        click.echo("  ❌ No trained models found")


if __name__ == "__main__":
    cli()

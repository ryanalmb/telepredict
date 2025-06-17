"""FastAPI web server for webhook and health endpoints."""

import asyncio
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any
import logging

from .telegram_bot.bot import SportsPredictionBot
from .config.settings import settings
from .utils.logger import get_logger

logger = get_logger(__name__)

# Global bot instance
bot_instance = None

def create_app() -> FastAPI:
    """Create FastAPI application."""
    app = FastAPI(
        title="Sports Prediction Bot",
        description="Sports prediction system with Telegram bot interface",
        version="1.0.0"
    )
    
    @app.on_event("startup")
    async def startup_event():
        """Initialize bot on startup."""
        global bot_instance
        try:
            bot_instance = SportsPredictionBot()
            await bot_instance.initialize()
            logger.info("Bot initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing bot: {e}")
            raise
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """Cleanup on shutdown."""
        global bot_instance
        if bot_instance:
            try:
                await bot_instance.stop()
                logger.info("Bot stopped successfully")
            except Exception as e:
                logger.error(f"Error stopping bot: {e}")
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint for AWS App Runner."""
        global bot_instance
        
        health_status = {
            "status": "healthy",
            "service": "sports-prediction-bot",
            "version": "1.0.0",
            "bot_initialized": bot_instance is not None,
            "supported_sports": settings.supported_sports
        }
        
        if bot_instance:
            try:
                bot_info = bot_instance.get_bot_info()
                health_status.update({
                    "bot_username": bot_info.get("bot_username"),
                    "predictors_initialized": bot_info.get("predictors_initialized", 0)
                })
            except Exception as e:
                logger.error(f"Error getting bot info: {e}")
                health_status["bot_error"] = str(e)
        
        return JSONResponse(content=health_status)
    
    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "message": "Sports Prediction Bot API",
            "version": "1.0.0",
            "endpoints": {
                "health": "/health",
                "webhook": "/webhook",
                "docs": "/docs"
            }
        }
    
    @app.post("/webhook")
    async def webhook_handler(request: Request):
        """Handle Telegram webhook."""
        global bot_instance
        
        if not bot_instance:
            raise HTTPException(status_code=503, detail="Bot not initialized")
        
        try:
            # Get the raw body
            body = await request.body()
            
            # Process the update
            if bot_instance.application:
                # Parse the update
                import json
                from telegram import Update
                
                update_data = json.loads(body.decode('utf-8'))
                update = Update.de_json(update_data, bot_instance.application.bot)
                
                if update:
                    # Process the update
                    await bot_instance.application.process_update(update)
                    return {"status": "ok"}
                else:
                    logger.warning("Received invalid update")
                    return {"status": "invalid_update"}
            else:
                raise HTTPException(status_code=503, detail="Bot application not ready")
                
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            raise HTTPException(status_code=500, detail=f"Webhook processing error: {str(e)}")
    
    @app.get("/stats")
    async def get_stats():
        """Get bot statistics."""
        global bot_instance
        
        if not bot_instance:
            raise HTTPException(status_code=503, detail="Bot not initialized")
        
        try:
            stats = await bot_instance.get_bot_stats()
            return stats
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            raise HTTPException(status_code=500, detail=f"Stats error: {str(e)}")
    
    return app

async def run_server(host: str = "0.0.0.0", port: int = 8000):
    """Run the FastAPI server."""
    app = create_app()
    
    config = uvicorn.Config(
        app=app,
        host=host,
        port=port,
        log_level="info",
        access_log=True
    )
    
    server = uvicorn.Server(config)
    
    try:
        await server.serve()
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise

def run_server_sync(host: str = "0.0.0.0", port: int = 8000):
    """Run the server synchronously."""
    asyncio.run(run_server(host, port))

if __name__ == "__main__":
    run_server_sync()

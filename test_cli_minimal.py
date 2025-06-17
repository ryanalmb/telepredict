#!/usr/bin/env python3
"""
Minimal CLI test for Sports Prediction Bot.
Tests CLI functionality without heavy dependencies.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

def test_settings_import():
    """Test if settings can be imported."""
    print("🧪 Testing Settings Import...")
    
    try:
        from sports_prediction.config.settings import settings
        print("✅ Settings imported successfully")
        
        # Test some basic settings
        print(f"✅ Supported sports: {len(settings.supported_sports)} sports")
        print(f"✅ Log level: {settings.log_level}")
        print(f"✅ Debug mode: {settings.debug}")
        
        return True
    except Exception as e:
        print(f"❌ Failed to import settings: {e}")
        return False

def test_directory_creation():
    """Test directory creation functionality."""
    print("\n🧪 Testing Directory Creation...")
    
    try:
        from sports_prediction.config.settings import settings
        
        # Test directory properties
        directories = [
            ("Data directory", settings.data_dir),
            ("Models directory", settings.models_dir),
            ("Cache directory", settings.cache_dir),
            ("Raw data directory", settings.raw_data_dir),
            ("Processed data directory", settings.processed_data_dir)
        ]
        
        for name, directory in directories:
            if not directory.exists():
                directory.mkdir(parents=True, exist_ok=True)
                print(f"✅ Created {name}: {directory}")
            else:
                print(f"✅ {name} exists: {directory}")
        
        # Create logs directory
        logs_dir = Path("logs")
        if not logs_dir.exists():
            logs_dir.mkdir(parents=True, exist_ok=True)
            print(f"✅ Created logs directory: {logs_dir}")
        else:
            print(f"✅ Logs directory exists: {logs_dir}")
        
        return True
    except Exception as e:
        print(f"❌ Failed to create directories: {e}")
        return False

def test_configuration_validation():
    """Test configuration validation."""
    print("\n🧪 Testing Configuration Validation...")
    
    try:
        from sports_prediction.config.settings import settings
        
        # Check required settings
        config_items = [
            ("Telegram Bot Token", settings.telegram_bot_token),
            ("ESPN API Key", settings.espn_api_key),
            ("SportRadar API Key", settings.sportradar_api_key),
            ("Odds API Key", settings.odds_api_key),
            ("Redis URL", settings.redis_url),
            ("MongoDB URL", settings.mongodb_url)
        ]
        
        configured_count = 0
        for name, value in config_items:
            if value and value != "your_telegram_bot_token_here":
                print(f"✅ {name}: Configured")
                configured_count += 1
            else:
                print(f"⚠️  {name}: Not configured (using default/placeholder)")
        
        print(f"\n📊 Configuration status: {configured_count}/{len(config_items)} items configured")
        
        # Check supported sports
        if settings.supported_sports:
            print(f"✅ Supported sports configured: {', '.join(settings.supported_sports[:5])}...")
        else:
            print("❌ No supported sports configured")
        
        return True
    except Exception as e:
        print(f"❌ Failed to validate configuration: {e}")
        return False

def test_environment_file():
    """Test environment file."""
    print("\n🧪 Testing Environment File...")
    
    # Check if .env exists
    if Path(".env").exists():
        print("✅ .env file exists")
        
        # Read and check basic structure
        with open(".env", 'r') as f:
            content = f.read()
        
        required_vars = [
            "TELEGRAM_BOT_TOKEN",
            "LOG_LEVEL",
            "DEBUG"
        ]
        
        for var in required_vars:
            if var in content:
                print(f"✅ Environment variable: {var}")
            else:
                print(f"⚠️  Missing environment variable: {var}")
    else:
        print("⚠️  .env file not found")
        
        # Check if .env.example exists
        if Path(".env.example").exists():
            print("ℹ️  .env.example found - you can copy it to .env")
        else:
            print("❌ .env.example also missing")
    
    return True

def test_basic_cli_structure():
    """Test basic CLI structure without importing heavy dependencies."""
    print("\n🧪 Testing CLI Structure...")
    
    # Check if CLI files exist
    cli_files = [
        "src/sports_prediction/cli/__init__.py",
        "src/sports_prediction/cli/main.py"
    ]
    
    for cli_file in cli_files:
        if Path(cli_file).exists():
            print(f"✅ CLI file exists: {cli_file}")
        else:
            print(f"❌ Missing CLI file: {cli_file}")
            return False
    
    # Check if main.py has the expected structure
    with open("src/sports_prediction/cli/main.py", 'r') as f:
        content = f.read()
    
    expected_commands = ["run-bot", "collect-data", "train-models", "predict", "setup", "status"]
    for command in expected_commands:
        if command in content:
            print(f"✅ CLI command found: {command}")
        else:
            print(f"⚠️  CLI command not found: {command}")
    
    return True

def run_minimal_tests():
    """Run minimal tests."""
    print("="*60)
    print("🧪 Sports Prediction Bot - Minimal CLI Test")
    print("="*60)
    
    tests = [
        ("Settings Import", test_settings_import),
        ("Directory Creation", test_directory_creation),
        ("Configuration Validation", test_configuration_validation),
        ("Environment File", test_environment_file),
        ("CLI Structure", test_basic_cli_structure)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ Test {test_name} failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "="*60)
    print("🧪 Test Results Summary")
    print("="*60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status} {test_name}")
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✅ 🎉 All minimal tests passed!")
        print("\nℹ️  Core functionality is working. Next steps:")
        print("ℹ️  1. Install full dependencies: pip install -r requirements.txt")
        print("ℹ️  2. Configure real API keys in .env file")
        print("ℹ️  3. Test full CLI: python -m src.sports_prediction.cli --help")
        print("ℹ️  4. Deploy infrastructure: infrastructure/deploy.bat dev us-east-1")
        return True
    else:
        print(f"\n❌ {total - passed} test(s) failed")
        print("ℹ️  Please fix the issues above before proceeding")
        return False

if __name__ == "__main__":
    success = run_minimal_tests()
    sys.exit(0 if success else 1)

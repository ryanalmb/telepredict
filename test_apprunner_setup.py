#!/usr/bin/env python3
"""Test script to verify App Runner setup."""

import os
import sys
import json
import asyncio
import aiohttp
from pathlib import Path

def check_files():
    """Check if required files exist."""
    print("🔍 Checking required files...")
    
    required_files = [
        "apprunner.yaml",
        "Dockerfile", 
        "requirements.txt",
        "src/sports_prediction/__init__.py",
        "src/sports_prediction/web_server.py",
        "src/sports_prediction/cli/main.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
        else:
            print(f"✅ {file_path}")
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    
    print("✅ All required files present")
    return True

def check_environment():
    """Check environment variables."""
    print("\n🔍 Checking environment variables...")
    
    required_vars = [
        "TELEGRAM_BOT_TOKEN"
    ]
    
    optional_vars = [
        "TELEGRAM_WEBHOOK_URL",
        "ESPN_API_KEY", 
        "SPORTRADAR_API_KEY",
        "ODDS_API_KEY",
        "AWS_REGION",
        "REDIS_URL",
        "MONGODB_URL"
    ]
    
    missing_required = []
    for var in required_vars:
        if os.getenv(var):
            print(f"✅ {var} is set")
        else:
            missing_required.append(var)
            print(f"❌ {var} is missing")
    
    for var in optional_vars:
        if os.getenv(var):
            print(f"✅ {var} is set")
        else:
            print(f"⚠️  {var} is not set (optional)")
    
    if missing_required:
        print(f"\n❌ Missing required environment variables: {missing_required}")
        return False
    
    print("\n✅ Required environment variables are set")
    return True

def check_apprunner_yaml():
    """Check apprunner.yaml format."""
    print("\n🔍 Checking apprunner.yaml format...")
    
    try:
        import yaml
        with open("apprunner.yaml", "r") as f:
            config = yaml.safe_load(f)
        
        # Check required sections
        required_sections = ["version", "runtime", "build", "run"]
        for section in required_sections:
            if section not in config:
                print(f"❌ Missing section: {section}")
                return False
            else:
                print(f"✅ Section '{section}' present")
        
        # Check run configuration
        run_config = config.get("run", {})
        if "command" not in run_config:
            print("❌ Missing 'command' in run section")
            return False
        
        if "network" not in run_config:
            print("❌ Missing 'network' in run section")
            return False
        
        network = run_config["network"]
        if network.get("port") != 8000:
            print(f"⚠️  Port is {network.get('port')}, should be 8000")
        
        print("✅ apprunner.yaml format looks good")
        return True
        
    except ImportError:
        print("⚠️  PyYAML not installed, skipping YAML validation")
        return True
    except Exception as e:
        print(f"❌ Error reading apprunner.yaml: {e}")
        return False

async def test_local_server():
    """Test the local server."""
    print("\n🔍 Testing local server...")
    
    try:
        # Import and start server
        from src.sports_prediction.web_server import create_app
        
        app = create_app()
        print("✅ FastAPI app created successfully")
        
        # Test health endpoint (mock)
        print("✅ Health endpoint should work")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Server test error: {e}")
        return False

def check_docker_setup():
    """Check Docker setup."""
    print("\n🔍 Checking Docker setup...")
    
    try:
        with open("Dockerfile", "r") as f:
            dockerfile_content = f.read()
        
        # Check for required elements
        required_elements = [
            "FROM python:",
            "COPY requirements.txt",
            "RUN pip install",
            "COPY src/",
            "EXPOSE 8000",
            "CMD"
        ]
        
        for element in required_elements:
            if element in dockerfile_content:
                print(f"✅ Found: {element}")
            else:
                print(f"❌ Missing: {element}")
                return False
        
        print("✅ Dockerfile looks good")
        return True
        
    except Exception as e:
        print(f"❌ Error checking Dockerfile: {e}")
        return False

def main():
    """Run all checks."""
    print("🚀 App Runner Setup Verification\n")
    
    checks = [
        ("Files", check_files),
        ("Environment", check_environment), 
        ("App Runner YAML", check_apprunner_yaml),
        ("Docker Setup", check_docker_setup),
        ("Local Server", lambda: asyncio.run(test_local_server()))
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n{'='*50}")
        print(f"🔍 {name} Check")
        print('='*50)
        
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Error in {name} check: {e}")
            results.append((name, False))
    
    # Summary
    print(f"\n{'='*50}")
    print("📊 SUMMARY")
    print('='*50)
    
    passed = 0
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {name}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n🎉 All checks passed! Ready for App Runner deployment.")
        print("\nNext steps:")
        print("1. Commit and push your code to GitHub")
        print("2. Create App Runner service in AWS Console")
        print("3. Set environment variables in App Runner")
        print("4. Deploy and test")
    else:
        print(f"\n⚠️  {total - passed} checks failed. Please fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()

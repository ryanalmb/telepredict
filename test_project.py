#!/usr/bin/env python3
"""
Comprehensive test script for Sports Prediction Bot project.
This script tests the entire project without requiring external APIs or services.
"""

import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path
import json
import time

def print_header(title):
    """Print a formatted header."""
    print(f"\n{'='*60}")
    print(f"🧪 {title}")
    print(f"{'='*60}")

def print_test(test_name):
    """Print test name."""
    print(f"\n📋 Test: {test_name}")
    print("-" * 40)

def print_success(message):
    """Print success message."""
    print(f"✅ {message}")

def print_warning(message):
    """Print warning message."""
    print(f"⚠️  {message}")

def print_error(message):
    """Print error message."""
    print(f"❌ {message}")

def print_info(message):
    """Print info message."""
    print(f"ℹ️  {message}")

def test_python_environment():
    """Test Python environment and version."""
    print_test("Python Environment")
    
    # Check Python version
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print_success(f"Python {version.major}.{version.minor}.{version.micro} is supported")
    else:
        print_error(f"Python {version.major}.{version.minor}.{version.micro} is not supported (requires 3.8+)")
        return False
    
    # Check if pip is available
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"], 
                      check=True, capture_output=True)
        print_success("pip is available")
    except subprocess.CalledProcessError:
        print_error("pip is not available")
        return False
    
    return True

def test_project_structure():
    """Test project file structure."""
    print_test("Project Structure")
    
    required_files = [
        "requirements.txt",
        "pyproject.toml",
        "README.md",
        "Dockerfile",
        "docker-compose.yml",
        ".env.example",
        "src/sports_prediction/__init__.py",
        "src/sports_prediction/cli/main.py",
        "src/sports_prediction/config/settings.py",
        "infrastructure/infrastructure.yaml"
    ]
    
    required_dirs = [
        "src/sports_prediction",
        "src/sports_prediction/cli",
        "src/sports_prediction/config",
        "src/sports_prediction/data_collection",
        "src/sports_prediction/ml_models",
        "src/sports_prediction/prediction_engine",
        "src/sports_prediction/telegram_bot",
        "src/sports_prediction/utils",
        "tests",
        "infrastructure",
        "data",
        "models",
        "logs"
    ]
    
    all_good = True
    
    # Check files
    for file_path in required_files:
        if Path(file_path).exists():
            print_success(f"File exists: {file_path}")
        else:
            print_error(f"Missing file: {file_path}")
            all_good = False
    
    # Check directories
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print_success(f"Directory exists: {dir_path}")
        else:
            print_warning(f"Directory missing (will be created): {dir_path}")
    
    return all_good

def test_dependencies():
    """Test if core dependencies can be imported."""
    print_test("Core Dependencies")
    
    core_deps = [
        ("click", "CLI framework"),
        ("pydantic", "Data validation"),
        ("pathlib", "Path handling"),
        ("asyncio", "Async support"),
        ("json", "JSON handling"),
        ("os", "OS interface"),
        ("sys", "System interface")
    ]
    
    all_good = True
    
    for module, description in core_deps:
        try:
            __import__(module)
            print_success(f"{module} - {description}")
        except ImportError:
            print_error(f"Cannot import {module} - {description}")
            all_good = False
    
    return all_good

def test_configuration():
    """Test configuration loading."""
    print_test("Configuration")
    
    # Create a temporary .env file for testing
    env_content = """
TELEGRAM_BOT_TOKEN=test_token_123
ESPN_API_KEY=test_espn_key
SPORTRADAR_API_KEY=test_sportradar_key
ODDS_API_KEY=test_odds_key
REDIS_URL=redis://localhost:6379
MONGODB_URL=mongodb://localhost:27017/test
LOG_LEVEL=INFO
DEBUG=True
TESTING=True
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write(env_content)
        env_file = f.name
    
    try:
        # Test if we can load the configuration
        os.environ['ENV_FILE'] = env_file
        
        # Try to import settings
        sys.path.insert(0, 'src')
        try:
            from sports_prediction.config.settings import settings
            print_success("Configuration module loaded successfully")
            
            # Test some settings
            if hasattr(settings, 'supported_sports'):
                print_success(f"Supported sports: {', '.join(settings.supported_sports)}")
            else:
                print_warning("Supported sports not configured")
            
            return True
            
        except ImportError as e:
            print_error(f"Cannot import settings: {e}")
            return False
        except Exception as e:
            print_error(f"Configuration error: {e}")
            return False
    
    finally:
        # Cleanup
        os.unlink(env_file)
        if 'ENV_FILE' in os.environ:
            del os.environ['ENV_FILE']

def test_cli_interface():
    """Test CLI interface."""
    print_test("CLI Interface")
    
    try:
        # Test if CLI module can be imported
        sys.path.insert(0, 'src')
        from sports_prediction.cli.main import cli
        print_success("CLI module imported successfully")
        
        # Test CLI help
        from click.testing import CliRunner
        runner = CliRunner()
        result = runner.invoke(cli, ['--help'])
        
        if result.exit_code == 0:
            print_success("CLI help command works")
            print_info("Available commands found in help output")
        else:
            print_error(f"CLI help failed: {result.output}")
            return False
        
        # Test setup command (dry run)
        result = runner.invoke(cli, ['setup'])
        if result.exit_code == 0:
            print_success("CLI setup command works")
        else:
            print_warning(f"CLI setup had issues: {result.output}")
        
        return True
        
    except ImportError as e:
        print_error(f"Cannot import CLI: {e}")
        return False
    except Exception as e:
        print_error(f"CLI test error: {e}")
        return False

def test_docker_configuration():
    """Test Docker configuration."""
    print_test("Docker Configuration")
    
    # Check Dockerfile
    if Path("Dockerfile").exists():
        print_success("Dockerfile exists")
        
        # Read and validate basic Dockerfile structure
        with open("Dockerfile", 'r') as f:
            content = f.read()
            
        if "FROM python:" in content:
            print_success("Dockerfile has Python base image")
        else:
            print_warning("Dockerfile doesn't use Python base image")
        
        if "COPY requirements.txt" in content:
            print_success("Dockerfile copies requirements.txt")
        else:
            print_warning("Dockerfile doesn't copy requirements.txt")
    else:
        print_error("Dockerfile missing")
        return False
    
    # Check docker-compose files
    compose_files = ["docker-compose.yml", "docker-compose.dev.yml", "docker-compose.prod.yml"]
    for compose_file in compose_files:
        if Path(compose_file).exists():
            print_success(f"{compose_file} exists")
        else:
            print_warning(f"{compose_file} missing")
    
    return True

def test_infrastructure():
    """Test infrastructure configuration."""
    print_test("Infrastructure Configuration")
    
    # Test CloudFormation template
    cf_template = Path("infrastructure/infrastructure.yaml")
    if cf_template.exists():
        print_success("CloudFormation template exists")
        
        # Basic YAML structure check
        try:
            with open(cf_template, 'r') as f:
                content = f.read()
            
            required_sections = ["AWSTemplateFormatVersion", "Parameters", "Resources", "Outputs"]
            for section in required_sections:
                if section in content:
                    print_success(f"CloudFormation template has {section} section")
                else:
                    print_error(f"CloudFormation template missing {section} section")
        except Exception as e:
            print_error(f"Error reading CloudFormation template: {e}")
    else:
        print_error("CloudFormation template missing")
        return False
    
    # Test parameter files
    param_files = ["dev.json", "staging.json", "prod.json"]
    for param_file in param_files:
        param_path = Path(f"infrastructure/parameters/{param_file}")
        if param_path.exists():
            print_success(f"Parameter file {param_file} exists")
            
            # Validate JSON
            try:
                with open(param_path, 'r') as f:
                    json.load(f)
                print_success(f"Parameter file {param_file} is valid JSON")
            except json.JSONDecodeError as e:
                print_error(f"Parameter file {param_file} has invalid JSON: {e}")
        else:
            print_error(f"Parameter file {param_file} missing")
    
    return True

def test_project_setup():
    """Test project setup functionality."""
    print_test("Project Setup")
    
    try:
        # Create necessary directories
        directories = ["data", "data/cache", "data/raw", "data/processed", "models", "logs"]
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
            print_success(f"Directory created/verified: {directory}")
        
        # Test if we can create a simple .env file
        if not Path(".env").exists():
            shutil.copy(".env.example", ".env")
            print_success("Created .env file from template")
        else:
            print_info(".env file already exists")
        
        return True
        
    except Exception as e:
        print_error(f"Setup error: {e}")
        return False

def run_comprehensive_test():
    """Run all tests."""
    print_header("Sports Prediction Bot - Comprehensive Test Suite")
    
    tests = [
        ("Python Environment", test_python_environment),
        ("Project Structure", test_project_structure),
        ("Core Dependencies", test_dependencies),
        ("Configuration", test_configuration),
        ("CLI Interface", test_cli_interface),
        ("Docker Configuration", test_docker_configuration),
        ("Infrastructure", test_infrastructure),
        ("Project Setup", test_project_setup)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print_error(f"Test {test_name} failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print_header("Test Results Summary")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status} {test_name}")
    
    print(f"\n📊 Overall Results: {passed}/{total} tests passed")
    
    if passed == total:
        print_success("🎉 All tests passed! Project is ready for development.")
        return True
    else:
        print_warning(f"⚠️  {total - passed} test(s) failed. Please review the issues above.")
        return False

if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)

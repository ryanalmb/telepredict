#!/usr/bin/env python3
"""
Basic test script for Sports Prediction Bot project.
Tests core functionality without requiring heavy dependencies.
"""

import os
import sys
import json
from pathlib import Path

def print_header(title):
    """Print a formatted header."""
    print(f"\n{'='*50}")
    print(f"🧪 {title}")
    print(f"{'='*50}")

def print_test(test_name):
    """Print test name."""
    print(f"\n📋 {test_name}")
    print("-" * 30)

def print_success(message):
    """Print success message."""
    print(f"✅ {message}")

def print_error(message):
    """Print error message."""
    print(f"❌ {message}")

def print_info(message):
    """Print info message."""
    print(f"ℹ️  {message}")

def test_project_structure():
    """Test basic project structure."""
    print_test("Project Structure")
    
    required_files = [
        "requirements.txt",
        "README.md",
        "Dockerfile",
        "docker-compose.yml",
        ".env.example",
        "src/sports_prediction/__init__.py",
        "src/sports_prediction/cli/main.py",
        "src/sports_prediction/config/settings.py",
        "infrastructure/infrastructure.yaml"
    ]
    
    all_good = True
    for file_path in required_files:
        if Path(file_path).exists():
            print_success(f"Found: {file_path}")
        else:
            print_error(f"Missing: {file_path}")
            all_good = False
    
    return all_good

def test_configuration_file():
    """Test configuration files."""
    print_test("Configuration Files")
    
    # Test .env.example
    if Path(".env.example").exists():
        print_success(".env.example exists")
        
        with open(".env.example", 'r') as f:
            content = f.read()
        
        required_vars = [
            "TELEGRAM_BOT_TOKEN",
            "ESPN_API_KEY", 
            "SPORTRADAR_API_KEY",
            "ODDS_API_KEY"
        ]
        
        for var in required_vars:
            if var in content:
                print_success(f"Environment variable template: {var}")
            else:
                print_error(f"Missing environment variable: {var}")
    else:
        print_error(".env.example missing")
        return False
    
    return True

def test_infrastructure_files():
    """Test infrastructure configuration."""
    print_test("Infrastructure Files")
    
    # Test CloudFormation template
    cf_template = Path("infrastructure/infrastructure.yaml")
    if cf_template.exists():
        print_success("CloudFormation template exists")
        
        with open(cf_template, 'r') as f:
            content = f.read()
        
        required_sections = [
            "AWSTemplateFormatVersion",
            "Parameters", 
            "Resources",
            "Outputs"
        ]
        
        for section in required_sections:
            if section in content:
                print_success(f"CloudFormation section: {section}")
            else:
                print_error(f"Missing CloudFormation section: {section}")
    else:
        print_error("CloudFormation template missing")
        return False
    
    # Test parameter files
    param_files = ["dev.json", "staging.json", "prod.json"]
    for param_file in param_files:
        param_path = Path(f"infrastructure/parameters/{param_file}")
        if param_path.exists():
            print_success(f"Parameter file: {param_file}")
            
            try:
                with open(param_path, 'r') as f:
                    data = json.load(f)
                print_success(f"Valid JSON: {param_file}")
            except json.JSONDecodeError:
                print_error(f"Invalid JSON: {param_file}")
        else:
            print_error(f"Missing parameter file: {param_file}")
    
    return True

def test_docker_files():
    """Test Docker configuration."""
    print_test("Docker Configuration")
    
    # Test Dockerfile
    if Path("Dockerfile").exists():
        print_success("Dockerfile exists")
        
        with open("Dockerfile", 'r') as f:
            content = f.read()
        
        if "FROM python:" in content:
            print_success("Dockerfile uses Python base image")
        else:
            print_error("Dockerfile doesn't use Python base image")
        
        if "requirements.txt" in content:
            print_success("Dockerfile installs requirements")
        else:
            print_error("Dockerfile doesn't install requirements")
    else:
        print_error("Dockerfile missing")
        return False
    
    # Test docker-compose files
    compose_files = [
        "docker-compose.yml",
        "docker-compose.dev.yml", 
        "docker-compose.prod.yml"
    ]
    
    for compose_file in compose_files:
        if Path(compose_file).exists():
            print_success(f"Docker Compose file: {compose_file}")
        else:
            print_error(f"Missing Docker Compose file: {compose_file}")
    
    return True

def test_python_modules():
    """Test Python module structure."""
    print_test("Python Module Structure")
    
    modules = [
        "src/sports_prediction/__init__.py",
        "src/sports_prediction/cli/__init__.py",
        "src/sports_prediction/config/__init__.py",
        "src/sports_prediction/data_collection/__init__.py",
        "src/sports_prediction/ml_models/__init__.py",
        "src/sports_prediction/prediction_engine/__init__.py",
        "src/sports_prediction/telegram_bot/__init__.py",
        "src/sports_prediction/utils/__init__.py"
    ]
    
    all_good = True
    for module in modules:
        if Path(module).exists():
            print_success(f"Module: {module}")
        else:
            print_error(f"Missing module: {module}")
            all_good = False
    
    return all_good

def test_requirements():
    """Test requirements.txt."""
    print_test("Requirements File")
    
    if not Path("requirements.txt").exists():
        print_error("requirements.txt missing")
        return False
    
    with open("requirements.txt", 'r') as f:
        content = f.read()
    
    # Check for key dependencies
    key_deps = [
        "python-telegram-bot",
        "pydantic",
        "click",
        "fastapi",
        "torch",
        "tensorflow",
        "scikit-learn"
    ]
    
    for dep in key_deps:
        if dep in content:
            print_success(f"Dependency: {dep}")
        else:
            print_error(f"Missing dependency: {dep}")
    
    return True

def test_directory_structure():
    """Test directory structure."""
    print_test("Directory Structure")
    
    # Create directories if they don't exist
    directories = [
        "data",
        "data/cache", 
        "data/raw",
        "data/processed",
        "models",
        "logs"
    ]
    
    for directory in directories:
        dir_path = Path(directory)
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print_success(f"Created directory: {directory}")
        else:
            print_success(f"Directory exists: {directory}")
    
    return True

def test_makefile():
    """Test Makefile."""
    print_test("Makefile")
    
    if Path("Makefile").exists():
        print_success("Makefile exists")
        
        with open("Makefile", 'r') as f:
            content = f.read()
        
        # Check for key targets
        targets = [
            "install",
            "test", 
            "run",
            "docker-build",
            "infra-deploy"
        ]
        
        for target in targets:
            if f"{target}:" in content:
                print_success(f"Makefile target: {target}")
            else:
                print_error(f"Missing Makefile target: {target}")
    else:
        print_error("Makefile missing")
        return False
    
    return True

def run_basic_tests():
    """Run all basic tests."""
    print_header("Sports Prediction Bot - Basic Test Suite")
    
    tests = [
        ("Project Structure", test_project_structure),
        ("Configuration Files", test_configuration_file),
        ("Infrastructure Files", test_infrastructure_files),
        ("Docker Configuration", test_docker_files),
        ("Python Modules", test_python_modules),
        ("Requirements", test_requirements),
        ("Directory Structure", test_directory_structure),
        ("Makefile", test_makefile)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print_error(f"Test {test_name} failed: {e}")
            results[test_name] = False
    
    # Summary
    print_header("Test Results Summary")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status} {test_name}")
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print_success("🎉 All basic tests passed!")
        print_info("Project structure is ready for development.")
        print_info("Next steps:")
        print_info("1. Install dependencies: pip install -r requirements.txt")
        print_info("2. Configure .env file with real API keys")
        print_info("3. Run setup: python -m src.sports_prediction.cli setup")
        print_info("4. Test CLI: python -m src.sports_prediction.cli --help")
        return True
    else:
        print_error(f"❌ {total - passed} test(s) failed")
        return False

if __name__ == "__main__":
    success = run_basic_tests()
    sys.exit(0 if success else 1)

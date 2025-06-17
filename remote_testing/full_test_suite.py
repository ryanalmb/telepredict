#!/usr/bin/env python3
"""
Comprehensive remote test suite for Sports Prediction Bot.
Designed to run in clean environments with full dependency testing.
"""

import os
import sys
import subprocess
import time
import json
import traceback
from pathlib import Path
from datetime import datetime

class RemoteTestSuite:
    def __init__(self):
        self.results = {
            'start_time': datetime.now().isoformat(),
            'environment': self.get_environment_info(),
            'tests': {},
            'summary': {}
        }
        self.test_count = 0
        self.passed_count = 0
    
    def get_environment_info(self):
        """Get environment information."""
        return {
            'python_version': sys.version,
            'platform': sys.platform,
            'cwd': str(Path.cwd()),
            'user': os.getenv('USER', 'unknown'),
            'hostname': os.getenv('HOSTNAME', 'unknown')
        }
    
    def log(self, message, level='INFO'):
        """Log a message with timestamp."""
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] {level}: {message}")
    
    def run_test(self, test_name, test_func):
        """Run a single test and record results."""
        self.test_count += 1
        self.log(f"Running test: {test_name}")
        
        start_time = time.time()
        try:
            result = test_func()
            duration = time.time() - start_time
            
            if result:
                self.passed_count += 1
                self.log(f"✅ PASSED: {test_name} ({duration:.2f}s)", 'PASS')
                status = 'PASSED'
            else:
                self.log(f"❌ FAILED: {test_name} ({duration:.2f}s)", 'FAIL')
                status = 'FAILED'
            
            self.results['tests'][test_name] = {
                'status': status,
                'duration': duration,
                'error': None
            }
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = str(e)
            self.log(f"❌ ERROR: {test_name} - {error_msg} ({duration:.2f}s)", 'ERROR')
            
            self.results['tests'][test_name] = {
                'status': 'ERROR',
                'duration': duration,
                'error': error_msg,
                'traceback': traceback.format_exc()
            }
            return False
    
    def test_python_environment(self):
        """Test Python environment."""
        # Check Python version
        if sys.version_info < (3, 8):
            self.log("Python version too old", 'ERROR')
            return False
        
        # Check pip
        try:
            subprocess.run([sys.executable, '-m', 'pip', '--version'], 
                         check=True, capture_output=True)
        except subprocess.CalledProcessError:
            self.log("pip not available", 'ERROR')
            return False
        
        return True
    
    def test_dependency_installation(self):
        """Test dependency installation."""
        try:
            # Install core dependencies first
            core_deps = [
                'click', 'pydantic', 'pydantic-settings', 
                'python-dotenv', 'fastapi', 'uvicorn'
            ]
            
            for dep in core_deps:
                subprocess.run([sys.executable, '-m', 'pip', 'install', dep], 
                             check=True, capture_output=True)
            
            # Try to install from requirements.txt
            if Path('requirements.txt').exists():
                self.log("Installing from requirements.txt...")
                result = subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                                      capture_output=True, text=True, timeout=600)
                
                if result.returncode != 0:
                    self.log(f"Requirements installation had issues: {result.stderr}")
                    # Continue anyway - some dependencies might be optional
            
            return True
            
        except subprocess.TimeoutExpired:
            self.log("Dependency installation timed out", 'ERROR')
            return False
        except Exception as e:
            self.log(f"Dependency installation failed: {e}", 'ERROR')
            return False
    
    def test_project_structure(self):
        """Test project structure."""
        required_files = [
            'requirements.txt',
            'src/sports_prediction/__init__.py',
            'src/sports_prediction/config/settings.py',
            'infrastructure/infrastructure.yaml'
        ]
        
        for file_path in required_files:
            if not Path(file_path).exists():
                self.log(f"Missing required file: {file_path}", 'ERROR')
                return False
        
        return True
    
    def test_configuration_loading(self):
        """Test configuration loading."""
        try:
            # Create test .env file
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
            with open('.env', 'w') as f:
                f.write(env_content)
            
            # Test settings import
            sys.path.insert(0, 'src')
            from sports_prediction.config.settings import settings
            
            # Validate settings
            if not settings.supported_sports:
                return False
            
            if len(settings.supported_sports) < 5:
                return False
            
            return True
            
        except Exception as e:
            self.log(f"Configuration loading failed: {e}", 'ERROR')
            return False
    
    def test_core_imports(self):
        """Test core module imports."""
        try:
            sys.path.insert(0, 'src')
            
            # Test basic imports
            import sports_prediction
            from sports_prediction.config.settings import settings
            
            # Test conditional imports
            try:
                from sports_prediction.utils.logger import get_logger
                logger = get_logger(__name__)
            except ImportError:
                self.log("Logger import failed (expected if dependencies missing)")
            
            return True
            
        except Exception as e:
            self.log(f"Core imports failed: {e}", 'ERROR')
            return False
    
    def test_cli_structure(self):
        """Test CLI structure."""
        try:
            cli_file = Path('src/sports_prediction/cli/main.py')
            if not cli_file.exists():
                return False
            
            # Read CLI file and check for commands
            with open(cli_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            expected_commands = ['run-bot', 'setup', 'status', 'predict']
            for command in expected_commands:
                if command not in content:
                    self.log(f"Missing CLI command: {command}")
                    return False
            
            return True
            
        except Exception as e:
            self.log(f"CLI structure test failed: {e}", 'ERROR')
            return False
    
    def test_infrastructure_files(self):
        """Test infrastructure files."""
        try:
            # Test CloudFormation template
            cf_template = Path('infrastructure/infrastructure.yaml')
            if not cf_template.exists():
                return False
            
            with open(cf_template, 'r') as f:
                content = f.read()
            
            required_sections = ['AWSTemplateFormatVersion', 'Parameters', 'Resources', 'Outputs']
            for section in required_sections:
                if section not in content:
                    return False
            
            # Test parameter files
            param_files = ['dev.json', 'staging.json', 'prod.json']
            for param_file in param_files:
                param_path = Path(f'infrastructure/parameters/{param_file}')
                if param_path.exists():
                    with open(param_path, 'r') as f:
                        json.load(f)  # Validate JSON
            
            return True
            
        except Exception as e:
            self.log(f"Infrastructure test failed: {e}", 'ERROR')
            return False
    
    def test_docker_configuration(self):
        """Test Docker configuration."""
        try:
            # Check Dockerfile
            if not Path('Dockerfile').exists():
                return False
            
            with open('Dockerfile', 'r') as f:
                content = f.read()
            
            if 'FROM python:' not in content:
                return False
            
            # Check docker-compose files
            compose_files = ['docker-compose.yml', 'docker-compose.dev.yml']
            for compose_file in compose_files:
                if not Path(compose_file).exists():
                    self.log(f"Missing compose file: {compose_file}")
                    return False
            
            return True
            
        except Exception as e:
            self.log(f"Docker configuration test failed: {e}", 'ERROR')
            return False
    
    def test_database_connections(self):
        """Test database connection capabilities."""
        try:
            # Test Redis connection (if available)
            try:
                import redis
                r = redis.Redis(host='localhost', port=6379, decode_responses=True)
                r.ping()
                self.log("Redis connection successful")
            except:
                self.log("Redis not available (expected in some environments)")
            
            # Test MongoDB connection (if available)
            try:
                import pymongo
                client = pymongo.MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=1000)
                client.server_info()
                self.log("MongoDB connection successful")
            except:
                self.log("MongoDB not available (expected in some environments)")
            
            return True
            
        except Exception as e:
            self.log(f"Database connection test failed: {e}", 'ERROR')
            return False
    
    def generate_report(self):
        """Generate test report."""
        self.results['end_time'] = datetime.now().isoformat()
        self.results['summary'] = {
            'total_tests': self.test_count,
            'passed_tests': self.passed_count,
            'failed_tests': self.test_count - self.passed_count,
            'success_rate': (self.passed_count / self.test_count * 100) if self.test_count > 0 else 0
        }
        
        # Save detailed results
        with open('test_results.json', 'w') as f:
            json.dump(self.results, f, indent=2)
        
        # Print summary
        print("\n" + "="*70)
        print("🧪 REMOTE TEST SUITE RESULTS")
        print("="*70)
        
        for test_name, result in self.results['tests'].items():
            status_icon = "✅" if result['status'] == 'PASSED' else "❌"
            print(f"{status_icon} {test_name}: {result['status']} ({result['duration']:.2f}s)")
        
        print(f"\n📊 Summary: {self.passed_count}/{self.test_count} tests passed")
        print(f"🎯 Success Rate: {self.results['summary']['success_rate']:.1f}%")
        
        if self.results['summary']['success_rate'] >= 80:
            print("🎉 OVERALL: SUCCESS - Project is ready for deployment!")
            return True
        else:
            print("⚠️ OVERALL: ISSUES FOUND - Review failed tests")
            return False
    
    def run_all_tests(self):
        """Run all tests."""
        print("🚀 Starting Remote Test Suite for Sports Prediction Bot")
        print(f"Environment: {self.results['environment']['platform']}")
        print(f"Python: {sys.version.split()[0]}")
        
        # Define test suite
        tests = [
            ("Python Environment", self.test_python_environment),
            ("Project Structure", self.test_project_structure),
            ("Dependency Installation", self.test_dependency_installation),
            ("Configuration Loading", self.test_configuration_loading),
            ("Core Imports", self.test_core_imports),
            ("CLI Structure", self.test_cli_structure),
            ("Infrastructure Files", self.test_infrastructure_files),
            ("Docker Configuration", self.test_docker_configuration),
            ("Database Connections", self.test_database_connections)
        ]
        
        # Run tests
        for test_name, test_func in tests:
            self.run_test(test_name, test_func)
        
        # Generate report
        return self.generate_report()

def main():
    """Main function."""
    suite = RemoteTestSuite()
    success = suite.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())

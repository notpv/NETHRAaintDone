#!/usr/bin/env python3
"""
NETHRA Test Runner Script
Comprehensive testing suite for NETHRA Guardian AI Backend
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
import logging
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NethraTestRunner:
    """Test runner for NETHRA backend"""
    
    def __init__(self):
        self.project_root = project_root
        self.test_results = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": []
        }
    
    def setup_test_environment(self):
        """Setup test environment"""
        logger.info("🔧 Setting up test environment...")
        
        # Set test environment variables
        os.environ["TESTING"] = "true"
        os.environ["DATABASE_URL"] = "sqlite:///./test_nethra.db"
        os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key-for-testing-only"
        os.environ["LOG_LEVEL"] = "ERROR"
        
        try:
            from database.database import init_db
            init_db()
            logger.info("✅ Test database initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize test database: {e}")
            return False
        
        return True
    
    def run_all_tests(self):
        """Run complete test suite"""
        logger.info("🚀 Starting NETHRA comprehensive test suite...")
        
        if not self.setup_test_environment():
            logger.error("❌ Test environment setup failed")
            return False
        
        try:
            # Test if server can start
            logger.info("🌐 Testing FastAPI server startup...")
            import main
            from fastapi.testclient import TestClient
            
            client = TestClient(main.app)
            response = client.get("/health")
            
            if response.status_code == 200:
                logger.info("✅ FastAPI server startup test passed")
                self.test_results["passed"] += 1
            else:
                logger.error("❌ FastAPI server startup test failed")
                self.test_results["failed"] += 1
            
            self.test_results["total_tests"] += 1
            
            # Test AI model loading
            logger.info("🤖 Testing AI model integration...")
            try:
                from scripts.integrated_backend import get_nethra_backend
                backend = get_nethra_backend()
                health = backend.health_check()
                
                if health.get("model_loaded"):
                    logger.info("✅ AI model loading test passed")
                    self.test_results["passed"] += 1
                else:
                    logger.error("❌ AI model loading test failed")
                    self.test_results["failed"] += 1
                    
            except Exception as e:
                logger.error(f"❌ AI model test failed: {e}")
                self.test_results["failed"] += 1
                self.test_results["errors"].append(f"Model test failed: {e}")
            
            self.test_results["total_tests"] += 1
            
            # Test database connectivity
            logger.info("🗄️ Testing database connectivity...")
            try:
                from database.database import get_db
                db = next(get_db())
                db.execute("SELECT 1")
                logger.info("✅ Database connectivity test passed")
                self.test_results["passed"] += 1
            except Exception as e:
                logger.error(f"❌ Database test failed: {e}")
                self.test_results["failed"] += 1
                self.test_results["errors"].append(f"Database test failed: {e}")
            
            self.test_results["total_tests"] += 1
            
            # Generate report
            return self.generate_test_report()
            
        except Exception as e:
            logger.error(f"❌ Test suite failed: {e}")
            self.test_results["errors"].append(f"Test suite failed: {e}")
            return False
    
    def generate_test_report(self):
        """Generate test report"""
        total = self.test_results["total_tests"]
        passed = self.test_results["passed"]
        failed = self.test_results["failed"]
        
        success_rate = (passed / total * 100) if total > 0 else 0
        
        report = f"""
        
🔐 NETHRA Guardian AI Backend - Test Report
==========================================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 Test Results Summary:
- Total Tests: {total}
- Passed: {passed} ✅
- Failed: {failed} ❌
- Success Rate: {success_rate:.1f}%

"""
        
        if self.test_results["errors"]:
            report += "\n❌ Errors:\n"
            for error in self.test_results["errors"]:
                report += f"- {error}\n"
        
        if failed == 0:
            report += "\n🏆 All tests passed! NETHRA backend is ready!\n"
        else:
            report += f"\n⚠️ {failed} test(s) failed. Review required.\n"
        
        print(report)
        
        # Save report
        try:
            with open("test_report.txt", "w") as f:
                f.write(report)
            logger.info("📄 Test report saved to test_report.txt")
        except Exception as e:
            logger.error(f"❌ Failed to save report: {e}")
        
        return success_rate >= 80

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="NETHRA Backend Test Runner")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    runner = NethraTestRunner()
    
    try:
        success = runner.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.warning("⏹️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Test runner failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

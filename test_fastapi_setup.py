"""Test script για το FastAPI setup"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("Testing FastAPI setup...")
print("-" * 80)

# Test 1: Import FASTAPI_AVAILABLE
try:
    from main import FASTAPI_AVAILABLE
    print(f"✅ FASTAPI_AVAILABLE imported: {FASTAPI_AVAILABLE}")
except Exception as e:
    print(f"❌ Failed to import FASTAPI_AVAILABLE: {e}")
    sys.exit(1)

# Test 2: Import sede_report
try:
    from sede_report import get_daily_sede_report
    print(f"✅ get_daily_sede_report imported successfully")
except Exception as e:
    print(f"❌ Failed to import get_daily_sede_report: {e}")
    sys.exit(1)

# Test 3: Test setup_fastapi_server import
try:
    from main import setup_fastapi_server
    print(f"✅ setup_fastapi_server imported successfully")
except Exception as e:
    print(f"❌ Failed to import setup_fastapi_server: {e}")
    sys.exit(1)

# Test 4: Check if FastAPI app can be created
if FASTAPI_AVAILABLE:
    try:
        from fastapi import FastAPI
        app = FastAPI()
        @app.get("/test")
        async def test():
            return {"message": "test"}
        print(f"✅ FastAPI app created successfully")
    except Exception as e:
        print(f"❌ Failed to create FastAPI app: {e}")
        sys.exit(1)
else:
    print("⚠️  FastAPI not available (will use fallback)")

print("-" * 80)
print("✅ All tests passed!")

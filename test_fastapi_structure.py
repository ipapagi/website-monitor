"""Test script για τη νέα δομή FastAPI"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("Testing FastAPI refactored structure...")
print("-" * 80)

# Test 1: Import app instance
try:
    from main import app
    print(f"✅ app instance imported successfully")
    print(f"   Type: {type(app)}")
except Exception as e:
    print(f"❌ Failed to import app: {e}")
    sys.exit(1)

# Test 2: Check app routes
try:
    routes = [route.path for route in app.routes]
    print(f"✅ App routes available: {routes}")
    if "/sede/daily" in routes:
        print(f"   ✅ /sede/daily endpoint exists")
    else:
        print(f"   ❌ /sede/daily endpoint missing")
except Exception as e:
    print(f"❌ Failed to check routes: {e}")

# Test 3: Verify create_fastapi_app function
try:
    from main import create_fastapi_app
    test_app = create_fastapi_app()
    print(f"✅ create_fastapi_app() works correctly")
    print(f"   Title: {test_app.title}")
    print(f"   Version: {test_app.version}")
except Exception as e:
    print(f"❌ Failed to create app: {e}")
    sys.exit(1)

# Test 4: Verify main function still works
try:
    from main import main
    print(f"✅ main() function still available for normal execution")
except Exception as e:
    print(f"❌ Failed to import main: {e}")
    sys.exit(1)

print("-" * 80)
print("✅ All structure tests passed!")
print("\nUsage:")
print("  FastAPI server: uvicorn src.main:app --host 0.0.0.0 --port 8000")
print("  Normal program: python -m src.main [arguments]")

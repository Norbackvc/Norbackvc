#!/usr/bin/env python3
"""Test script to debug why the app doesn't start."""
import sys
import os
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("TEST 1: Importing database module...")
try:
    from pos_system.database import initialize_database
    print("✓ Database module imported")
except Exception as e:
    print(f"✗ Error: {e}")
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("TEST 2: Initializing database...")
try:
    initialize_database()
    print("✓ Database initialized")
except Exception as e:
    print(f"✗ Error: {e}")
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("TEST 3: Importing auth module...")
try:
    from pos_system import auth
    print("✓ Auth module imported")
except Exception as e:
    print(f"✗ Error: {e}")
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("TEST 4: Importing GUI modules...")
try:
    from pos_system.gui.login import LoginWindow
    from pos_system.gui.main_window import MainWindow
    print("✓ GUI modules imported")
except Exception as e:
    print(f"✗ Error: {e}")
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("TEST 5: All imports successful!")
print("=" * 60)

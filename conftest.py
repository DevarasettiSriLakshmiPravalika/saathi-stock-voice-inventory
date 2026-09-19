# Root conftest — adds backend/ to sys.path so `app` is importable.
import sys
import os

# Ensure the backend package root is on the path for all tests.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

"""Ensure the demo repo root is on sys.path so `src.pricing` is importable."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
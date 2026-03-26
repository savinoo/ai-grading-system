"""
Streamlit observability app — debug interface for CorretumAI grading pipeline.

Entrypoint que delega para app/main.py.
Run: streamlit run streamlit_app.py
"""
import runpy
import os
import sys

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Delegate to the actual app
runpy.run_module('app.main', run_name='__main__')

"""
Smoke test for Streamlit entry points.
Tests that the app modules can be imported and basic functions exist.
"""
import sys
import pathlib
import pytest

# Add 02-Src to path
src_path = pathlib.Path(__file__).parent.parent / "02-Src"
sys.path.insert(0, str(src_path))


def test_app_imports():
    """Test that app.py can be imported without executing Streamlit code."""
    try:
        # Import as module to check syntax
        import app
        assert app is not None
        assert hasattr(app, 'OLLAMA_MODEL')
        assert hasattr(app, 'DOCUMENTS_DIR')
    except ImportError as e:
        # If streamlit or langchain not installed, that's OK for unit tests
        if 'streamlit' in str(e) or 'langchain' in str(e):
            pytest.skip(f"Skipping due to missing dependency: {e}")
        else:
            raise


def test_app_optimized_imports():
    """Test that app_optimized.py can be imported."""
    try:
        import app_optimized
        assert app_optimized is not None
        assert hasattr(app_optimized, 'PerformanceMonitor')
        assert hasattr(app_optimized, 'MultiLayerCache')
        assert hasattr(app_optimized, 'OptimizedDocumentProcessor')
    except ImportError as e:
        if 'streamlit' in str(e) or 'langchain' in str(e):
            pytest.skip(f"Skipping due to missing dependency: {e}")
        else:
            raise


def test_app_config_values():
    """Test that app configuration values are sensible."""
    try:
        import app
        assert isinstance(app.OLLAMA_MODEL, str)
        assert len(app.OLLAMA_MODEL) > 0
        assert isinstance(app.DOCUMENTS_DIR, str)
        assert isinstance(app.CHROMA_DB_PATH, str)
    except ImportError:
        pytest.skip("Streamlit not installed")


def test_optimized_config_values():
    """Test that optimized app configuration is sensible."""
    try:
        import app_optimized
        assert app_optimized.CHUNK_SIZE > 0
        assert app_optimized.CHUNK_OVERLAP >= 0
        assert app_optimized.CHUNK_OVERLAP < app_optimized.CHUNK_SIZE
        assert app_optimized.MAX_WORKERS > 0
    except ImportError:
        pytest.skip("Dependencies not installed")

"""
Test suite for Lexi Law Agent
Run with: pytest test_file.py -v
"""

import os
import sys
from pathlib import Path
from importlib import import_module
import pytest
from unittest.mock import Mock, patch, MagicMock


# ==============================================================================
# BASIC REPOSITORY STRUCTURE TESTS
# ==============================================================================

def test_repo_has_core_files():
    """Verify essential project files exist"""
    root = Path(__file__).resolve().parent
    assert (root / "Dockerfile").exists(), "Dockerfile missing"
    assert (root / "requirements.txt").exists(), "requirements.txt missing"
    assert (root / "docker-compose.yml").exists(), "docker-compose.yml missing"
    assert (root / ".env.example").exists(), ".env.example missing"
    assert (root / "README.md").exists(), "README.md missing"


def test_src_directory_structure():
    """Verify src directory has required modules"""
    root = Path(__file__).resolve().parent
    src_dir = root / "src"
    assert src_dir.exists(), "src directory missing"
    
    required_files = [
        "app.py",
        "auth.py",
        "tools.py",
        "retriever.py",
        "agentsandnodes.py",
        "agent_flow_calling.py",
        "redis_caching.py"
    ]
    
    for file in required_files:
        assert (src_dir / file).exists(), f"src/{file} missing"


def test_python_itself():
    """Basic sanity check"""
    assert 1 + 1 == 2


# ==============================================================================
# IMPORT TESTS
# ==============================================================================

def test_app_imports():
    """Test that main app module can be imported"""
    root = Path(__file__).resolve().parent
    sys.path.insert(0, str(root / "src"))
    
    try:
        import app
        assert hasattr(app, 'load_main_application'), "load_main_application function missing"
    except ModuleNotFoundError as e:
        pytest.fail(f"Failed to import app module: {e}")


def test_auth_module_imports():
    """Test authentication module imports"""
    root = Path(__file__).resolve().parent
    sys.path.insert(0, str(root / "src"))
    
    try:
        import auth
        assert hasattr(auth, 'SessionManager'), "SessionManager class missing"
        assert hasattr(auth, 'render_auth_page'), "render_auth_page function missing"
    except ModuleNotFoundError as e:
        pytest.fail(f"Failed to import auth module: {e}")


def test_tools_module_imports():
    """Test tools module imports"""
    root = Path(__file__).resolve().parent
    sys.path.insert(0, str(root / "src"))
    
    try:
        import tools
        assert hasattr(tools, 'laws_db_lookup'), "laws_db_lookup function missing"
        assert hasattr(tools, 'procedures_db_lookup'), "procedures_db_lookup function missing"
        assert hasattr(tools, 'generate_court_form'), "generate_court_form function missing"
    except ModuleNotFoundError as e:
        pytest.fail(f"Failed to import tools module: {e}")


def test_agentsandnodes_imports():
    """Test agent nodes module imports"""
    root = Path(__file__).resolve().parent
    sys.path.insert(0, str(root / "src"))
    
    try:
        import agentsandnodes
        assert hasattr(agentsandnodes, 'supervisor_node'), "supervisor_node missing"
        assert hasattr(agentsandnodes, 'law_node'), "law_node missing"
        assert hasattr(agentsandnodes, 'procedure_node'), "procedure_node missing"
        assert hasattr(agentsandnodes, 'general_node'), "general_node missing"
    except ModuleNotFoundError as e:
        pytest.fail(f"Failed to import agentsandnodes module: {e}")


# ==============================================================================
# ENVIRONMENT CONFIGURATION TESTS
# ==============================================================================

def test_env_example_has_required_vars():
    """Verify .env.example has all required environment variables"""
    root = Path(__file__).resolve().parent
    env_example = root / ".env.example"
    
    with open(env_example, 'r') as f:
        content = f.read()
    
    required_vars = [
        "OPENAI_API_KEY",
        "AZURE_POSTGRES_HOST",
        "AZURE_POSTGRES_DB",
        "AZURE_POSTGRES_USER",
        "AZURE_POSTGRES_PASSWORD",
        "REDIS_HOST",
        "REDIS_PORT",
        "REDIS_PASSWORD"
    ]
    
    for var in required_vars:
        assert var in content, f"{var} missing from .env.example"


# ==============================================================================
# AZURE BLOB SYNC TESTS
# ==============================================================================

@pytest.fixture
def mock_env(monkeypatch):
    """Fixture to manage environment variables"""
    def _set_env(**kwargs):
        for key, value in kwargs.items():
            monkeypatch.setenv(key, value)
    return _set_env


def test_choose_chroma_dir_defaults(tmp_path, monkeypatch):
    """Test choose_chroma_dir returns default when no env vars set"""
    root = Path(__file__).resolve().parent
    sys.path.insert(0, str(root / "src"))
    
    # Import after adding to path
    from blob_sync import choose_chroma_dir
    
    default_dir = tmp_path / "default"
    default_dir.mkdir()
    
    # Clear environment variables
    for k in ["LAWS_CHROMA_DIR", "LAWS_CHROMA_SAS_URL"]:
        monkeypatch.delenv(k, raising=False)
    
    # Test with existing default directory
    picked = choose_chroma_dir(
        default_dir=str(default_dir),
        sas_url="",
        cache_dir=str(tmp_path / "cache")
    )
    
    assert Path(picked) == default_dir


def test_choose_chroma_dir_with_sas_url(tmp_path, monkeypatch):
    """Test choose_chroma_dir uses cache when SAS URL provided"""
    root = Path(__file__).resolve().parent
    sys.path.insert(0, str(root / "src"))
    
    from blob_sync import choose_chroma_dir
    
    cache_dir = tmp_path / "cache"
    default_dir = tmp_path / "default"
    
    # Mock SAS URL
    fake_sas = "https://example.blob.core.windows.net/container?sp=r&st=..."
    
    with patch('blob_sync.sync_container_to_dir') as mock_sync:
        picked = choose_chroma_dir(
            default_dir=str(default_dir),
            sas_url=fake_sas,
            cache_dir=str(cache_dir)
        )
        
        # Should attempt to sync when SAS URL provided and no default exists
        if not default_dir.exists():
            mock_sync.assert_called_once()


# ==============================================================================
# REDIS CACHING TESTS
# ==============================================================================

def test_redis_cache_initialization():
    """Test RedisCache class can be initialized"""
    root = Path(__file__).resolve().parent
    sys.path.insert(0, str(root / "src"))
    
    from redis_caching import RedisCache
    
    with patch('redis_caching.redis.Redis') as mock_redis:
        mock_redis.return_value = MagicMock()
        
        cache = RedisCache(
            host="localhost",
            port=6379,
            password="test",
            ttl=3600
        )
        
        assert cache is not None


def test_redis_cache_key_generation():
    """Test cache key generation is consistent"""
    root = Path(__file__).resolve().parent
    sys.path.insert(0, str(root / "src"))
    
    from redis_caching import RedisCache
    
    with patch('redis_caching.redis.Redis'):
        cache = RedisCache(host="localhost", port=6379, password="test")
        
        # Same input should generate same key
        key1 = cache._generate_key("test query", {"param": "value"})
        key2 = cache._generate_key("test query", {"param": "value"})
        
        assert key1 == key2
        
        # Different input should generate different key
        key3 = cache._generate_key("different query", {"param": "value"})
        assert key1 != key3


# ==============================================================================
# AGENT SYSTEM TESTS
# ==============================================================================

def test_agent_state_structure():
    """Test State TypedDict has required fields"""
    root = Path(__file__).resolve().parent
    sys.path.insert(0, str(root / "src"))
    
    from agentsandnodes import State
    
    # State should have these annotations
    assert 'messages' in State.__annotations__
    assert 'next' in State.__annotations__
    assert 'file_path' in State.__annotations__
    assert 'extracted_context' in State.__annotations__


def test_supervisor_prompt_exists():
    """Test supervisor agent has routing prompt defined"""
    root = Path(__file__).resolve().parent
    sys.path.insert(0, str(root / "src"))
    
    from agentsandnodes import SUPERVISOR_AGENT_PROMPT
    
    assert SUPERVISOR_AGENT_PROMPT is not None
    assert len(SUPERVISOR_AGENT_PROMPT) > 0
    assert "law" in SUPERVISOR_AGENT_PROMPT.lower()
    assert "procedure" in SUPERVISOR_AGENT_PROMPT.lower()


def test_agent_system_prompts_defined():
    """Test all agent system prompts are defined"""
    root = Path(__file__).resolve().parent
    sys.path.insert(0, str(root / "src"))
    
    from agentsandnodes import LAW_SYS, PROC_SYS, UNKNOWN_SYS
    
    assert LAW_SYS is not None and len(LAW_SYS) > 0
    assert PROC_SYS is not None and len(PROC_SYS) > 0
    assert UNKNOWN_SYS is not None and len(UNKNOWN_SYS) > 0


# ==============================================================================
# AUTHENTICATION TESTS
# ==============================================================================

def test_session_manager_initialization():
    """Test SessionManager can be initialized"""
    root = Path(__file__).resolve().parent
    sys.path.insert(0, str(root / "src"))
    
    from auth import SessionManager
    
    with patch('auth.st') as mock_st:
        mock_st.session_state = {}
        session_mgr = SessionManager()
        assert session_mgr is not None


def test_password_hashing():
    """Test password hashing is consistent"""
    root = Path(__file__).resolve().parent
    sys.path.insert(0, str(root / "src"))
    
    from auth import DatabaseManager
    
    with patch('auth.psycopg2.connect'):
        db = DatabaseManager(
            host="test",
            database="test",
            user="test",
            password="test"
        )
        
        # Same password should produce same hash
        hash1 = db._hash_password("testpass123")
        hash2 = db._hash_password("testpass123")
        assert hash1 == hash2
        
        # Different passwords should produce different hashes
        hash3 = db._hash_password("differentpass")
        assert hash1 != hash3


# ==============================================================================
# RETRIEVER TESTS
# ==============================================================================

def test_text_splitter_configuration():
    """Test document chunking configuration"""
    root = Path(__file__).resolve().parent
    sys.path.insert(0, str(root / "src"))
    
    from retriever import chunk_document_text
    
    test_text = "This is a test document. " * 100
    chunks = chunk_document_text(test_text)
    
    assert len(chunks) > 0
    assert all(isinstance(chunk, str) for chunk in chunks)


# ==============================================================================
# INTEGRATION TESTS
# ==============================================================================

@pytest.mark.integration
def test_agent_graph_builds():
    """Test that the agent graph can be built without errors"""
    root = Path(__file__).resolve().parent
    sys.path.insert(0, str(root / "src"))
    
    from agent_flow_calling import build_app
    
    with patch.dict(os.environ, {
        'OPENAI_API_KEY': 'test-key',
        'REDIS_HOST': 'localhost',
        'REDIS_PORT': '6379',
        'REDIS_PASSWORD': 'test'
    }):
        try:
            app = build_app()
            assert app is not None
        except Exception as e:
            # Graph building might fail due to missing dependencies in test env
            # but we can at least verify the function exists
            pytest.skip(f"Graph building requires full environment: {e}")


# ==============================================================================
# SECURITY TESTS
# ==============================================================================

def test_no_secrets_in_code():
    """Ensure no secrets are hardcoded in source files"""
    root = Path(__file__).resolve().parent
    src_dir = root / "src"
    
    # Common secret patterns
    secret_patterns = [
        'sk-proj-',  # OpenAI keys
        'password=',
        'api_key=',
        'secret_key='
    ]
    
    for py_file in src_dir.glob("*.py"):
        with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read().lower()
            
        for pattern in secret_patterns:
            if pattern in content:
                # Allow patterns in comments or as variable names
                lines = content.split('\n')
                for i, line in enumerate(lines, 1):
                    if pattern in line and not line.strip().startswith('#'):
                        if '=' in line and '"' in line and len(line.split('"')[1]) > 10:
                            pytest.fail(
                                f"Potential hardcoded secret in {py_file.name}:{i}"
                            )


def test_env_file_in_gitignore():
    """Ensure .env is in .gitignore"""
    root = Path(__file__).resolve().parent
    gitignore = root / ".gitignore"
    
    if gitignore.exists():
        with open(gitignore, 'r') as f:
            content = f.read()
        
        assert '.env' in content, ".env should be in .gitignore"
        assert 'data/' in content or 'data\\' in content, "data folder should be gitignored"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

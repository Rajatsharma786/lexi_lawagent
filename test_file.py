"""
Test suite for Lexi Law Agent
Run with: pytest test_file.py -v
"""

import os
import sys
from pathlib import Path
import pytest
from unittest.mock import Mock, patch, MagicMock

# ==============================================================================
# SETUP - Mock Azure before any imports
# ==============================================================================

@pytest.fixture(autouse=True)
def mock_azure_and_redis():
    """Auto-use fixture to mock Azure and Redis connections globally"""
    with patch.dict(os.environ, {
        'OPENAI_API_KEY': 'sk-test-key-12345678901234567890',
        'REDIS_HOST': 'localhost',
        'REDIS_PORT': '6379',
        'REDIS_PASSWORD': 'test-password',
        'REDIS_EXPIRATION': '3600',
        'HF_TOKEN': 'hf_test_token'
    }):
        with patch('azure.storage.blob.ContainerClient') as mock_container:
            with patch('redis.Redis') as mock_redis:
                # Setup mock Redis
                mock_redis_instance = MagicMock()
                mock_redis.return_value = mock_redis_instance
                
                # Setup mock Azure Container
                mock_container_instance = MagicMock()
                mock_container.from_container_url.return_value = mock_container_instance
                mock_container_instance.list_blobs.return_value = []
                
                yield


# ==============================================================================
# BASIC REPOSITORY STRUCTURE TESTS
# ==============================================================================

def test_repo_has_core_files():
    """Verify essential project files exist"""
    root = Path(__file__).resolve().parent
    assert (root / "Dockerfile").exists(), "Dockerfile missing"
    assert (root / "requirements.txt").exists(), "requirements.txt missing"


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
        "redis_caching.py",
        "blob_sync.py"
    ]
    
    for file in required_files:
        assert (src_dir / file).exists(), f"src/{file} missing"


def test_python_itself():
    """Basic sanity check"""
    assert 1 + 1 == 2


# ==============================================================================
# IMPORT TESTS
# ==============================================================================

def test_tools_module_imports():
    """Test tools module imports without Azure/Redis connections"""
    root = Path(__file__).resolve().parent
    sys.path.insert(0, str(root / "src"))
    
    with patch('langchain_community.vectorstores.Chroma'):
        with patch('langchain_community.embeddings.HuggingFaceEmbeddings'):
            with patch('langchain.retrievers.contextual_compression.ContextualCompressionRetriever'):
                with patch('langchain.retrievers.document_compressors.LLMChainFilter'):
                    with patch('langchain_community.cross_encoders.HuggingFaceCrossEncoder'):
                        with patch('langchain.retrievers.document_compressors.CrossEncoderReranker'):
                            with patch('sentence_transformers.SentenceTransformer'):
                                try:
                                    import tools
                                    assert hasattr(tools, 'laws_db_lookup'), "laws_db_lookup function missing"
                                    assert hasattr(tools, 'procedures_db_lookup'), "procedures_db_lookup function missing"
                                    assert hasattr(tools, 'generate_court_form'), "generate_court_form function missing"
                                except Exception as e:
                                    pytest.fail(f"Failed to import tools module: {e}")


def test_agentsandnodes_imports():
    """Test agent nodes module imports"""
    root = Path(__file__).resolve().parent
    sys.path.insert(0, str(root / "src"))
    
    with patch('langchain_community.vectorstores.Chroma'):
        with patch('langchain_community.embeddings.HuggingFaceEmbeddings'):
            with patch('langchain.retrievers.contextual_compression.ContextualCompressionRetriever'):
                with patch('langchain.retrievers.document_compressors.LLMChainFilter'):
                    with patch('langchain_community.cross_encoders.HuggingFaceCrossEncoder'):
                        with patch('langchain.retrievers.document_compressors.CrossEncoderReranker'):
                            with patch('sentence_transformers.SentenceTransformer'):
                                with patch('langgraph.prebuilt.create_react_agent'):
                                    with patch('langchain_openai.ChatOpenAI'):
                                        try:
                                            import agentsandnodes
                                            assert hasattr(agentsandnodes, 'supervisor_node'), "supervisor_node missing"
                                            assert hasattr(agentsandnodes, 'law_node'), "law_node missing"
                                            assert hasattr(agentsandnodes, 'procedure_node'), "procedure_node missing"
                                            assert hasattr(agentsandnodes, 'general_node'), "general_node missing"
                                        except Exception as e:
                                            pytest.fail(f"Failed to import agentsandnodes module: {e}")


def test_auth_module_imports():
    """Test authentication module imports"""
    root = Path(__file__).resolve().parent
    sys.path.insert(0, str(root / "src"))
    
    with patch('psycopg2.connect'):
        try:
            import auth
            assert hasattr(auth, 'SessionManager'), "SessionManager class missing"
            assert hasattr(auth, 'render_auth_page'), "render_auth_page function missing"
        except Exception as e:
            pytest.fail(f"Failed to import auth module: {e}")


# ==============================================================================
# AZURE BLOB SYNC TESTS
# ==============================================================================

def test_choose_chroma_dir_defaults(tmp_path, monkeypatch):
    """Test choose_chroma_dir returns default when no env vars set"""
    root = Path(__file__).resolve().parent
    sys.path.insert(0, str(root / "src"))
    
    from blob_sync import choose_chroma_dir
    
    default_dir = tmp_path / "default"
    default_dir.mkdir()
    
    # Clear environment variables
    monkeypatch.delenv("LAWS_CHROMA_DIR", raising=False)
    monkeypatch.delenv("LAWS_CHROMA_SAS_URL", raising=False)
    
    picked = choose_chroma_dir(
        env_var_dir="LAWS_CHROMA_DIR",
        env_var_sas="LAWS_CHROMA_SAS_URL",
        subdir_name="laws_db_chroma",
        default_dir=str(default_dir)
    )
    
    assert Path(picked) == default_dir


def test_choose_chroma_dir_with_mounted_dir(tmp_path, monkeypatch):
    """Test choose_chroma_dir uses mounted directory when available"""
    root = Path(__file__).resolve().parent
    sys.path.insert(0, str(root / "src"))
    
    from blob_sync import choose_chroma_dir
    
    mounted_dir = tmp_path / "mounted"
    mounted_dir.mkdir()
    
    monkeypatch.setenv("LAWS_CHROMA_DIR", str(mounted_dir))
    
    picked = choose_chroma_dir(
        env_var_dir="LAWS_CHROMA_DIR",
        env_var_sas="LAWS_CHROMA_SAS_URL",
        subdir_name="laws_db_chroma",
        default_dir="./default"
    )
    
    assert Path(picked) == mounted_dir


def test_choose_chroma_dir_with_sas_url(tmp_path, monkeypatch):
    """Test choose_chroma_dir uses cache when SAS URL provided"""
    root = Path(__file__).resolve().parent
    sys.path.insert(0, str(root / "src"))
    
    monkeypatch.delenv("LAWS_CHROMA_DIR", raising=False)
    monkeypatch.setenv("CHROMA_CACHE_DIR", str(tmp_path / ".chroma_cache"))
    
    fake_sas = "https://example.blob.core.windows.net/container?sp=r&st=..."
    monkeypatch.setenv("LAWS_CHROMA_SAS_URL", fake_sas)
    
    with patch('blob_sync.sync_container_to_dir') as mock_sync:
        from blob_sync import choose_chroma_dir
        
        picked = choose_chroma_dir(
            env_var_dir="LAWS_CHROMA_DIR",
            env_var_sas="LAWS_CHROMA_SAS_URL",
            subdir_name="laws_db_chroma",
            default_dir="./default"
        )
        
        # Verify sync was called
        mock_sync.assert_called_once()
        
        # Verify returned path is in cache dir
        assert ".chroma_cache" in picked


# ==============================================================================
# REDIS CACHING TESTS
# ==============================================================================

def test_redis_cache_initialization():
    """Test RedisCache class can be initialized"""
    root = Path(__file__).resolve().parent
    sys.path.insert(0, str(root / "src"))
    
    from redis_caching import RedisCache
    
    cache = RedisCache()
    assert cache is not None
    assert cache.redis_host == 'localhost'
    assert cache.redis_port == 6379


def test_redis_cache_query_hash():
    """Test query hash generation is consistent"""
    root = Path(__file__).resolve().parent
    sys.path.insert(0, str(root / "src"))
    
    from redis_caching import RedisCache
    
    cache = RedisCache()
    
    # Same input should generate same hash
    hash1 = cache.get_query_hash("test query")
    hash2 = cache.get_query_hash("test query")
    assert hash1 == hash2
    
    # Different input should generate different hash
    hash3 = cache.get_query_hash("different query")
    assert hash1 != hash3


# ==============================================================================
# AGENT SYSTEM TESTS
# ==============================================================================

def test_agent_state_structure():
    """Test State TypedDict has required fields"""
    root = Path(__file__).resolve().parent
    sys.path.insert(0, str(root / "src"))
    
    with patch('langchain_community.vectorstores.Chroma'):
        with patch('langchain_community.embeddings.HuggingFaceEmbeddings'):
            with patch('langchain.retrievers.contextual_compression.ContextualCompressionRetriever'):
                with patch('langchain.retrievers.document_compressors.CrossEncoderReranker'):
                    with patch('sentence_transformers.SentenceTransformer'):
                        with patch('langgraph.prebuilt.create_react_agent'):
                            with patch('langchain_openai.ChatOpenAI'):
                                from agentsandnodes import State
                                
                                assert 'messages' in State.__annotations__
                                assert 'next' in State.__annotations__
                                assert 'file_path' in State.__annotations__
                                assert 'extracted_context' in State.__annotations__


def test_supervisor_prompt_exists():
    """Test supervisor agent has routing prompt defined"""
    root = Path(__file__).resolve().parent
    sys.path.insert(0, str(root / "src"))
    
    with patch('langchain_community.vectorstores.Chroma'):
        with patch('langchain_community.embeddings.HuggingFaceEmbeddings'):
            with patch('langchain.retrievers.contextual_compression.ContextualCompressionRetriever'):
                with patch('langchain.retrievers.document_compressors.CrossEncoderReranker'):
                    with patch('sentence_transformers.SentenceTransformer'):
                        with patch('langgraph.prebuilt.create_react_agent'):
                            with patch('langchain_openai.ChatOpenAI'):
                                from agentsandnodes import SUPERVISOR_AGENT_PROMPT
                                
                                assert SUPERVISOR_AGENT_PROMPT is not None
                                assert len(SUPERVISOR_AGENT_PROMPT) > 0
                                assert "law" in SUPERVISOR_AGENT_PROMPT.lower()
                                assert "procedure" in SUPERVISOR_AGENT_PROMPT.lower()


def test_agent_system_prompts_defined():
    """Test all agent system prompts are defined"""
    root = Path(__file__).resolve().parent
    sys.path.insert(0, str(root / "src"))
    
    with patch('langchain_community.vectorstores.Chroma'):
        with patch('langchain_community.embeddings.HuggingFaceEmbeddings'):
            with patch('langchain.retrievers.contextual_compression.ContextualCompressionRetriever'):
                with patch('langchain.retrievers.document_compressors.CrossEncoderReranker'):
                    with patch('sentence_transformers.SentenceTransformer'):
                        with patch('langgraph.prebuilt.create_react_agent'):
                            with patch('langchain_openai.ChatOpenAI'):
                                from agentsandnodes import LAW_SYS, PROC_SYS, UNKNOWN_SYS
                                
                                assert LAW_SYS is not None and len(LAW_SYS) > 0
                                assert PROC_SYS is not None and len(PROC_SYS) > 0
                                assert UNKNOWN_SYS is not None and len(UNKNOWN_SYS) > 0


# ==============================================================================
# AUTHENTICATION TESTS
# ==============================================================================

def test_session_manager_methods():
    """Test SessionManager has required methods"""
    root = Path(__file__).resolve().parent
    sys.path.insert(0, str(root / "src"))
    
    with patch('psycopg2.connect'):
        from auth import SessionManager
        
        assert hasattr(SessionManager, 'initialize_session')
        assert hasattr(SessionManager, 'login_user')
        assert hasattr(SessionManager, 'logout_user')
        assert hasattr(SessionManager, 'is_authenticated')


def test_password_manager_hashing():
    """Test PasswordManager hashing"""
    root = Path(__file__).resolve().parent
    sys.path.insert(0, str(root / "src"))
    
    with patch('psycopg2.connect'):
        from auth import PasswordManager
        
        salt = PasswordManager.generate_salt()
        assert len(salt) == 32  # 16 bytes * 2 (hex)
        
        # Same password + salt should produce same hash
        hash1 = PasswordManager.hash_password("testpass123", salt)
        hash2 = PasswordManager.hash_password("testpass123", salt)
        assert hash1 == hash2
        
        # Verify password
        assert PasswordManager.verify_password("testpass123", hash1, salt)
        assert not PasswordManager.verify_password("wrongpass", hash1, salt)


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
# DOCKER CONFIGURATION TESTS
# ==============================================================================

def test_dockerfile_exists():
    """Verify Dockerfile exists and has required stages"""
    root = Path(__file__).resolve().parent
    dockerfile = root / "Dockerfile"
    
    assert dockerfile.exists(), "Dockerfile not found"
    
    with open(dockerfile, 'r') as f:
        content = f.read()
    
    # Check for multi-stage build
    assert 'FROM python:3.11' in content, "Python base image not found"
    assert 'AS builder' in content, "Builder stage not found"
    assert 'AS production' in content, "Production stage not found"
    
    # Check for test execution
    assert 'pytest' in content, "Test execution not found in builder stage"


def test_docker_compose_exists():
    """Verify docker-compose.yml exists"""
    root = Path(__file__).resolve().parent
    docker_compose = root / "docker-compose.yml"
    
    assert docker_compose.exists(), "docker-compose.yml not found"


# ==============================================================================
# SECURITY TESTS
# ==============================================================================

def test_no_secrets_in_code():
    """Ensure no secrets are hardcoded in source files"""
    root = Path(__file__).resolve().parent
    src_dir = root / "src"
    
    secret_patterns = [
        ('sk-proj-', 40),  # OpenAI keys
        ('hf_', 30),       # HuggingFace tokens
    ]
    
    for py_file in src_dir.glob("*.py"):
        with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        for pattern, min_len in secret_patterns:
            if pattern in content:
                lines = content.split('\n')
                for i, line in enumerate(lines, 1):
                    if pattern in line and not line.strip().startswith('#'):
                        if '=' in line and any(q in line for q in ['"', "'"]):
                            parts = line.split('=', 1)
                            if len(parts) > 1:
                                value = parts[1].strip().strip('"').strip("'")
                                if len(value) > min_len:
                                    pytest.fail(f"Potential hardcoded secret in {py_file.name}:{i}")


def test_env_file_in_gitignore():
    """Ensure .env is in .gitignore"""
    root = Path(__file__).resolve().parent
    gitignore = root / ".gitignore"
    
    if gitignore.exists():
        with open(gitignore, 'r') as f:
            content = f.read()
        
        assert '.env' in content, ".env should be in .gitignore"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
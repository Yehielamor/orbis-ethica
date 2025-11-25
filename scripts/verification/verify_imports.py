"""
Verification script to check imports with mocked dependencies.
"""
import sys
import os
from unittest.mock import MagicMock
import types

# Add project root to path
sys.path.append(os.getcwd())

# Helper to mock a package with submodules
def mock_package(name):
    m = MagicMock()
    sys.modules[name] = m
    return m

# Mock external dependencies
mock_package("anthropic")
mock_package("openai")
mock_package("langchain")
mock_package("langchain_openai")
mock_package("networkx")
mock_package("web3")
mock_package("eth_account")
mock_package("eth_utils")
mock_package("ipfshttpclient")
mock_package("py2neo")
mock_package("sqlalchemy")
mock_package("alembic")
mock_package("psycopg2")

# Mock fastapi and its submodules
fastapi = mock_package("fastapi")
fastapi_middleware = mock_package("fastapi.middleware")
fastapi_middleware_cors = mock_package("fastapi.middleware.cors")

mock_package("uvicorn")

# Mock pydantic
pydantic = mock_package("pydantic")
# Ensure BaseModel accepts arguments
class MockBaseModel:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
    
    def dict(self):
        return self.__dict__

pydantic.BaseModel = MockBaseModel
pydantic.Field = MagicMock()
# Mock field_validator decorator
def mock_validator(*args, **kwargs):
    def decorator(f):
        return f
    return decorator
pydantic.field_validator = mock_validator

mock_package("pydantic_settings")
mock_package("python_dotenv")

# Mock rich
mock_package("rich")
mock_package("rich.console")
mock_package("rich.table")
mock_package("rich.panel")
mock_package("rich.markdown")
mock_package("click")

print("Verifying imports...")

try:
    import backend.main
    print("✓ backend.main imported")
    
    import backend.api.app
    print("✓ backend.api.app imported")
    
    import backend.core.models.ulfr
    print("✓ backend.core.models.ulfr imported")
    
    import backend.entities.seeker
    print("✓ backend.entities.seeker imported")
    
    import backend.core.protocols.deliberation
    print("✓ backend.core.protocols.deliberation imported")
    
    # Check mocks
    import backend.governance.dao.contract
    print("✓ backend.governance.dao.contract imported")
    
    import backend.memory.graph.manager
    print("✓ backend.memory.graph.manager imported")
    
    import backend.security.crypto.signer
    print("✓ backend.security.crypto.signer imported")

    print("\nAll checks passed!")
    
except Exception as e:
    print(f"\n✗ Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

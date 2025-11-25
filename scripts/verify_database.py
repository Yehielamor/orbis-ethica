import sys
import os
import json
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.memory.graph import MemoryGraph
from backend.core.database import init_db, get_db, SessionLocal
from backend.core.models.sql_models import SQLMemoryNode
from backend.core.ledger import LocalBlockchain

def test_database_persistence():
    print("💾 Starting Database Verification...")
    
    # 1. Setup
    db_path = "orbis_ethica.db"
    if os.path.exists(db_path):
        os.remove(db_path)
        print("   🗑️  Cleaned up old DB")
        
    ledger = LocalBlockchain()
    graph = MemoryGraph(ledger=ledger)
    
    # 2. Add Node
    content = {"test": "persistence", "value": 42}
    agent_id = "TestAgent"
    node_id = graph.add_node("TEST_NODE", content, agent_id)
    
    print(f"\n🔹 Added Node: {node_id}")
    
    # 3. Verify Persistence (Direct SQL Check)
    db = SessionLocal()
    sql_node = db.query(SQLMemoryNode).filter(SQLMemoryNode.id == node_id).first()
    
    if sql_node:
        print(f"   ✅ Node found in DB!")
        print(f"      Type: {sql_node.type}")
        print(f"      Content: {sql_node.content}")
        print(f"      Ledger Block: #{sql_node.ledger_block_index}")
    else:
        print("   ❌ Node NOT found in DB!")
        
    db.close()
    
    # 4. Verify Retrieval via Graph API
    retrieved_node = graph.get_node(node_id)
    if retrieved_node and retrieved_node.content == content:
        print("   ✅ Graph.get_node() working correctly")
    else:
        print("   ❌ Graph.get_node() failed")

    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)

if __name__ == "__main__":
    test_database_persistence()

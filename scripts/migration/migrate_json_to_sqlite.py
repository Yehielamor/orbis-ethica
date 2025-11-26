import json
import os
import sys
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from backend.core.database import init_db, SessionLocal
from backend.core.models.sql_models import LedgerEntryModel, SQLMemoryNode

def migrate_ledger():
    ledger_path = "burn_ledger.json"
    if not os.path.exists(ledger_path):
        print(f"⚠️ {ledger_path} not found. Skipping ledger migration.")
        return

    print(f"📦 Migrating {ledger_path}...")
    try:
        with open(ledger_path, 'r') as f:
            data = json.load(f)
            
        session = SessionLocal()
        count = 0
        for tx in data:
            # Check if exists (simple check by timestamp + sender + amount)
            # ideally we would have IDs in JSON
            
            # Parse timestamp
            ts_str = tx.get("timestamp")
            try:
                ts = datetime.fromisoformat(ts_str)
            except:
                ts = datetime.utcnow()

            # Validate required fields
            sender = tx.get("sender")
            recipient = tx.get("recipient")
            amount = tx.get("amount")
            
            if not all([sender, recipient, amount is not None]):
                print(f"⚠️ Skipping invalid entry: {tx}")
                continue

            entry = LedgerEntryModel(
                timestamp=ts,
                sender=sender,
                recipient=recipient,
                amount=amount,
                currency=tx.get("currency", "ETHC"),
                transaction_type=tx.get("type", "unknown"),
                reference_id=tx.get("reference_id"),
                description=tx.get("description")
            )
            session.add(entry)
            count += 1
            
        session.commit()
        print(f"✅ Migrated {count} ledger entries.")
        session.close()
        
        # Rename JSON to .bak
        os.rename(ledger_path, ledger_path + ".bak")
        
    except Exception as e:
        print(f"❌ Failed to migrate ledger: {e}")

def migrate_memory_graph():
    graph_path = "memory_graph.json"
    if not os.path.exists(graph_path):
        print(f"⚠️ {graph_path} not found. Skipping memory graph migration.")
        return

    print(f"🧠 Migrating {graph_path}...")
    try:
        with open(graph_path, 'r') as f:
            data = json.load(f)
            
        nodes = data.get("nodes", {})
        session = SessionLocal()
        count = 0
        
        for node_id, node_data in nodes.items():
            # Check if exists
            existing = session.query(SQLMemoryNode).filter_by(id=node_id).first()
            if existing:
                continue
                
            # Parse timestamp
            ts_str = node_data.get("timestamp")
            try:
                ts = datetime.fromisoformat(ts_str)
            except:
                ts = datetime.utcnow()

            sql_node = SQLMemoryNode(
                id=node_id,
                type=node_data.get("type"),
                content=node_data.get("content"),
                agent_id=node_data.get("agent_id"),
                timestamp=ts,
                parent_ids=node_data.get("parent_ids", [])
            )
            session.add(sql_node)
            count += 1
            
        session.commit()
        print(f"✅ Migrated {count} memory nodes.")
        session.close()
        
        # Rename JSON to .bak
        os.rename(graph_path, graph_path + ".bak")
        
    except Exception as e:
        print(f"❌ Failed to migrate memory graph: {e}")

if __name__ == "__main__":
    print("🚀 Starting Migration to SQLite...")
    init_db() # Ensure tables exist
    migrate_ledger()
    migrate_memory_graph()
    print("🏁 Migration Complete.")

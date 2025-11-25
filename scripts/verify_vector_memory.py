import sys
import os
import shutil

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.memory.vector_store import VectorStore
from backend.entities.base import BaseEntity
from backend.core.models import Entity, EntityType

# Mock Entity for testing
class MockEntity(BaseEntity):
    def get_system_prompt(self):
        return ""
    def evaluate_proposal(self, proposal):
        pass

def test_vector_memory():
    print("🧠 Starting Vector Memory Verification...")
    
    # 1. Setup
    storage_path = "test_vector_memory.json"
    if os.path.exists(storage_path):
        os.remove(storage_path)
        
    store = VectorStore(storage_path=storage_path)
    
    # 2. Add Memories
    memories = [
        "The council decided that privacy is more important than security in the case of facial recognition.",
        "We approved the new water purification system to save lives in Sector 7.",
        "Fairness requires that we distribute resources equally among all districts.",
        "The AI rights bill was rejected because it lacked clear definitions of sentience."
    ]
    
    print("\n🔹 Adding Memories...")
    for mem in memories:
        store.add_memory(mem, metadata={"source": "test"})
        
    # 3. Test Search
    query = "decisions about privacy and surveillance"
    print(f"\n🔹 Searching for: '{query}'")
    
    results = store.search(query, top_k=1)
    
    if results:
        top_doc, score = results[0]
        print(f"   ✅ Found: {top_doc['text']}")
        print(f"      Score: {score:.4f}")
        
        # Verify relevance (simple check)
        if "privacy" in top_doc["text"]:
            print("   ✅ Result is relevant")
        else:
            print("   ❌ Result might be irrelevant")
    else:
        print("   ❌ No results found")
        
    # 4. Test Entity Recall
    entity_model = Entity(name="TestBot", type=EntityType.SEEKER, reputation=1.0, primary_focus="U", bias_description="None")
    entity = MockEntity(entity_model, vector_store=store)
    
    print("\n🔹 Testing Entity Recall...")
    recall = entity.recall_memories("water system", limit=1)
    print(f"   Recall Output:\n{recall}")
    
    if "water purification" in recall:
        print("   ✅ Entity successfully recalled memory")
    else:
        print("   ❌ Entity failed to recall memory")

    # Cleanup
    if os.path.exists(storage_path):
        os.remove(storage_path)

if __name__ == "__main__":
    test_vector_memory()

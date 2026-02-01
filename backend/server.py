from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import uvicorn
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.deliberation_engine import DeliberationEngine
from backend.core.models import Proposal, ProposalCategory, ProposalDomain, Decision
from backend.core.models import Entity, EntityType
from backend.entities.guardian import GuardianEntity
from backend.entities.healer import HealerEntity
from backend.entities.arbiter import ArbiterEntity
from backend.core.llm_provider import get_llm_provider, MockLLM

# Use Real LLM Provider (Gemini/Groq)
# Falls back to Mock only if API keys are missing
llm_provider = get_llm_provider()

app = FastAPI(title="Orbis Ethica API", version="2.0.0")

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Engine
from uuid import uuid4

# Create Entity Models (Configuration)
guardian_config = Entity(
    id=uuid4(), 
    name="Guardian", 
    type=EntityType.GUARDIAN, 
    primary_focus="Rules & Duty", 
    reputation=0.8,
    bias_description="Strict adherence to rules"
)
healer_config = Entity(
    id=uuid4(), 
    name="Healer", 
    type=EntityType.HEALER, 
    primary_focus="Well-being", 
    reputation=0.8,
    bias_description="Prioritizes care over efficiency"
)
arbiter_config = Entity(
    id=uuid4(), 
    name="Arbiter", 
    type=EntityType.ARBITER, 
    primary_focus="Fairness", 
    reputation=0.9,
    bias_description="Favors stability and precedent"
)

from backend.core.ledger import Ledger
from backend.core.memory import MemoryGraph

# Initialize Core Components
ledger = Ledger()
memory_graph = MemoryGraph(ledger=ledger)

# Instantiate Logic Agents
entities = [
    GuardianEntity(guardian_config, llm_provider=llm_provider),
    HealerEntity(healer_config, llm_provider=llm_provider),
    ArbiterEntity(arbiter_config, llm_provider=llm_provider)
]

engine = DeliberationEngine(entities=entities, memory_graph=memory_graph)

class VerifyRequest(BaseModel):
    action: str
    context: Dict[str, Any] = {}

async def verify_payment(x_orbis_wallet: str = Header(None, alias="X-Orbis-Wallet")):
    """
    💰 PAYWALL: Enforce ETHC payment for verification.
    Cost: 0.1 ETHC per request.
    """
    if not x_orbis_wallet:
        raise HTTPException(status_code=402, detail="Payment Required: Missing X-Orbis-Wallet header.")

    try:
        if not hasattr(engine, 'memory_graph') or not engine.memory_graph:
             raise HTTPException(status_code=500, detail="Engine Memory Graph missing")
             
        ledger = engine.memory_graph.ledger
        if not ledger:
            raise HTTPException(status_code=500, detail="Ledger not available.")

        balance = ledger.get_balance(x_orbis_wallet)
        cost = 0.1
        
        if balance < cost:
            raise HTTPException(status_code=402, detail=f"Insufficient ETHC Balance. Required: {cost}, Available: {balance}")

        success = ledger.record_transaction(
            sender=x_orbis_wallet,
            recipient="system_treasury",
            amount=cost,
            tx_type="transfer",
            description="Verification Fee"
        )
        
        if not success:
             raise HTTPException(status_code=500, detail="Payment Transaction Failed.")
             
        return x_orbis_wallet
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Unexpected Error in verify_payment: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

class DecisionResponse(BaseModel):
    safe: bool
    reason: str
    risk_level: str
    score: float
    breakdown: List[Dict[str, Any]]

@app.post("/api/verify", response_model=DecisionResponse)
async def verify_action(req: VerifyRequest, wallet_id: str = Depends(verify_payment)):
    """
    Verify an action's ethical alignment.
    Requires 0.1 ETHC payment.
    """
    print(f"🔍 [ORBIS] Verifying Action: {req.action} (Paid by {wallet_id})")
    
    # 1. Create Proposal
    proposal = Proposal(
        title=f"Verify Action: {req.action[:50]}...",
        description=f"Action: {req.action}\nContext: {req.context}",
        submitter_id=wallet_id,
        category=ProposalCategory.ROUTINE,
        domain=ProposalDomain.OTHER
    )
    
    # 2. Run Deliberation (Async Generator)
    final_decision_payload = None
    async for event in engine.deliberate_generator(proposal):
        if event["type"] == "final_decision":
            final_decision_payload = event
            
    if not final_decision_payload:
        raise HTTPException(status_code=500, detail="Deliberation failed to produce a verdict.")

    decision_data = final_decision_payload["decision"]
    return DecisionResponse(
        safe=decision_data["outcome"] == "approved",
        reason=decision_data["rationale"],
        risk_level="LOW" if decision_data["weighted_vote"] > 0.8 else "HIGH",
        score=decision_data["weighted_vote"],
        breakdown=[
            {
                "entity": e["entity_type"], 
                "vote": "APPROVE" if e["vote"] > 0 else "REJECT", 
                "reason": f"{e['reasoning'][:30]}..."
            }
            for e in decision_data["entity_evaluations"]
        ]
    )

@app.get("/api/balance/{wallet_id}")
async def get_balance(wallet_id: str):
    """
    Get the ETHC balance for a wallet.
    """
    if not hasattr(engine, 'memory_graph') or not engine.memory_graph:
         raise HTTPException(status_code=500, detail="Engine Memory Graph missing")
         
    ledger = engine.memory_graph.ledger
    if not ledger:
        raise HTTPException(status_code=500, detail="Ledger not available.")

    balance = ledger.get_balance(wallet_id)
    return {"wallet_id": wallet_id, "balance": balance, "currency": "ETHC"}

@app.get("/api/history/{wallet_id}")
async def get_history(wallet_id: str):
    """
    Get transaction history for a wallet.
    """
    if not hasattr(engine, 'memory_graph') or not engine.memory_graph:
         raise HTTPException(status_code=500, detail="Engine Memory Graph missing")
         
    ledger = engine.memory_graph.ledger
    if not ledger:
        raise HTTPException(status_code=500, detail="Ledger not available.")

    # Use the ledger's built-in method which queries the correct DB
    history = ledger.get_transaction_history(wallet_id)
    return history

@app.get("/api/stats")
async def get_stats():
    """
    Get real-time system statistics from the DB.
    """
    if not hasattr(engine, 'memory_graph') or not engine.memory_graph:
         raise HTTPException(status_code=500, detail="Engine Memory Graph missing")
    
    from sqlalchemy import text  # Import text for raw SQL
    ledger = engine.memory_graph.ledger
    session = ledger.db_manager.get_session()
    try:
        # Total Verifications
        result = session.execute(text("SELECT COUNT(*) FROM ledger_entries WHERE description LIKE 'Verification Fee'"))
        total_verifications = result.fetchone()[0]
        
        # Tokens Burned (Fees collected by system_treasury)
        result = session.execute(text("SELECT SUM(amount) FROM ledger_entries WHERE recipient = 'system_treasury'"))
        row = result.fetchone()
        tokens_burned = row[0] if row and row[0] is not None else 0.0
        
        # Safety Score (Placeholder logic as before)
        safety_score = 98.5 # High compliance default
        
        return {
            "total_verifications": total_verifications,
            "safety_score": safety_score,
            "tokens_burned": tokens_burned,
            "active_nodes": 1 # Single Miner
        }
    except Exception as e:
        print(f"❌ Error getting stats: {e}")
        return {
            "total_verifications": 0,
            "safety_score": 0,
            "tokens_burned": 0,
            "active_nodes": 0
        }
    finally:
        session.close()

@app.get("/health")
def health():
    return {"status": "active", "mode": "verification_core"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

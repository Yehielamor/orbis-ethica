import asyncio  # Added for P2P background tasks
import os
import sys
from typing import Any

import uvicorn
import json
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
logging.basicConfig(level=logging.INFO)

from backend.core.deliberation_engine import DeliberationEngine
from backend.core.ledger import Ledger
from backend.core.llm_provider import get_llm_provider
from backend.core.memory import MemoryGraph
from backend.core.models import (
    Entity,
    EntityType,
    Proposal,
    ProposalCategory,
    ProposalDomain,
)

# 👇 NEW: Import the NetworkManager we created
from backend.core.network_manager import NetworkManager
from backend.entities.arbiter import ArbiterEntity
from backend.entities.creator import CreatorEntity
from backend.entities.guardian import GuardianEntity
from backend.entities.healer import HealerEntity
from backend.entities.mediator import MediatorEntity
from backend.entities.seeker import SeekerEntity

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

# StaticFiles moved to end to avoid shadowing API

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

# New entities (Phase II)
seeker_config = Entity(
    id=uuid4(),
    name="Seeker",
    type=EntityType.SEEKER,
    primary_focus="Utility & Knowledge",
    reputation=0.8,
    bias_description="Prioritizes aggregate outcomes over individual rights"
)
mediator_config = Entity(
    id=uuid4(),
    name="Mediator",
    type=EntityType.MEDIATOR,
    primary_focus="Balance & Compromise",
    reputation=0.75,
    bias_description="May dilute strong positions to find middle ground"
)
creator_config = Entity(
    id=uuid4(),
    name="Creator",
    type=EntityType.CREATOR,
    primary_focus="Innovation & Long-term Value",
    reputation=0.7,
    bias_description="May be overly optimistic about speculative solutions"
)

# Initialize Core Components
ledger = Ledger()

# 👇 NEW: P2P Network Initialization
# We assume specific env vars or defaults
my_ip = os.getenv("MY_IP", "127.0.0.1")
# Parse seed nodes (remove empty strings)
seed_nodes_raw = os.getenv("SEED_NODES", "").split(",")
bootstrap_nodes = [node for node in seed_nodes_raw if node]

network_manager = NetworkManager(
    ledger=ledger, 
    my_ip=my_ip, 
    bootstrap_nodes=bootstrap_nodes
)

memory_graph = MemoryGraph(ledger=ledger)

# Instantiate Logic Agents (Full Council - 6 Entities)
entities = [
    GuardianEntity(guardian_config, llm_provider=llm_provider),
    HealerEntity(healer_config, llm_provider=llm_provider),
    ArbiterEntity(arbiter_config, llm_provider=llm_provider),
    SeekerEntity(seeker_config, llm_provider=llm_provider),
    MediatorEntity(mediator_config, llm_provider=llm_provider),
    CreatorEntity(creator_config, llm_provider=llm_provider),
]

engine = DeliberationEngine(
    entities=entities, 
    memory_graph=memory_graph,
    node_manager=network_manager  # 🔌 Wire up the P2P Network for Sharding
)

class VerifyRequest(BaseModel):
    action: str
    context: dict[str, Any] = {}

class DecisionResponse(BaseModel):
    safe: bool
    reason: str
    risk_level: str
    score: float
    breakdown: list[dict[str, Any]]

# 👇 NEW: Startup Event to kick off P2P Discovery
@app.on_event("startup")
async def startup_event():
    """
    Start the P2P background tasks (Discovery & Health Checks)
    """
    print(f"🚀 Server starting on {my_ip}:{os.getenv('PORT', '8000')}")
    print(f"🕸️ Joining Swarm with seeds: {bootstrap_nodes}")
    await network_manager.start()

# --- P2P ENDPOINTS (Satoshi Protocol) ---

@app.get("/api/p2p/peers")
async def get_peers():
    """
    Discovery Endpoint: Share my routing table with others.
    """
    # Return known peers + myself so they can add me
    return network_manager.get_known_peers_urls() + [f"http://{my_ip}:8000"]

@app.post("/api/p2p/receive_block")
async def receive_block_p2p(block_data: dict):
    """
    Gossip Endpoint: Receive a block from a peer, validate, and re-broadcast.
    """
    print(f"📥 [P2P] Received Block {block_data.get('index')} from peer")
    
    # 1. Validate against local ledger
    # FIX: Use correct method name 'validate_block' instead of 'validate_incoming_block'
    if ledger.validate_block(block_data):
        # 2. Add to local chain (Use real method, not the mock add_block)
        if ledger.add_block_from_peer(block_data):
            # 3. 🔥 Gossip: Re-Broadcast to MY peers (Viral Spread)
            asyncio.create_task(network_manager.broadcast_block(block_data)) 
            return {"status": "added_and_gossiped"}
        else:
             print("❌ [P2P] Block addition failed (DB error?)")
             raise HTTPException(status_code=500, detail="Block addition failed")
    
    print("❌ [P2P] Block validation failed")
    raise HTTPException(status_code=400, detail="Invalid Block or Signature")

@app.post("/api/p2p/handshake")
async def handshake(payload: dict):
    """
    Active Peer Registration.
    Peers call this to say 'Hello, add me to your list'.
    """
    peer_url = payload.get("url")
    if peer_url:
        print(f"🤝 [P2P] Handshake received from {peer_url}")
        network_manager.add_peer(peer_url)
        return {"status": "connected", "my_url": network_manager.my_url}
    return {"status": "ignored"}

# --- P2P SHARDING ENDPOINTS (Phase II) ---

@app.post("/api/p2p/shard/process")
async def process_shard_endpoint(shard_data: dict):
    """
    Worker Endpoint: Receives a shard to process.
    Delegates to the Engine's new worker method.
    """
    # Verify shard structure? Engine handles it.
    try:
        result = await engine.process_remote_shard(shard_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/p2p/shard/result")
async def receive_shard_result_endpoint(result_payload: dict):
    """
    Leader Endpoint: Receives a result for a shard I sent out.
    """
    if engine.shard_manager:
        engine.shard_manager.handle_shard_result(result_payload)
        return {"status": "accepted"}
    return {"status": "ignored_no_manager"}


@app.get("/api/mining/info")
async def get_mining_info():
    """
    Get information needed for a miner to mine the next block.
    """
    last_block = ledger.get_latest_block()
    
    # NEW: Fetch pending transactions from DB
    session = ledger.db_manager.get_session()
    pending_txs = []
    try:
        from backend.core.models.sql_models import LedgerEntryModel
        
        # DEBUG: Count all txs
        total_txs = session.query(LedgerEntryModel).count()
        pending_count_check = session.query(LedgerEntryModel).filter(LedgerEntryModel.block_hash == None).count()
        print(f"🐛 [DEBUG] Mining Info: Total TXs={total_txs}, Pending={pending_count_check}")
        
        # Get up to 10 pending txs (Mempool)
        # Assuming block_hash IS NULL means it's pending
        results = session.query(LedgerEntryModel).filter(
            LedgerEntryModel.block_hash == None
        ).limit(10).all()
        
        for tx in results:
            print(f"   -> Found pending tx: {tx.id} ({tx.transaction_type})")
            pending_txs.append({
                "id": str(tx.id), # Use ID as unique handle
                "sender": tx.sender,
                "recipient": tx.recipient,
                "amount": tx.amount,
                "type": tx.transaction_type,
                "description": tx.description,
                "timestamp": tx.timestamp.isoformat()
            })
    except Exception as e:
        print(f"⚠️ Error fetching mempool: {e}")
    finally:
        session.close()

    return {
        "index": last_block.index + 1,
        "previous_hash": last_block.hash,
        "difficulty": 1, # Trivial for MVP
        "transactions": pending_txs
    }

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

@app.post("/api/verify", response_model=DecisionResponse)
async def verify_action(req: VerifyRequest, wallet_id: str = Depends(verify_payment)):
    """
    Verify an action's ethical alignment.
    Requires 0.1 ETHC payment.
    """
    print(f"🔍 [ORBIS] 🔥🔥 HIT verify_action for {req.action[:20]}... ")
    
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
    
    # 3. 🔥 NEW: If successful, Broadcast the resulting Block/Verdict to P2P Swarm
    # (Assuming deliberation_engine handles block creation, but we should ensure it triggers the broadcast)
    # Since engine updates ledger internally, we might need a hook here or just rely on the miner loop.
    # For now, this stays as is, assuming Mining Loop handles the main block creation.
    
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

# 👇 NEW: SSE Streaming Endpoint for Live UI
from fastapi.responses import StreamingResponse

@app.get("/api/verify/stream")
async def stream_verification(action: str, wallet_id: str = Header(None, alias="X-Orbis-Wallet")):
    """
    Server-Sent Events (SSE) endpoint for real-time deliberation updates.
    """
    # 0. Basic Validation
    if not wallet_id:
        # SSE doesn't handle 402 well on connection, but we can send an error event
        async def auth_error():
            yield f"data: {json.dumps({'type': 'error', 'message': 'Payment Required: Connect Wallet'})}\n\n"
        return StreamingResponse(
            auth_error(), 
            media_type="text/event-stream",
            headers={
                "X-Accel-Buffering": "no",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive"
            }
        )

    print(f"📡 [SSE] Starting stream for {wallet_id} - Action: {action[:20]}...")

    # 1. Create Proposal (Same logic as verify_action)
    req_context = "Streaming Verification Request" # Default context/research will fill in
    
    proposal = Proposal(
        title=f"Verify Action: {action[:50]}...",
        description=f"Action: {action}\nContext: {req_context}",
        submitter_id=wallet_id,
        category=ProposalCategory.ROUTINE,
        domain=ProposalDomain.OTHER
    )

    # 2. Generator Wrapper for SSE
    async def event_generator():
        try:
            # Send immediate Keep-Alive to establish connection through Nginx
            yield ": keep-alive\n\n"
            
            # Ensure Payment
            if hasattr(engine, 'memory_graph') and engine.memory_graph.ledger:
                balance = engine.memory_graph.ledger.get_balance(wallet_id)
                if balance < 0.1:
                    yield f"data: {json.dumps({'type': 'error', 'message': 'Insufficient ETHC Balance'})}\n\n"
                    return
                # Record fee
                engine.memory_graph.ledger.record_transaction(
                    sender=wallet_id, recipient="system_treasury", amount=0.1, 
                    tx_type="transfer", description="Verification Fee (Stream)"
                )
            
            # Run Deliberation
            async for event in engine.deliberate_generator(proposal):
                yield f"data: {json.dumps(event)}\n\n"
                
                # If final decision, we are done
                if event["type"] == "final_decision":
                    break
        except Exception as e:
            print(f"❌ [SSE ERROR] Stream failed: {e}")
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'type': 'error', 'message': f'Server Error: {str(e)}'})}\n\n"

    # CRITICAL: Nginx buffering often kills SSE. We must disable it.
    return StreamingResponse(
        event_generator(), 
        media_type="text/event-stream",
        headers={
            "X-Accel-Buffering": "no",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
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

        # Calculate Supply Metrics
        mints = session.execute(text("SELECT SUM(amount) FROM ledger_entries WHERE transaction_type = 'mint'")).fetchone()[0] or 0.0
        perm_burns = session.execute(text("SELECT SUM(amount) FROM ledger_entries WHERE recipient = 'system_burn'")).fetchone()[0] or 0.0
        total_supply = mints - perm_burns

        # Staked
        staked_in = session.execute(text("SELECT SUM(amount) FROM ledger_entries WHERE recipient = 'STAKING_CONTRACT'")).fetchone()[0] or 0.0
        staked_out = session.execute(text("SELECT SUM(amount) FROM ledger_entries WHERE sender = 'STAKING_CONTRACT'")).fetchone()[0] or 0.0
        total_staked = staked_in - staked_out

        # Circulating
        circulating_supply = total_supply - total_staked
        
        safety_score = 98.5 
        
        # 👇 NEW: Include P2P stats
        active_peers = len(network_manager.known_peers)
        
        return {
            "total_verifications": total_verifications,
            "safety_score": safety_score,
            "tokens_burned": tokens_burned,
            "active_nodes": 1 + active_peers, # Me + Peers
            "total_supply": total_supply,
            "circulating_supply": circulating_supply,
            "staked_supply": total_staked
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

# 👇 NEW: Analytics & Treasury Endpoints

@app.get("/api/analytics/charts")
async def get_analytics_charts():
    """
    Get time-series data for dashboard charts.
    Returns:
    - Activity (Verifications per hour)
    - Token Distribution
    """
    if not hasattr(engine, 'memory_graph') or not engine.memory_graph:
         raise HTTPException(status_code=500, detail="Engine Memory Graph missing")
    
    from sqlalchemy import text
    from datetime import datetime, timedelta
    
    ledger = engine.memory_graph.ledger
    session = ledger.db_manager.get_session()
    
    try:
        # 1. Activity Chart (Last 24 Hours)
        # We group by hour. SQLite dependent syntax via strftime.
        # Ensure we cover the last 24h even if empty? 
        # For MVP, we just return what we have.
        
        # Count transactions of type 'transfer' to 'system_treasury' (Verifications)
        # Grouped by hour
        activity_query = text("""
            SELECT 
                strftime('%H:00', timestamp) as hour,
                COUNT(*) as count
            FROM ledger_entries 
            WHERE recipient = 'system_treasury'
            AND timestamp > datetime('now', '-24 hours')
            GROUP BY strftime('%H', timestamp)
            ORDER BY timestamp ASC
        """)
        
        results = session.execute(activity_query).fetchall()
        
        # Format for Chart.js
        labels = []
        data = []
        for r in results:
            labels.append(r[0])
            data.append(r[1])
            
        # 2. Token Distribution (Doughnut)
        # Reuse logic from stats
        # Burned
        burned = session.execute(text("SELECT SUM(amount) FROM ledger_entries WHERE recipient = 'system_treasury'")).fetchone()[0] or 0.0
        # Staked
        staked_in = session.execute(text("SELECT SUM(amount) FROM ledger_entries WHERE recipient = 'STAKING_CONTRACT'")).fetchone()[0] or 0.0
        staked_out = session.execute(text("SELECT SUM(amount) FROM ledger_entries WHERE sender = 'STAKING_CONTRACT'")).fetchone()[0] or 0.0
        total_staked = staked_in - staked_out
        # Minted (Total Supply approx)
        minted = session.execute(text("SELECT SUM(amount) FROM ledger_entries WHERE transaction_type = 'mint'")).fetchone()[0] or 0.0
        
        circulating = minted - burned - total_staked
        
        return {
            "activity": {
                "labels": labels,
                "data": data
            },
            "distribution": {
                "labels": ["Circulating", "Bunded (Fees)", "Staked"],
                "data": [circulating, burned, total_staked]
            }
        }
        
    except Exception as e:
        print(f"❌ Error getting charts: {e}")
        return {"activity": {"labels":[], "data":[]}, "distribution": {"labels":[], "data":[]}}
    finally:
        session.close()

@app.get("/api/treasury/ledger")
async def get_treasury_ledger():
    """
    Get specific transaction history for the System Treasury.
    """
    if not hasattr(engine, 'memory_graph') or not engine.memory_graph:
         raise HTTPException(status_code=500, detail="Engine Memory Graph missing")
         
    ledger = engine.memory_graph.ledger
    # Reuse the existing history logic but force wallet_id
    history = ledger.get_transaction_history("system_treasury")
    return history

@app.get("/health")
def health():
    return {
        "status": "active", 
        "mode": "verification_core",
        "p2p_peers": len(network_manager.known_peers)
    }

# 👇 NEW: Serve Frontend Static Files (Moved to bottom)
from fastapi.staticfiles import StaticFiles
app.mount("/", StaticFiles(directory="frontend", html=True), name="static")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
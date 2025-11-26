"""
Orbis Ethica API - FastAPI server for ethical deliberation.

This module exposes the core Orbis Ethica deliberation engine via REST API.
"""

import os
import json
import asyncio
from typing import List, Dict, Any, Optional
from uuid import uuid4
from fastapi import FastAPI, HTTPException, Body, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv

# Rate Limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Load environment variables
load_dotenv()

# --- IMPORTS ---
from ..core.llm_provider import get_llm_provider
from ..core.deliberation_engine import DeliberationEngine
from ..core.models import Proposal, ProposalCategory, ProposalDomain, Entity, EntityType
from ..memory.graph import MemoryGraph



# --- WebSocket for P2P ---
from ..entities.base import BaseEntity
from ..entities.seeker import SeekerEntity
from ..entities.healer import HealerEntity
from ..entities.guardian import GuardianEntity
from ..entities.mediator import MediatorEntity
from ..entities.creator import CreatorEntity
from ..entities.arbiter import ArbiterEntity

# --- P2P Imports ---
from ..p2p.node_manager import NodeManager
from ..p2p.models import P2PMessage, MessageType, PeerInfo

app = FastAPI(
    title="Orbis Ethica API",
    description="Decentralized Moral Operating System - REST API for ethical deliberation",
    version="0.1.3",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Initialize Rate Limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", "http://localhost:4930", "http://127.0.0.1:4930"],  # Explicitly allow frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

    # 3.5 Authentication Middleware (Phase XVI)
from .auth_middleware import SignatureAuthMiddleware
app.add_middleware(
    SignatureAuthMiddleware,
    protected_paths=[
        "/api/proposals/submit",
        "/api/votes"
    ]
)

@app.get("/api/network/peers")
async def get_network_peers():
    """Get list of all known peers and their status."""
    if not node_manager:
        return []
    return node_manager.get_peers_status()

# --- Global State (Initialized at Startup) ---
llm_provider = None
deliberation_engine = None
memory_graph = None
config_manager = None
burn_protocol = None
knowledge_gateway = None
node_manager = None
sync_manager = None
ENTITY_INSTANCES = []
identity = None # Make identity global

@app.on_event("startup")
async def startup_event():
    """Initialize core components on server startup."""
    global llm_provider, deliberation_engine, memory_graph, ENTITY_INSTANCES, config_manager, burn_protocol, knowledge_gateway, node_manager, identity, sync_manager
    
    print("🚀 Orbis Ethica API: Starting up...")
    
    # 0. Initialize Database (Phase XVII)
    from ..core.database import init_db
    init_db()
    
    # 1. Initialize LLM Provider
    llm_provider = get_llm_provider()
    print(f"   📡 LLM Provider: {llm_provider.__class__.__name__}")
    
    if llm_provider.__class__.__name__ == "MockLLM":
        print("   ⚠️  WARNING: Running in MOCK mode. Set GEMINI_API_KEY for live LLM.")
    
    # 1.5 Initialize Node Identity (Phase IX) - Moved to top for dependency injection
    NODE_ID = os.getenv("NODE_ID", f"node_{os.urandom(4).hex()}")
    KEY_PASSWORD = os.getenv("KEY_PASSWORD")
    
    from ..security.identity import NodeIdentity
    try:
        identity = NodeIdentity(node_id=NODE_ID, password=KEY_PASSWORD)
        print(f"   🔑 Node Identity: {identity.public_key_hex[:16]}...")
    except ValueError as e:
        print(f"❌ FATAL: Failed to load identity: {e}")
        print("   💡 If keys are encrypted, ensure KEY_PASSWORD is set.")
        # We should probably exit here, but raising exception will stop startup
        raise e
    
    # 2. Initialize Ledger (Phase III)
    # 2. Initialize Ledger (Phase XVII)
    from ..core.ledger import Ledger
    ledger = Ledger() # Uses global DatabaseManager
    print(f"   ⛓️  Ledger: Initialized (SQLite Backend)")
    
    # 3. Initialize Memory Graph (with Ledger)
    memory_graph = MemoryGraph(ledger=ledger)
    print(f"   🧠 Memory Graph: Initialized (Connected to Ledger)")
    
    # 3.5 Load Genesis (Phase XVIII)
    ledger.load_genesis()
    
    # 4. Define Entity Models
    entity_models_data = [
        {
            "name": "Seeker Alpha",
            "type": EntityType.SEEKER,
            "reputation": 0.95,
            "primary_focus": "U",
            "bias_description": "May prioritize aggregate outcomes over individual rights"
        },
        {
            "name": "Healer Prime",
            "type": EntityType.HEALER,
            "reputation": 0.98,
            "primary_focus": "L",
            "bias_description": "May be overly cautious, blocking beneficial innovations"
        },
        {
            "name": "Guardian Justice",
            "type": EntityType.GUARDIAN,
            "reputation": 0.90,
            "primary_focus": "R",
            "bias_description": "May be overly rigid about rules and procedures"
        },
        {
            "name": "Mediator Balance",
            "type": EntityType.MEDIATOR,
            "reputation": 0.85,
            "primary_focus": "F",
            "bias_description": "May produce weak compromises"
        },
        {
            "name": "Creator Nova",
            "type": EntityType.CREATOR,
            "reputation": 0.88,
            "primary_focus": "Innovation",
            "bias_description": "May be too speculative"
        },
        {
            "name": "Arbiter Judge",
            "type": EntityType.ARBITER,
            "reputation": 1.00,
            "primary_focus": "Balance",
            "bias_description": "May defer to precedent"
        },
    ]
    
    # 5. Initialize Entities
    ENTITY_CLASS_MAP = {
        EntityType.SEEKER: SeekerEntity,
        EntityType.HEALER: HealerEntity,
        EntityType.GUARDIAN: GuardianEntity,
        EntityType.MEDIATOR: MediatorEntity,
        EntityType.CREATOR: CreatorEntity,
        EntityType.ARBITER: ArbiterEntity,
    }
    
    ENTITY_INSTANCES = []
    for data in entity_models_data:
        entity_model = Entity(**data)
        entity_class = ENTITY_CLASS_MAP[data['type']]
        ENTITY_INSTANCES.append(entity_class(entity_model, llm_provider))
    
    print(f"   👥 Entities Loaded: {len(ENTITY_INSTANCES)}")
    
    # 6. Extract Mediator (4th in list, index 3)
    mediator_instance = ENTITY_INSTANCES[3]
    
    # 7. Initialize Reputation Manager
    from ..security.reputation_manager import ReputationManager
    reputation_manager = ReputationManager()
    print(f"   🛡️  Reputation Manager: Initialized")
    
    # 10. Initialize Config Manager (Phase IV Governance)
    from ..core.config import ConfigManager
    config_manager = ConfigManager()
    print(f"   ⚙️  Config Manager: Initialized (Threshold: {config_manager.get_config().deliberation_threshold})")

    # 2. Initialize P2P Service (Phase XI - True P2P)
    # We use the new Libp2pService instead of the old NodeManager for transport
    from ..p2p.libp2p_service import Libp2pService
    
    # Use a random port or fixed one
    p2p_port = int(os.getenv("P2P_PORT", 0))
    p2p_service = Libp2pService(port=p2p_port)
    p2p_service.start_background()
    
    # Attach to app state for access
    app.state.p2p_service = p2p_service
    
    # Wait a bit for it to initialize (hacky but simple for now)
    await asyncio.sleep(2)
    print(f"   🕸️  Libp2p Node Started: {p2p_service.get_peer_id()}")
    
    # Legacy NodeManager (keeping for now to avoid breaking other parts, but it won't do much)
    # Use the random port we generated above if NODE_PORT is not set
    final_p2p_port = int(os.getenv('NODE_PORT', p2p_port))
    
    node_manager = NodeManager(
        node_id=NODE_ID,
        host=os.getenv("NODE_HOST", "127.0.0.1"),
        port=final_p2p_port,
        seed_nodes=os.getenv("SEED_NODES", "").split(",") if os.getenv("SEED_NODES") else [],
        identity=identity
    )
    # await node_manager.start() # Disable legacy start to avoid confusion? 
    # Actually, keep it for the UI API for now until we fully migrate.
    await node_manager.start()
    print(f"   🌐 P2P Node Manager: Active ({NODE_ID} on {os.getenv('NODE_HOST', '127.0.0.1')}:{final_p2p_port})")
    
    # 4.5 Initialize Sync Manager (Phase XVIII)
    from ..p2p.sync_manager import SyncManager
    sync_manager = SyncManager(ledger=ledger, node_manager=node_manager)
    # asyncio.create_task(sync_manager.start_sync_loop()) # Uncomment to enable active sync
    print(f"   🔄 Sync Manager: Initialized")
    
    # 8. Initialize Deliberation Engine (Updated with ConfigManager)
    # 8. Initialize Deliberation Engine
    deliberation_engine = DeliberationEngine(
        entities=ENTITY_INSTANCES,
        mediator=mediator_instance,
        memory_graph=memory_graph,
        reputation_manager=reputation_manager,
        config_manager=config_manager,
        node_manager=node_manager # Pass P2P Manager
    )
    print(f"   ⚖️  Deliberation Engine: Ready")
    
    # 9. Initialize Burn Protocol (Phase III Automation)
    from ..security.burn.protocol import BurnProtocol
    
    # Create Entity Lookup Map (ID -> Entity Model)
    entity_lookup = {str(e.entity.id): e.entity for e in ENTITY_INSTANCES}
    
    burn_protocol = BurnProtocol(
        reputation_manager=reputation_manager,
        ledger=ledger,
        entity_lookup=entity_lookup
    )
    print(f"   🔥 Burn Protocol: Automated & Armed")
    
    # 10. Initialize Knowledge Gateway (Phase VI.5 Clear Layer)
    from ..knowledge.gateway import KnowledgeGateway
    knowledge_gateway = KnowledgeGateway(verified_sources=["WHO_Secure_Feed", "Reuters_Node", "Orbis_Admin", "Trusted_User"])
    print(f"   🛡️  Knowledge Gateway: Active (Sources: {len(knowledge_gateway.verified_sources)})")

    print("✅ Orbis Ethica API: Startup complete!\n")


# --- Pydantic Models for API ---
class ProposalInput(BaseModel):
    """Input model for submitting a proposal."""
    title: str = Body(..., min_length=10, max_length=200, example="Mandatory Biometric Surveillance for Public Safety")
    description: str = Body(..., min_length=20, example="Implement city-wide facial recognition to reduce crime by 40%. Includes 24/7 monitoring and centralized database.")
    category: str = Body(default="HIGH_IMPACT", example="HIGH_IMPACT")
    domain: str = Body(default="SECURITY", example="SECURITY")
    submitter_id: str = Body(default="API_User", example="DAO_Rep_1")
    affected_parties: List[str] = Body(default=[], example=["Citizens", "Law enforcement", "Privacy advocates"])
    context: Dict[str, Any] = Body(default={}, example={"crime_rate": 0.15, "budget": 10000000})


class ProposalResponse(BaseModel):
    """Response model for deliberation results."""
    proposal_id: str
    status: str
    final_score: float
    threshold: float
    rounds_completed: int
    outcome: str
    verdict_node_id: str
    message: str
    entity_votes: List[Dict[str, Any]]
    refinements_made: List[str] = []  # History of Mediator refinements


# --- KNOWLEDGE ENDPOINTS (Phase VI.5) ---
from ..knowledge.models import RawKnowledge, VerifiedKnowledge

@app.post("/api/knowledge/ingest", response_model=VerifiedKnowledge)
async def ingest_knowledge(raw: RawKnowledge):
    """
    Ingest raw knowledge through the purification gateway.
    Verifies source and signature.
    """
    if not knowledge_gateway:
        raise HTTPException(status_code=503, detail="Knowledge Gateway not initialized")
    
    try:
        verified = knowledge_gateway.process_knowledge(raw)
        
        # Store in Memory Graph as KNOWLEDGE node
        if memory_graph:
            memory_graph.add_node(
                type="KNOWLEDGE",
                content={
                    "text": verified.content,
                    "source": verified.source_id,
                    "purity": verified.purity_score
                },
                agent_id="KnowledgeGateway"
            )
            
        return verified
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class ChallengeRequest(BaseModel):
    source_id: str

@app.post("/api/knowledge/challenge")
async def request_challenge(req: ChallengeRequest):
    """
    Step 1: Request a cryptographic challenge (nonce).
    """
    if not knowledge_gateway:
        raise HTTPException(status_code=503, detail="Gateway not initialized")
    
    try:
        nonce = knowledge_gateway.create_challenge(req.source_id)
        return {"nonce": nonce}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class SignRequest(BaseModel):
    content: str # In this case, the content to sign is the NONCE

@app.post("/api/knowledge/sign")
async def sign_content(req: SignRequest):
    """
    Helper endpoint to generate a valid mock signature for testing.
    In production, this would NOT exist (signatures come from client).
    """
    # Mock signature logic: "SIG_" + content (where content is the nonce)
    signature = f"SIG_{req.content}"
    return {"signature": signature}


# --- P2P WEBSOCKET ENDPOINT ---
@app.websocket("/ws/p2p")
async def p2p_websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for P2P communication.
    Handles incoming connections from other nodes.
    """
    await websocket.accept()
    peer_id = None
    try:
        # 1. Handshake: Wait for HELLO message
        data = await websocket.receive_text()
        message = P2PMessage.parse_raw(data)
        
        if message.type == MessageType.HANDSHAKE:
            peer_id = message.sender_id
            peer_info = PeerInfo(**message.payload)
            
            # Register peer
            if node_manager:
                node_manager.add_peer(peer_info)
                node_manager.active_connections[peer_id] = websocket
            
            # Send ACK
            ack_msg = P2PMessage(
                type=MessageType.HANDSHAKE_ACK,
                sender_id=node_manager.node_id if node_manager else "UNKNOWN",
                payload={"status": "connected", "node_id": node_manager.node_id if node_manager else "UNKNOWN"}
            )
            await websocket.send_text(ack_msg.json())
            print(f"✅ P2P Handshake successful with {peer_id}")
            
            # 2. Main Loop
            while True:
                data = await websocket.receive_text()
                msg = P2PMessage.parse_raw(data)
                
                # Deduplicate
                msg_hash = f"{msg.sender_id}:{msg.timestamp}:{msg.type}"
                if node_manager and msg_hash in node_manager.seen_messages:
                    continue
                if node_manager:
                    node_manager.seen_messages.add(msg_hash)
                
                print(f"📩 Received {msg.type} from {msg.sender_id}")
                
                if msg.type == MessageType.GOSSIP_TX:
                    # Received a new proposal from a peer
                    proposal_data = msg.payload
                    print(f"   💡 New Proposal Gossip: {proposal_data.get('title', 'Unknown')}")
                    # TODO: Add to Mempool / Validate
                    
                    # Re-broadcast to other peers (Flood)
                    if node_manager:
                        await node_manager.broadcast(msg)
                        
                elif msg.type == MessageType.GOSSIP_BLOCK:
                    # Received a new block
                    block_data = msg.payload
                    print(f"   🧱 New Block Gossip: Height {block_data.get('index')}")
                    
                    if memory_graph and memory_graph.ledger:
                        # Attempt to add block
                        success = memory_graph.ledger.add_block_from_peer(block_data)
                        
                        if success:
                            # Re-broadcast only if valid and new
                            if node_manager:
                                await node_manager.broadcast(msg)
                        else:
                            # If failed, it might be a fork or we are behind.
                            # TODO: Implement Sync Request if index > local_height + 1
                            pass
                
    except WebSocketDisconnect:
        print(f"❌ P2P Connection closed: {peer_id}")
        if node_manager and peer_id:
            node_manager.remove_peer(peer_id)
            if peer_id in node_manager.active_connections:
                del node_manager.active_connections[peer_id]
    except Exception as e:
        print(f"❌ P2P Error: {e}")
        await websocket.close()


# --- API Endpoints ---

@app.get("/")
async def root():
    return {
        "message": "Orbis Ethica API v0.1.3",
        "docs": "/docs",
        "endpoints": [
            "/api/deliberate",
            "/api/proposals/submit",
            "/api/entities",
            "/api/governance/config",
            "/api/ledger",
            "/api/memory/search"
        ]
    }

# --- LEDGER ENDPOINTS ---

class StakeRequest(BaseModel):
    amount: float

@app.get("/api/wallet")
def get_wallet_info():
    """Get current node's wallet status."""
    if not memory_graph or not memory_graph.ledger:
        raise HTTPException(status_code=503, detail="Ledger not initialized")
    
    ledger = memory_graph.ledger
    # Use global identity
    my_address = identity.public_key_hex if identity else "genesis_wallet"
    
    return {
        "address": my_address,
        "liquid_balance": ledger.get_balance(my_address),
        "staked_balance": 0.0, # Staking not yet migrated to DB
        "is_validator": False
    }

@app.post("/api/wallet/stake")
def stake_tokens(req: StakeRequest):
    """Stake tokens to become a validator."""
    if not memory_graph or not memory_graph.ledger:
        raise HTTPException(status_code=503, detail="Ledger not initialized")
        
    ledger = memory_graph.ledger
    my_address = ledger.identity.public_key_hex if ledger.identity else "genesis_wallet"
    
    # Create STAKE transaction
    from ..core.ledger import TokenTransaction, TransactionType
    
    tx = TokenTransaction(
        id=f"stake_{uuid4().hex[:8]}",
        type=TransactionType.STAKE,
        sender=my_address,
        receiver="STAKING_CONTRACT",
        amount=req.amount,
        signature="simulated_sig" # In real app, sign with private key
    )
    
    if ledger.add_block(data={"msg": "Staking Request"}, transactions=[tx]):
        return {"status": "success", "new_stake": ledger.get_stake_balance(my_address)}
    else:
        raise HTTPException(status_code=400, detail="Staking failed (Insufficient funds?)")

@app.post("/api/wallet/unstake")
def unstake_tokens(req: StakeRequest):
    """Unstake tokens."""
    if not memory_graph or not memory_graph.ledger:
        raise HTTPException(status_code=503, detail="Ledger not initialized")
        
    ledger = memory_graph.ledger
    my_address = ledger.identity.public_key_hex if ledger.identity else "genesis_wallet"
    
    # Create UNSTAKE transaction
    from ..core.ledger import TokenTransaction, TransactionType
    
    tx = TokenTransaction(
        id=f"unstake_{uuid4().hex[:8]}",
        type=TransactionType.UNSTAKE,
        sender=my_address,
        receiver="STAKING_CONTRACT", # Receiver doesn't matter much for unstake logic
        amount=req.amount,
        signature="simulated_sig"
    )
    
    if ledger.add_block(data={"msg": "Unstaking Request"}, transactions=[tx]):
        return {"status": "success", "new_stake": ledger.get_stake_balance(my_address)}
    else:
        raise HTTPException(status_code=400, detail="Unstaking failed (Insufficient stake?)")


# --- MEMORY ENDPOINTS ---
class SearchQuery(BaseModel):
    query: str
    limit: int = 5

@app.post("/api/memory/search")
async def search_memory(query: SearchQuery):
    """Semantic search in the vector memory."""
    if not memory_graph:
        raise HTTPException(status_code=503, detail="Memory graph not initialized")
    
    try:
        results = memory_graph.vector_store.search(query.query, top_k=query.limit)
        
        return {
            "results": [
                {"text": doc.get("text", ""), "score": score, "metadata": doc.get("metadata", {})}
                for doc, score in results
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Memory search failed: {str(e)}")


@app.get("/api/status")
def get_status():
    """Returns the current health status and component readiness."""
    return {
        "status": "Operational" if deliberation_engine else "Initializing",
        "api_version": app.version,
        "components": {
            "llm_provider": llm_provider.__class__.__name__ if llm_provider else "Not initialized",
            "entities_loaded": len(ENTITY_INSTANCES),
            "deliberation_engine": "Ready" if deliberation_engine else "Not initialized",
            "memory_graph": "Active" if memory_graph else "Not initialized",
            "ledger": "Active" if memory_graph and memory_graph.ledger else "Not initialized",
            "config_manager": "Active" if config_manager else "Not initialized"
        }
    }


@app.get("/api/entities")
def get_entities():
    """Returns information about all loaded entities."""
    if not ENTITY_INSTANCES:
        raise HTTPException(status_code=503, detail="Entities not yet initialized")
    
    entities_info = []
    for entity_obj in ENTITY_INSTANCES:
        entities_info.append({
            "id": str(entity_obj.entity.id),
            "name": entity_obj.entity.name,
            "type": entity_obj.entity.type.value,
            "reputation": entity_obj.entity.reputation,
            "primary_focus": entity_obj.entity.primary_focus,
            "bias": entity_obj.entity.bias_description,
            "decisions_participated": entity_obj.entity.decisions_participated
        })
    
    return {
        "total_entities": len(entities_info),
        "entities": entities_info
    }


@app.get("/api/ledger")
def get_ledger():
    """Returns the full ledger transaction history."""
    if not memory_graph or not memory_graph.ledger:
        raise HTTPException(status_code=503, detail="Ledger not initialized")
    
    # New SQLite Ledger returns transactions, not blocks
    history = memory_graph.ledger.get_transaction_history()
    return {
        "count": len(history),
        "transactions": history
    }

@app.get("/api/governance/config")
def get_governance_config():
    """Returns the current system configuration."""
    if not config_manager:
        raise HTTPException(status_code=503, detail="Config Manager not initialized")
    
    try:
        return config_manager.get_config().model_dump()
    except Exception as e:
        print(f"❌ Error in get_governance_config: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


class BurnRequest(BaseModel):
    entity_id: str
    reason: str
    council_vote: float = 1.0

@app.post("/api/security/burn")
def trigger_burn(request: BurnRequest):
    """
    [ADMIN] Manually trigger the Burn Protocol for an entity.
    """
    if not burn_protocol:
        raise HTTPException(status_code=503, detail="Burn Protocol not initialized")
    
    try:
        from ..security.burn.models import BurnOffenseType
        
        event = burn_protocol.execute_burn(
            perpetrator_id=request.entity_id,
            offense=BurnOffenseType.SIGNATURE_MISMATCH,
            description=request.reason,
            evidence={"manual_trigger": True, "admin_user": "API_TEST"},
            council_vote=request.council_vote
        )
        
        return {
            "status": "BURN_EXECUTED",
            "event_id": event.id,
            "perpetrator": request.entity_id,
            "reputation_now": 0.0,
            "ledger_block": "Check /api/ledger"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/proposals/submit")
@limiter.limit("5/minute")
async def submit_proposal(request: Request, proposal_input: ProposalInput):
    """
    Submits a new proposal and runs the full deliberation protocol with real-time streaming.
    Returns a Server-Sent Events (SSE) stream.
    """
    # Validate input
    if not deliberation_engine:
        raise HTTPException(
            status_code=503,
            detail="Deliberation Engine not initialized. Please check server logs."
        )
    
    try:
        # 1. Create Proposal Object
        proposal = Proposal(
            title=proposal_input.title,
            description=proposal_input.description,
            category=ProposalCategory(proposal_input.category.lower()),
            domain=ProposalDomain(proposal_input.domain.lower()) if proposal_input.domain else ProposalDomain.OTHER,
            affected_parties=proposal_input.affected_parties,
            context=proposal_input.context
        )
        
        proposal.submit(submitter_id=proposal_input.submitter_id)
        
        print(f"\n🚀 API: Streaming deliberation for proposal: {proposal.title}")
        
        # --- P2P BROADCAST (Phase VIII) ---
        if node_manager:
            asyncio.create_task(node_manager.broadcast(
                P2PMessage(
                    type=MessageType.GOSSIP_TX,
                    sender_id=node_manager.node_id,
                    payload=proposal.to_dict()
                )
            ))
        
        # 2. Define SSE Generator
        async def sse_generator():
            try:
                # Use the generator from the engine
                # FastAPI runs sync iterators in a threadpool, so this won't block the event loop
                generator = deliberation_engine.deliberate_generator(
                    proposal=proposal,
                    submitter_id=proposal.submitter_id
                )
                
                async for event in generator:
                    # Format as SSE
                    yield f"data: {json.dumps(event)}\n\n"
                    
            except Exception as e:
                print(f"❌ STREAM ERROR: {e}")
                error_event = {"type": "error", "message": str(e)}
                yield f"data: {json.dumps(error_event)}\n\n"

        # 3. Return Streaming Response
        return StreamingResponse(sse_generator(), media_type="text/event-stream")
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(e)}")
    except Exception as e:
        print(f"❌ API ERROR: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Deliberation failed: {str(e)}"
        )


@app.get("/api/memory/export")
def export_memory():
    """Exports the current memory graph."""
    if not memory_graph:
        raise HTTPException(status_code=503, detail="Memory graph not initialized")
    
    try:
        memory_graph.export_to_json("memory_graph_export.json")
        return {
            "status": "Success",
            "message": "Memory graph exported to memory_graph_export.json",
            "total_nodes": len(memory_graph.nodes)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


# --- Health Check ---
@app.get("/health")
def health_check():
    """Simple health check endpoint."""
    return {"status": "healthy"}


# NOTE: To run this server:
# cd backend
# uvicorn api.app:app --reload --host 0.0.0.0 --port 8000
#
# Then visit: http://localhost:8000/api/docs for interactive API documentation

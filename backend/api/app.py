"""
Orbis Ethica API - FastAPI server for ethical deliberation.

This module exposes the core Orbis Ethica deliberation engine via REST API.
"""

import os
import json
import asyncio
from typing import List, Dict, Any, Optional
from uuid import uuid4
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- Import Core Components ---
from ..core.llm_provider import get_llm_provider
from ..core.deliberation_engine import DeliberationEngine
from ..core.models import Proposal, ProposalCategory, ProposalDomain, Entity, EntityType
from ..memory.graph import MemoryGraph

# --- Entity Imports ---
from ..entities.base import BaseEntity
from ..entities.seeker import SeekerEntity
from ..entities.healer import HealerEntity
from ..entities.guardian import GuardianEntity
from ..entities.mediator import MediatorEntity
from ..entities.creator import CreatorEntity
from ..entities.arbiter import ArbiterEntity

app = FastAPI(
    title="Orbis Ethica API",
    description="Decentralized Moral Operating System - REST API for ethical deliberation",
    version="0.1.1-alpha",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Global State (Initialized at Startup) ---
llm_provider = None
deliberation_engine = None
memory_graph = None
ENTITY_INSTANCES = []


@app.on_event("startup")
async def startup_event():
    """Initialize core components on server startup."""
    global llm_provider, deliberation_engine, memory_graph, ENTITY_INSTANCES
    
    print("🚀 Orbis Ethica API: Starting up...")
    
    # 1. Initialize LLM Provider
    llm_provider = get_llm_provider()
    print(f"   📡 LLM Provider: {llm_provider.__class__.__name__}")
    
    if llm_provider.__class__.__name__ == "MockLLM":
        print("   ⚠️  WARNING: Running in MOCK mode. Set GEMINI_API_KEY for live LLM.")
    
    # 2. Initialize Ledger (Phase III)
    from ..core.ledger import LocalBlockchain
    ledger = LocalBlockchain()
    print(f"   ⛓️  Ledger: Initialized (Genesis Block: {ledger.get_latest_block().hash[:8]}...)")

    # 3. Initialize Memory Graph (with Ledger)
    memory_graph = MemoryGraph(ledger=ledger)
    print(f"   🧠 Memory Graph: Initialized (Connected to Ledger)")
    
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
    
    # 8. Initialize Deliberation Engine (Updated with ConfigManager)
    deliberation_engine = DeliberationEngine(
        entities=ENTITY_INSTANCES,
        mediator=mediator_instance,
        memory_graph=memory_graph,
        reputation_manager=reputation_manager,
        config_manager=config_manager
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


# --- API Endpoints ---

@app.get("/")
def read_root():
    """Root endpoint - API information."""
    return {
        "name": "Orbis Ethica API",
        "version": app.version,
        "description": "Decentralized Moral Operating System",
        "endpoints": {
            "status": "/api/status",
            "docs": "/api/docs",
            "submit_proposal": "/api/proposals/submit",
            "entities": "/api/entities",
            "ledger": "/api/ledger",
            "governance": "/api/governance/config"
        }
    }


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
    """Returns the full blockchain ledger."""
    if not memory_graph or not memory_graph.ledger:
        raise HTTPException(status_code=503, detail="Ledger not initialized")
    
    chain = memory_graph.ledger.get_chain()
    return {
        "height": len(chain),
        "blocks": [block.model_dump() for block in chain]
    }

@app.get("/api/governance/config")
def get_governance_config():
    """Returns the current system configuration."""
    if not config_manager:
        raise HTTPException(status_code=503, detail="Config Manager not initialized")
    
    return config_manager.get_config().model_dump()


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
async def submit_proposal(proposal_input: ProposalInput):
    """
    Submits a new proposal and runs the full deliberation protocol with real-time streaming.
    Returns a Server-Sent Events (SSE) stream.
    """
    if not deliberation_engine:
        raise HTTPException(
            status_code=503,
            detail="Deliberation engine not initialized. Please wait for startup to complete."
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
        
        # 2. Define SSE Generator
        def sse_generator():
            try:
                # Use the generator from the engine
                # FastAPI runs sync iterators in a threadpool, so this won't block the event loop
                generator = deliberation_engine.deliberate_generator(
                    proposal=proposal,
                    submitter_id=proposal.submitter_id
                )
                
                for event in generator:
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

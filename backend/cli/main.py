#!/usr/bin/env python3
"""
Orbis Ethica CLI - Phase I Interface

Usage:
    python -m cli.main submit "Your proposal title" --description "Details..."
    python -m cli.main evaluate <proposal_id>
    python -m cli.main list
"""

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from datetime import datetime
from uuid import UUID

from ..core.models import (
    Proposal, ProposalCategory, ProposalDomain,
    Entity, EntityType
)
from ..entities import SeekerEntity, GuardianEntity, ArbiterEntity
from ..core.models.entity import PHASE_I_ENTITIES
from ..core.protocols import DeliberationEngine

console = Console()


# Initialize Phase I entities
def init_entities():
    """Initialize the 3 Phase I entities."""
    entities = []
    
    for entity_config in PHASE_I_ENTITIES:
        if entity_config.type == EntityType.SEEKER:
            entities.append(SeekerEntity(entity_config))
        elif entity_config.type == EntityType.GUARDIAN:
            entities.append(GuardianEntity(entity_config))
        elif entity_config.type == EntityType.ARBITER:
            entities.append(ArbiterEntity(entity_config))
    
    return entities


@click.group()
def cli():
    """Orbis Ethica - A Moral Operating System for AGI"""
    pass


@cli.command()
@click.argument('title')
@click.option('--description', '-d', required=True, help='Detailed proposal description')
@click.option('--category', '-c', 
              type=click.Choice(['routine', 'high_impact', 'constitutional', 'emergency']),
              default='routine',
              help='Proposal category')
@click.option('--domain', 
              type=click.Choice(['healthcare', 'finance', 'education', 'technology', 'other']),
              default='other',
              help='Proposal domain')
def submit(title, description, category, domain):
    """Submit a new proposal for ethical evaluation."""
    
    console.print("\n[bold cyan]Orbis Ethica - Submitting Proposal[/bold cyan]\n")
    
    # Create proposal
    proposal = Proposal(
        title=title,
        description=description,
        category=ProposalCategory(category),
        domain=ProposalDomain(domain)
    )
    
    console.print(Panel(
        f"[bold]Title:[/bold] {proposal.title}\n"
        f"[bold]Category:[/bold] {proposal.category.value}\n"
        f"[bold]Domain:[/bold] {proposal.domain.value}\n"
        f"[bold]Threshold:[/bold] {proposal.threshold_required:.2f}",
        title="Proposal Details",
        border_style="cyan"
    ))
    
    # Initialize entities
    console.print("\n[yellow]Initializing cognitive entities...[/yellow]")
    try:
        entities = init_entities()
        console.print(f"[green]✓[/green] Loaded {len(entities)} entities: Seeker, Guardian, Arbiter\n")
    except Exception as e:
        console.print(f"[red]✗ Error initializing entities: {e}[/red]")
        console.print("[yellow]Make sure OPENAI_API_KEY and ANTHROPIC_API_KEY are set in .env[/yellow]")
        return
    
    # Run deliberation
    console.print("[yellow]Starting deliberation process...[/yellow]\n")
    
    try:
        engine = DeliberationEngine(entities)
        decision = engine.deliberate(proposal, submitter_id="cli_user")
        
        # Print detailed report
        engine.print_detailed_report(decision)
        
        # Save decision (in real implementation, save to database)
        console.print(f"\n[green]Decision saved with ID: {decision.id}[/green]")
        
    except Exception as e:
        console.print(f"\n[red]✗ Error during deliberation: {e}[/red]")
        import traceback
        console.print(traceback.format_exc())


@cli.command()
def demo():
    """Run a demo proposal (hospital triage scenario)."""
    
    console.print("\n[bold cyan]Orbis Ethica - Demo: Hospital Resource Allocation[/bold cyan]\n")
    
    # Create demo proposal
    proposal = Proposal(
        title="AI-Assisted Hospital ICU Bed Allocation During Pandemic",
        description="""
Allocate 200 ICU beds among 450 patients during a pandemic surge using AI-assisted triage.

Proposed allocation criteria:
- 35% survival probability (based on medical assessment)
- 25% life-years saved (age and health factors)
- 20% severity of condition (immediate need)
- 10% time on waitlist (fairness consideration)
- 10% healthcare worker status (essential workers priority)

Expected outcomes:
- Survival rate: 174 patients (vs 142 with random allocation)
- Fairness (Gini coefficient): 0.44

Safeguards:
- Weekly ethics review by hospital committee
- Public appeals process for disputed cases
- Quarterly audit of outcomes by demographic distribution
- Human override available for edge cases

Concerns to address:
- Age-based discrimination (elderly systematically deprioritized)
- Healthcare worker definition unclear
- No explicit cap on age penalties
        """.strip(),
        category=ProposalCategory.HIGH_IMPACT,
        domain=ProposalDomain.HEALTHCARE,
        affected_parties=[
            "ICU patients",
            "Healthcare workers",
            "Hospital administrators",
            "Elderly population",
            "General public"
        ]
    )
    
    console.print(Panel(
        f"[bold]Scenario:[/bold] Hospital Resource Allocation\n"
        f"[bold]Category:[/bold] {proposal.category.value}\n"
        f"[bold]Threshold Required:[/bold] {proposal.threshold_required:.2f}\n"
        f"[bold]Affected Parties:[/bold] {len(proposal.affected_parties)}",
        title="Demo Proposal",
        border_style="cyan"
    ))
    
    # Initialize entities
    console.print("\n[yellow]Initializing cognitive entities...[/yellow]")
    try:
        entities = init_entities()
        console.print(f"[green]✓[/green] Loaded {len(entities)} entities\n")
    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")
        console.print("[yellow]Make sure API keys are configured in backend/.env[/yellow]")
        return
    
    # Run deliberation
    console.print("[yellow]Starting deliberation...[/yellow]\n")
    
    try:
        engine = DeliberationEngine(entities, max_rounds=3)
        decision = engine.deliberate(proposal, submitter_id="demo")
        
        # Print report
        engine.print_detailed_report(decision)
        
    except Exception as e:
        console.print(f"\n[red]✗ Error: {e}[/red]")
        import traceback
        console.print(traceback.format_exc())


@cli.command()
def test():
    """Test entity initialization and basic functionality."""
    
    console.print("\n[bold cyan]Orbis Ethica - System Test[/bold cyan]\n")
    
    # Test 1: Entity initialization
    console.print("[yellow]Test 1: Entity Initialization[/yellow]")
    try:
        entities = init_entities()
        console.print(f"[green]✓[/green] Successfully initialized {len(entities)} entities")
        
        for entity in entities:
            console.print(f"  - {entity.entity.name} ({entity.entity.type.value})")
        
    except Exception as e:
        console.print(f"[red]✗[/red] Failed: {e}")
        return
    
    # Test 2: Simple proposal
    console.print("\n[yellow]Test 2: Simple Proposal Evaluation[/yellow]")
    try:
        proposal = Proposal(
            title="Test Proposal: Implement AI Safety Monitoring",
            description="Deploy automated monitoring system for AI safety violations.",
            category=ProposalCategory.ROUTINE,
            domain=ProposalDomain.TECHNOLOGY
        )
        
        console.print(f"[green]✓[/green] Created test proposal")
        console.print(f"  Threshold: {proposal.threshold_required:.2f}")
        
    except Exception as e:
        console.print(f"[red]✗[/red] Failed: {e}")
        return
    
    # Test 3: Single entity evaluation
    console.print("\n[yellow]Test 3: Single Entity Evaluation[/yellow]")
    try:
        seeker = entities[0]
        console.print(f"  Testing with {seeker.entity.name}...")
        
        evaluation = seeker.evaluate_proposal(proposal)
        
        console.print(f"[green]✓[/green] Evaluation complete")
        console.print(f"  Vote: {evaluation.vote}")
        console.print(f"  Confidence: {evaluation.confidence:.2f}")
        console.print(f"  ULFR: U={evaluation.ulfr_score.utility:.2f}, "
                     f"L={evaluation.ulfr_score.life:.2f}")
        
    except Exception as e:
        console.print(f"[red]✗[/red] Failed: {e}")
        import traceback
        console.print(traceback.format_exc())
        return
    
    console.print("\n[green]All tests passed![/green]\n")


@cli.command()
def info():
    """Display system information."""
    
    console.print("\n[bold cyan]Orbis Ethica - System Information[/bold cyan]\n")
    
    # System info
    info_table = Table(title="Configuration")
    info_table.add_column("Parameter", style="cyan")
    info_table.add_column("Value", style="green")
    
    info_table.add_row("Phase", "I - Proof of Concept")
    info_table.add_row("Entities", "3 (Seeker, Guardian, Arbiter)")
    info_table.add_row("Max Rounds", "4")
    info_table.add_row("Quorum", "60%")
    info_table.add_row("Thresholds", "Routine: 0.50, High-Impact: 0.70, Constitutional: 0.85")
    
    console.print(info_table)
    
    # Entity info
    console.print("\n")
    entity_table = Table(title="Cognitive Entities")
    entity_table.add_column("Entity", style="cyan")
    entity_table.add_column("Focus", style="yellow")
    entity_table.add_column("Primary Question", style="green")
    
    entity_table.add_row(
        "Seeker",
        "Utility Maximization",
        "What generates the most good?"
    )
    entity_table.add_row(
        "Guardian",
        "Rights Protection",
        "Does this respect fundamental rights?"
    )
    entity_table.add_row(
        "Arbiter",
        "Final Judgment",
        "What will future generations respect?"
    )
    
    console.print(entity_table)
    console.print()


if __name__ == '__main__':
    cli()

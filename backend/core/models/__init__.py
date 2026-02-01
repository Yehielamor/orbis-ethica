"""Core models for Orbis Ethica."""

from .decision import Decision, DecisionOutcome
from .entity import Entity, EntityType, EntityVote
from .proposal import Proposal, ProposalCategory, ProposalDomain, ProposalStatus
from .ulfr import ULFRScore, ULFRWeights

__all__ = [
    "ULFRScore",
    "ULFRWeights",
    "Proposal",
    "ProposalStatus",
    "ProposalCategory",
    "ProposalDomain",
    "Decision",
    "DecisionOutcome",
    "Entity",
    "EntityType",
    "EntityVote",
]

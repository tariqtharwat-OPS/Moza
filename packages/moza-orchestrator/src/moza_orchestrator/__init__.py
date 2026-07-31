"""
Moza Orchestrator - Multi-Provider Failover System

A smart routing layer that sits between the user and 7 AI providers with 19 ranked models.
Provides transparent failover for rate limits, auth errors, quality issues.
"""

from .orchestrator import MozaOrchestrator, FailoverError

__version__ = "1.0.0"
__all__ = ["MozaOrchestrator", "FailoverError"]
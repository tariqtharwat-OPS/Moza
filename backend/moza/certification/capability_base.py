from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum


class MaturityLevel(Enum):
    NOT_IMPLEMENTED = 0
    BASIC = 1
    ERROR_HANDLING = 2
    REALISTIC = 3
    PRODUCTION_READY = 4
    TRUSTED_AUTONOMY = 5


@dataclass
class CertificationResult:
    capability_name: str
    maturity_level: MaturityLevel
    confidence_score: float  # 0-100%
    tests_passed: int
    tests_failed: int
    evidence_files: List[str]
    definition_of_done_met: bool


class Capability(ABC):
    def __init__(self, name: str, purpose: str, user_story: str):
        self.name = name
        self.purpose = purpose
        self.user_story = user_story
        self.maturity_level = MaturityLevel.NOT_IMPLEMENTED
        self.confidence_score = 0.0

    @abstractmethod
    async def certify(self) -> CertificationResult:
        """Run certification and return result"""
        pass

    @abstractmethod
    def get_definition_of_done(self) -> List[str]:
        """Return list of DoD criteria"""
        pass

    @abstractmethod
    def get_forbidden_behaviors(self) -> List[str]:
        """Return list of forbidden behaviors"""
        pass

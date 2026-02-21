from dataclasses import dataclass
from typing import List, Protocol, runtime_checkable, Dict, Any, Optional

from modules.government.dtos import (
    FiscalPolicyDTO,
    MonetaryPolicyDTO,
    GovernmentStateDTO,
    PolicyDecisionDTO,
    ExecutionResultDTO,
    MacroEconomicSnapshotDTO,
    WelfareResultDTO,
    BailoutResultDTO,
    TaxCollectionResultDTO,
    FiscalContextDTO,
    BondIssueRequestDTO,
    BondIssuanceResultDTO,
    IAgent,
    TaxBracketDTO
)
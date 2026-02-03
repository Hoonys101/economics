from typing import List, Any, Optional, TYPE_CHECKING
import logging
from simulation.models import Transaction
from modules.government.constants import DEFAULT_INFRASTRUCTURE_INVESTMENT_COST
from modules.system.api import DEFAULT_CURRENCY

if TYPE_CHECKING:
    from simulation.agents.government import Government

logger = logging.getLogger(__name__)

class InfrastructureManager:
    def __init__(self, government: 'Government'):
        self.government = government
        self.config = government.config_module

    def invest_infrastructure(self, current_tick: int, households: List[Any] = None) -> List[Transaction]:
        """
        Refactored: Returns transactions instead of executing direct transfers.
        Side-effects (TFP Boost) are deferred via metadata.
        NOW DISTRIBUTES DIRECTLY TO HOUSEHOLDS (Public Works).
        """
        transactions = []
        if self.config:
            cost = getattr(self.config, "INFRASTRUCTURE_INVESTMENT_COST", DEFAULT_INFRASTRUCTURE_INVESTMENT_COST)
        else:
            cost = DEFAULT_INFRASTRUCTURE_INVESTMENT_COST

        effective_cost = cost

        if self.government.firm_subsidy_budget_multiplier < 0.8:
            return []

        # Synchronous Financing (WO-117)
        current_assets_raw = self.government.assets
        current_assets = current_assets_raw
        if isinstance(current_assets_raw, dict):
            current_assets = current_assets_raw.get(DEFAULT_CURRENCY, 0.0)

        if current_assets < effective_cost:
            needed = effective_cost - current_assets
            # Use new synchronous method
            if hasattr(self.government.finance_system, 'issue_treasury_bonds_synchronous'):
                success, bond_txs = self.government.finance_system.issue_treasury_bonds_synchronous(self.government, needed, current_tick)
                if not success:
                     logger.warning(f"BOND_ISSUANCE_FAILED | Failed to raise {needed:.2f} for infrastructure.")
                     return []
                transactions.extend(bond_txs)
            else:
                # Fallback to old behavior (should not happen if system is updated)
                bonds, txs = self.government.finance_system.issue_treasury_bonds(needed, current_tick)
                if not bonds:
                    logger.warning(f"BOND_ISSUANCE_FAILED | Failed to raise {needed:.2f} for infrastructure.")
                    return []
                transactions.extend(txs)

        # Distribute as Labor Income (Public Works)
        if not households:
             logger.warning("INFRASTRUCTURE_ABORTED | No households provided for public works.")
             return transactions # Return whatever bond txs we made? Or rollback?
             # If we issued bonds, we have cash. We just don't spend it. That's fine.

        active_households = [h for h in households if getattr(h, "is_active", False)]
        if not active_households:
             return transactions

        amount_per_hh = effective_cost / len(active_households)

        for h in active_households:
            tx = Transaction(
                buyer_id=self.government.id,
                seller_id=h.id,
                item_id="infrastructure_labor",
                quantity=1.0,
                price=amount_per_hh,
                market_id="system",
                transaction_type="infrastructure_spending",
                time=current_tick,
                metadata={
                    "triggers_effect": "GOVERNMENT_INFRA_UPGRADE" if h == active_households[0] else None,
                    "is_public_works": True
                }
            )
            transactions.append(tx)

        logger.info(
            f"INFRASTRUCTURE_PENDING | Level {self.government.infrastructure_level + 1} initiated. Cost: {effective_cost}. Distributed to {len(active_households)} households.",
            extra={
                "tick": current_tick,
                "agent_id": self.government.id,
                "tags": ["investment", "infrastructure"]
            }
        )
        return transactions

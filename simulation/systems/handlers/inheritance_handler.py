from typing import Any, List, Tuple
import math
import logging
from simulation.systems.api import ITransactionHandler, TransactionContext
from simulation.models import Transaction
from modules.system.api import DEFAULT_CURRENCY
from modules.finance.api import IPortfolioHandler, PortfolioDTO, PortfolioAsset

logger = logging.getLogger(__name__)

class InheritanceHandler(ITransactionHandler):
    """
    Handles 'inheritance_distribution' transactions.
    Distributes deceased agent's assets to heirs using Zero-Sum integer math logic.
    Enforces atomic settlement.
    """

    def handle(self, tx: Transaction, buyer: Any, seller: Any, context: TransactionContext) -> bool:
        """
        Executes the inheritance distribution.
        Buyer: Deceased Agent (Estate)
        Seller: Not used (None) or could be considered heirs implicitly.
        """
        # "buyer" is the Deceased Agent (Estate) holding the assets.
        deceased_agent = buyer

        heir_ids = tx.metadata.get("heir_ids", []) if tx.metadata else []

        # Round total cash to 2 decimals to prevent floating point dust propagation.
        assets_val = 0.0
        if hasattr(deceased_agent, 'wallet'):
            assets_val = deceased_agent.wallet.get_balance(DEFAULT_CURRENCY)
        elif hasattr(deceased_agent, 'assets') and isinstance(deceased_agent.assets, dict):
            assets_val = deceased_agent.assets.get(DEFAULT_CURRENCY, 0.0)
        elif hasattr(deceased_agent, 'assets'):
            assets_val = float(deceased_agent.assets)

        # TD-233: Use floor to ensure we don't distribute non-existent rounded-up cents
        total_cash = math.floor(assets_val * 100) / 100.0
        dust = assets_val - total_cash

        # Capture Portfolio (Atomic Step 1)
        original_portfolio = None
        has_portfolio = False
        if isinstance(deceased_agent, IPortfolioHandler):
             original_portfolio = deceased_agent.get_portfolio()
             # Clear immediately to prevent cloning/double-spending.
             # Will be restored if settlement fails.
             deceased_agent.clear_portfolio()
             if original_portfolio and original_portfolio.assets:
                 has_portfolio = True

        if total_cash <= 0 and dust <= 1e-9 and not has_portfolio:
            context.logger.info(f"INHERITANCE_SKIP | Agent {deceased_agent.id} has no assets ({assets_val}) and no portfolio.")
            # Restore if somehow captured empty one (unlikely but safe)
            if original_portfolio:
                 deceased_agent.receive_portfolio(original_portfolio)
            return True

        if not heir_ids:
            # If no heirs but we have dust/cash, handled elsewhere or we skip
            # InheritanceManager should handle escheatment if no heirs.
             context.logger.info(f"INHERITANCE_SKIP | Agent {deceased_agent.id} has no heirs.")
             # Restore portfolio if no heirs (so it can be escheated later if logic allows, though this handler assumes distribution)
             # But usually InheritanceManager checks for heirs first.
             if original_portfolio:
                 deceased_agent.receive_portfolio(original_portfolio)
             return True

        count = len(heir_ids)
        # Calculate amount per heir, avoiding float precision issues (floor to cent)
        base_amount = math.floor((total_cash / count) * 100) / 100.0

        credits: List[Tuple[Any, float, str]] = []
        distributed_sum = 0.0

        agents = context.agents # SimulationState has agents dict

        # Distribute to all but the last heir
        for i in range(count - 1):
            h_id = heir_ids[i]
            heir = agents.get(h_id)
            if heir:
                credits.append((heir, base_amount, "inheritance_distribution"))
                distributed_sum += base_amount

        # Last heir gets the remainder to ensure zero-sum of the rounded total
        last_heir_id = heir_ids[-1]
        last_heir = agents.get(last_heir_id)
        if last_heir:
            remaining_amount = round(total_cash - distributed_sum, 2)
            # Ensure we don't transfer negative amounts or dust if something went wrong
            if remaining_amount > 0:
                credits.append((last_heir, remaining_amount, "inheritance_distribution_final"))

        # TD-233: Sweep fractional dust to Government to ensure Zero Leak (Agent balance -> 0.0)
        if dust > 1e-9 and context.government:
             credits.append((context.government, dust, "inheritance_dust_sweep"))

        # Atomic Settlement (Cash)
        cash_success = True
        if credits:
            cash_success = context.settlement_system.settle_atomic(deceased_agent, credits, context.time)

            if cash_success:
                 context.logger.info(f"INHERITANCE_SUCCESS | Distributed {total_cash} from {deceased_agent.id} to {count} heirs. Swept {dust:.4f} dust.")
            else:
                 context.logger.error(f"INHERITANCE_FAIL | Atomic settlement failed for {deceased_agent.id}.")
                 # Rollback Portfolio
                 if original_portfolio:
                      deceased_agent.receive_portfolio(original_portfolio)
                 return False

        # Distribute Portfolio (Atomic Step 2 - Side Effect)
        if cash_success and original_portfolio and original_portfolio.assets:
             self._distribute_portfolio(original_portfolio, heir_ids, agents)

        return True

    def _distribute_portfolio(self, portfolio: PortfolioDTO, heir_ids: List[int], agents: dict[int, Any]):
        if not heir_ids or not portfolio.assets:
            return

        count = len(heir_ids)
        if count == 0:
            return

        # Distribute assets evenly among heirs
        for asset in portfolio.assets:
            quantity_per_heir = asset.quantity / count

            for h_id in heir_ids:
                heir = agents.get(h_id)
                if isinstance(heir, IPortfolioHandler):
                    # Construct a single-asset portfolio for transfer
                    heir_portfolio = PortfolioDTO(assets=[
                        PortfolioAsset(
                            asset_type=asset.asset_type,
                            asset_id=asset.asset_id,
                            quantity=quantity_per_heir
                        )
                    ])
                    heir.receive_portfolio(heir_portfolio)

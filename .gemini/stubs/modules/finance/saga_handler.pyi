from _typeshed import Incomplete
from modules.finance.api import IBank as IBank, IFinancialAgent as IFinancialAgent, MortgageApplicationDTO as MortgageApplicationDTO
from modules.finance.kernel.api import IMonetaryLedger as IMonetaryLedger
from modules.finance.sagas.housing_api import HousingSagaAgentContext as HousingSagaAgentContext, HousingTransactionSagaStateDTO as HousingTransactionSagaStateDTO, IHousingTransactionSagaHandler as IHousingTransactionSagaHandler, ILoanMarket as ILoanMarket, IPropertyRegistry as IPropertyRegistry, MortgageApprovalDTO as MortgageApprovalDTO
from modules.housing.api import IHousingService as IHousingService
from modules.simulation.api import HouseholdSnapshotDTO as HouseholdSnapshotDTO, ISimulationState as ISimulationState
from simulation.finance.api import ISettlementSystem as ISettlementSystem
from uuid import UUID as UUID

logger: Incomplete

class HousingTransactionSagaHandler(IHousingTransactionSagaHandler):
    simulation: Incomplete
    settlement_system: ISettlementSystem
    housing_service: IHousingService
    loan_market: Incomplete
    monetary_ledger: IMonetaryLedger | None
    def __init__(self, simulation: ISimulationState) -> None: ...
    def execute_step(self, saga: HousingTransactionSagaStateDTO) -> HousingTransactionSagaStateDTO: ...
    def compensate_step(self, saga: HousingTransactionSagaStateDTO) -> HousingTransactionSagaStateDTO: ...

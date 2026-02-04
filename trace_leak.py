import sys
import logging
from typing import Dict, Optional, List, Any
from dataclasses import dataclass

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TraceLeak")

# Import Modules
from modules.finance.wallet.audit import GLOBAL_WALLET_LOG
from modules.finance.wallet.wallet import Wallet
from modules.finance.wallet.api import IWallet, WalletOpLogDTO
from modules.finance.api import IFinancialEntity
from modules.system.api import DEFAULT_CURRENCY, CurrencyCode
from simulation.systems.settlement_system import SettlementSystem

# --- Mocks ---

@dataclass
class MockAgent:
    id: int
    initial_assets: float = 0.0

    def __post_init__(self):
        self.wallet = Wallet(self.id, {DEFAULT_CURRENCY: self.initial_assets})

    @property
    def assets(self) -> float:
        return self.wallet.get_balance(DEFAULT_CURRENCY)

    def deposit(self, amount: float, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        if amount > 0:
            self.wallet.add(amount, currency, memo="Deposit")

    def withdraw(self, amount: float, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        if amount > 0:
            self.wallet.subtract(amount, currency, memo="Withdraw")

# Define class with name "CentralBank" to satisfy SettlementSystem check
class CentralBank(MockAgent):
    def __post_init__(self):
        self.wallet = Wallet(self.id, allow_negative_balance=True)

    def mint(self, amount: float) -> None:
        self.wallet.add(amount, memo="Mint")

# --- Verification Logic ---

def verify_audit_log(expected_net_change: float = 0.0):
    logger.info("Verifying Global Audit Log...")

    total_delta = 0.0
    by_currency = {}

    for entry in GLOBAL_WALLET_LOG:
        total_delta += entry.delta
        by_currency[entry.currency] = by_currency.get(entry.currency, 0.0) + entry.delta

    logger.info(f"Total Logged Operations: {len(GLOBAL_WALLET_LOG)}")
    logger.info(f"Net Global Delta: {total_delta}")
    logger.info(f"By Currency: {by_currency}")

    net_default = by_currency.get(DEFAULT_CURRENCY, 0.0)

    if abs(net_default - expected_net_change) > 1e-9:
        logger.error(f"INTEGRITY FAIL: Expected {expected_net_change}, Got {net_default}")
        sys.exit(1)
    else:
        logger.info("INTEGRITY PASS: Zero-Sum Verified (Relative to Minting)")

def main():
    logger.info("Starting Trace Leak Overhaul Verification...")
    GLOBAL_WALLET_LOG.clear()

    # 1. Initialize Agents
    alice = MockAgent(1, 100.0)
    bob = MockAgent(2, 50.0)
    cb = CentralBank(999)

    settlement = SettlementSystem(logger=logger)

    # 2. Transfer Alice -> Bob (50)
    logger.info("--- Test 1: Simple Transfer (Alice -> Bob) ---")
    success = settlement.transfer(alice, bob, 50.0, "Test Transfer", tick=1)
    if not success:
        logger.error("Transfer failed!")
        sys.exit(1)

    verify_audit_log(expected_net_change=0.0)

    # 3. Central Bank Minting
    logger.info("--- Test 2: CB Minting ---")
    cb.mint(1000.0)
    verify_audit_log(expected_net_change=1000.0)

    # 4. CB Transfer to Alice (Helicopter Money)
    logger.info("--- Test 3: CB -> Alice (Stimulus) ---")
    # Should result in Net +200 if CB is recognized
    settlement.create_and_transfer(cb, alice, 200.0, "Stimulus", tick=2)
    verify_audit_log(expected_net_change=1200.0)

    # 5. Liquidation (Destruction)
    logger.info("--- Test 4: Liquidation (Alice) ---")
    # Should result in Net -50
    settlement.transfer_and_destroy(alice, cb, 50.0, "Tax Burn", tick=3)
    verify_audit_log(expected_net_change=1150.0)

    logger.info("Verification Complete!")

if __name__ == "__main__":
    main()

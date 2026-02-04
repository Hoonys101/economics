from typing import List
from .api import WalletOpLogDTO

# Shared mutable log for global auditing
GLOBAL_WALLET_LOG: List[WalletOpLogDTO] = []

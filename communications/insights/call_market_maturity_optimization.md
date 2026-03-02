# Call Market Maturity Queue Optimization

## Context
In the `CallMarketService`, the `settle_matured_loans` function is responsible for executing repayment transactions for all short-term loans that have reached their maturity tick. Previously, this function iterated over all active loans (`self.active_loans.items()`) on every tick to check if `tick >= loan['maturity_tick']`. As the number of active loans scales in the simulation, this O(N) iteration on every tick becomes a severe performance bottleneck.

## Resolution
To resolve this O(N) iteration penalty, a Min-heap (`self.maturity_queue`) was introduced using Python's `heapq` module.

### Data Structure Choice
The `heapq` (Min-heap) was chosen because it allows O(1) retrieval of the earliest maturing loan, and O(log M) insertion. Since time (ticks) progresses strictly forward, the min-heap perfectly maps to the temporal nature of maturities. Processing a tick simply pops elements until the top of the heap is strictly greater than the current tick.

Compared to a Dictionary indexed by tick (`Dict[int, List[str]]`), the min-heap avoids memory bloat from holding empty tick lists indefinitely and handles long-duration gaps cleanly without iterating over sparse keys.

### Resilience and Retry Mechanism
In the previous implementation, if a settlement transfer failed (e.g. `tx` returned `False`), the loan remained in the `active_loans` dictionary. Consequently, the next tick's O(N) loop would organically retry it.

With the heap-based approach, once a loan is popped, it must be explicitly re-queued if it fails to settle. We implemented a robust failover mechanism that collects all `failed_loans` during a tick and uses `heapq.heappush(self.maturity_queue, (tick + 1, lid))` to ensure these defaulted or stuck loans are automatically retried in the next tick, preserving systemic integrity.

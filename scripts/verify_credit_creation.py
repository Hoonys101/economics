
import sys
import os
sys.path.append(os.getcwd())
from main import create_simulation

def verify_multiplier():
    print("--- VERIFY CREDIT CREATION START ---")
    sim = create_simulation()
    
    # 0. Baseline
    m0_initial = sim.world_state.calculate_total_money()
    print(f"Initial M2 (Total Money): {m0_initial:,.2f}")
    
    bank = sim.bank
    borrower = sim.firms[0]
    savers = sim.households[:5]
    
    # 1. Households Deposit Cash (Increase Bank Reserves)
    total_deposit = 0.0
    for h in savers:
        amount = 1000.0
        if h._econ_state.assets >= amount:
            h._sub_assets(amount)
            bank.deposit(amount) # Bank Assets (Reserves) Up
            bank.deposit_from_customer(h.id, amount) # Bank Liabilities Up
            total_deposit += amount
            
    print(f"Deposited {total_deposit:,.2f} into Bank.")
    print(f"Bank Reserves: {bank.assets:,.2f}")
    
    m1 = sim.world_state.calculate_total_money()
    print(f"Post-Deposit M2: {m1:,.2f} (Should be roughly same as M0, just moved from Cash to Deposits)")
    
    # 2. Firm Borrows Money (Credit Creation)
    # With 10% Reserve Ratio, Bank can lend up to 90% of Deposits (if constrained)
    # But here Bank has Initial Capital + Deposits.
    loan_amount = 50000.0 
    print(f"Attempting Loan of {loan_amount:,.2f}...")
    
    loan_id = bank.grant_loan(borrower.id, loan_amount)
    
    if not loan_id:
        print("❌ Loan Denied! Credit Creation Failed.")
        sys.exit(1)
        
    print(f"✅ Loan Granted: {loan_id}")
    
    # 3. Check Money Supply Expansion
    # grant_loan triggers:
    #   if assets < amount: Mint (Govt Issued) -> Bank Reserves Up -> Loan Out
    #   Borrower Assets Up (Cash)
    #   Bank Assets (Loan) Up
    
    m2_final = sim.world_state.calculate_total_money()
    delta = m2_final - m1
    
    print(f"Final M2: {m2_final:,.2f}")
    print(f"Delta (M2 - M1): {delta:,.2f}")
    
    # Authorized Minting
    authorized_mint = sim.government.get_monetary_delta()
    print(f"Authorized Minting (Govt): {authorized_mint:,.2f}")
    
    if abs(delta - loan_amount) < 1.0:
         print("✅ M2 Expanded by exactly Loan Amount (Credit Created!)")
    else:
         print(f"⚠️ M2 Expansion Mismatch. Expected ~{loan_amount}, Got {delta}")
         
    # Check if Leak?
    leak = delta - authorized_mint
    print(f"Leak (Delta - Authorized): {leak:,.2f}")
    
    if abs(leak) < 1.0:
        print("✅ INTEGRITY CONFIRMED: Expansion is fully authorized.")
    else:
        print("❌ LEAK DETECTED: Authorized minting does not match expansion.")

if __name__ == "__main__":
    verify_multiplier()

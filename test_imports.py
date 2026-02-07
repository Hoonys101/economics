
try:
    from simulation.components.finance_department import FinanceDepartment
    print("FinanceDepartment imported successfully.")
except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"Error: {e}")

try:
    from simulation.components.hr_department import HRDepartment
    print("HRDepartment imported successfully.")
except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"Error: {e}")

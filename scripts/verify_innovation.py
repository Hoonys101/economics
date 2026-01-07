
import pandas as pd
import matplotlib.pyplot as plt
import os

# 1. Load Data
file_path = 'wo23_test_results.csv' 

if not os.path.exists(file_path):
    print(f"❌ 파일을 찾을 수 없습니다: {file_path}")
    exit()

try:
    df = pd.read_csv(file_path)
    print("✅ 데이터 로드 성공!")
    print(f"Columns: {df.columns.tolist()}")
except Exception as e:
    print(f"❌ 데이터 로드 실패: {e}")
    exit()

plt.style.use('seaborn-v0_8-darkgrid')
fig, axes = plt.subplots(3, 1, figsize=(12, 15))

# --- Graph 1: Production Shift (산업 구조 전환) ---
if 'prod_food' in df.columns and 'prod_goods' in df.columns:
    axes[0].plot(df['tick'], df['prod_food'], label='Food Production (Essential)', color='orange', alpha=0.7)
    axes[0].plot(df['tick'], df['prod_goods'], label='Goods Production (Innovation)', color='purple', linewidth=2)
    axes[0].set_title('Industrial Revolution: Sector Shift', fontsize=14, fontweight='bold')
    axes[0].set_ylabel('Output Units')
    axes[0].legend()
else:
    axes[0].text(0.5, 0.5, 'Goods Production Data Missing', ha='center')

# --- Graph 2: Consumption Utility (삶의 질) ---
if 'cons_goods' in df.columns:
    axes[1].plot(df['tick'], df['cons_food'], label='Food Consumption', color='orange', linestyle='--')
    axes[1].plot(df['tick'], df['cons_goods'], label='Goods Consumption', color='blue')
    axes[1].set_title('Quality of Life: Consumption Diversification', fontsize=14)
    axes[1].set_ylabel('Consumed Units')
    axes[1].legend()

# --- Graph 3: Economic Scale (GDP Growth) ---
if 'gdp' in df.columns:
    axes[2].plot(df['tick'], df['gdp'], label='Real GDP', color='green', linewidth=2)
    axes[2].axvline(x=200, color='red', linestyle=':', label='Previous Collapse (Tick 200)')
    axes[2].set_title('Economic Sustainability', fontsize=14)
    axes[2].set_xlabel('Tick')
    axes[2].set_ylabel('Value')
    axes[2].legend()

plt.tight_layout()
plt.savefig('innovation_verification.png')
print("📊 그래프 생성 완료: innovation_verification.png")

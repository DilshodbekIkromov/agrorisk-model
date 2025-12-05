"""
Retrain model with synthetic training data
"""

import pandas as pd
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent / "src"))
from model_training import AgroRiskModel
from config import DATA_SYNTHETIC_DIR

print("="*50)
print("RETRAINING MODEL WITH SYNTHETIC DATA")
print("="*50)

# Load synthetic training data (matches prediction pipeline features)
df = pd.read_csv(DATA_SYNTHETIC_DIR / "training_data.csv")
print(f"\nLoaded {len(df)} samples")
print(f"Features: {list(df.columns)}")

# Train
print("\n" + "-"*50)
model = AgroRiskModel()
metrics = model.train(df, target_col="risk_score")

# Save
model.save("models")

print("\n" + "="*50)
print("MODEL RETRAINED SUCCESSFULLY!")
print("="*50)
print(f"\nMetrics:")
print(f"  R²:   {metrics['r2']:.4f}")
print(f"  RMSE: {metrics['rmse']:.2f}")
print(f"  MAE:  {metrics['mae']:.2f}")
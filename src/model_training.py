"""
Agricultural Risk Model Training

This module trains a LightGBM model to predict crop risk scores
and provides SHAP-based explanations for each prediction.

Model outputs:
- risk_score: 0-100 (higher = better conditions, lower risk)
- risk_category: green (70-100), yellow (40-69), red (0-39)
- explanations: top factors driving the prediction
"""

import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import shap
import joblib
import json
from pathlib import Path

class AgroRiskModel:
    def __init__(self):
        self.model = None
        self.feature_names = None
        self.label_encoders = {}
        self.explainer = None
        self.feature_importance = None
        
    def prepare_features(self, df, fit_encoders=False):
        """Prepare features for training/inference"""
        df = df.copy()
        
        categorical_cols = ["region", "district", "crop", "crop_category", "climate_zone"]
        
        for col in categorical_cols:
            if col in df.columns:
                if fit_encoders:
                    self.label_encoders[col] = LabelEncoder()
                    df[col + "_encoded"] = self.label_encoders[col].fit_transform(df[col].astype(str))
                else:
                    if col in self.label_encoders:
                        known_labels = set(self.label_encoders[col].classes_)
                        df[col] = df[col].apply(lambda x: x if x in known_labels else "unknown")
                        if "unknown" not in self.label_encoders[col].classes_:
                            self.label_encoders[col].classes_ = np.append(self.label_encoders[col].classes_, "unknown")
                        df[col + "_encoded"] = self.label_encoders[col].transform(df[col].astype(str))
        
        base_feature_cols = [
            "latitude", "longitude", "month",
            "hist_temp_mean", "hist_precip_annual", "hist_soil_moisture",
            "current_temp_mean", "current_precip", "current_soil_moisture",
            "forecast_temp_14d", "forecast_precip_14d",
            "frost_risk", "drought_risk",
            "ndvi_current", "ndvi_forecast",
            "crop_temp_min", "crop_temp_max", "crop_water_need",
            "crop_moisture_min", "crop_drought_sens", "crop_frost_sens",
            "region_suitable", "season_suitable",
        ]

        feature_cols = list(base_feature_cols)
        for col in categorical_cols:
            if col + "_encoded" in df.columns:
                feature_cols.append(col + "_encoded")

        if fit_encoders:
            available_cols = [c for c in feature_cols if c in df.columns]
            self.feature_names = available_cols
            return df[available_cols]

        # Inference path: honor persisted feature order/selection when available to avoid
        # LightGBM shape mismatches. Fallback to the dynamically derived columns otherwise.
        if self.feature_names:
            # Ensure categorical columns expected by the stored feature list are encoded to numbers
            for col in categorical_cols:
                if col in df.columns and col in self.feature_names and col in self.label_encoders:
                    encoder = self.label_encoders[col]
                    def _encode(value):
                        if value in encoder.classes_:
                            return encoder.transform([value])[0]
                        if "unknown" in encoder.classes_:
                            return encoder.transform(["unknown"])[0]
                        # Fallback to first class to avoid breaking inference
                        return encoder.transform([encoder.classes_[0]])[0]
                    df[col] = df[col].apply(_encode)

            ordered_cols = [c for c in self.feature_names if c in df.columns]
            return df[ordered_cols]

        available_cols = [c for c in feature_cols if c in df.columns]
        return df[available_cols]
    
    def train(self, df, target_col="risk_score"):
        """Train the LightGBM model"""
        print("Preparing features...")
        X = self.prepare_features(df, fit_encoders=True)
        y = df[target_col]
        
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        print(f"Training set: {len(X_train)} samples")
        print(f"Validation set: {len(X_val)} samples")
        
        params = {
            "objective": "regression",
            "metric": "rmse",
            "boosting_type": "gbdt",
            "num_leaves": 31,
            "learning_rate": 0.05,
            "feature_fraction": 0.8,
            "bagging_fraction": 0.8,
            "bagging_freq": 5,
            "verbose": -1,
            "seed": 42,
        }
        
        train_data = lgb.Dataset(X_train, label=y_train)
        val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)
        
        print("\nTraining model...")
        self.model = lgb.train(
            params,
            train_data,
            num_boost_round=500,
            valid_sets=[train_data, val_data],
            callbacks=[
                lgb.early_stopping(stopping_rounds=50),
                lgb.log_evaluation(period=100)
            ]
        )
        
        y_pred = self.model.predict(X_val)
        
        metrics = {
            "rmse": np.sqrt(mean_squared_error(y_val, y_pred)),
            "mae": mean_absolute_error(y_val, y_pred),
            "r2": r2_score(y_val, y_pred),
        }
        
        print(f"\nValidation Metrics:")
        print(f"  RMSE: {metrics['rmse']:.2f}")
        print(f"  MAE:  {metrics['mae']:.2f}")
        print(f"  R²:   {metrics['r2']:.4f}")
        
        self.feature_importance = dict(zip(
            self.feature_names,
            self.model.feature_importance(importance_type="gain")
        ))
        
        print("\nInitializing SHAP explainer...")
        self.explainer = shap.TreeExplainer(self.model)
        
        return metrics
    
    def predict(self, df):
        """Make predictions with explanations"""
        X = self.prepare_features(df, fit_encoders=False)
        
        scores = self.model.predict(X)
        scores = np.clip(scores, 0, 100)
        
        # Some legacy artifacts may not have an explainer persisted; in that case skip SHAP
        shap_values = None
        if self.explainer is not None:
            shap_values = self.explainer.shap_values(X)
        
        results = []
        for i in range(len(df)):
            score = scores[i]
            category = "green" if score >= 70 else "yellow" if score >= 40 else "red"
            
            top_factors = []
            if shap_values is not None:
                feature_contributions = dict(zip(self.feature_names, shap_values[i]))
                sorted_contributions = sorted(
                    feature_contributions.items(),
                    key=lambda x: abs(x[1]),
                    reverse=True
                )
                for feat, contrib in sorted_contributions[:5]:
                    direction = "increases" if contrib > 0 else "decreases"
                    top_factors.append({
                        "feature": feat,
                        "contribution": round(contrib, 2),
                        "direction": direction,
                        "value": float(X.iloc[i][feat]) if feat in X.columns else None
                    })

            # Fallback when SHAP is unavailable or empty: use model feature importances
            if not top_factors:
                top_factors = self._fallback_factors(X.iloc[i])
            
            results.append({
                "risk_score": round(score, 1),
                "risk_category": category,
                "confidence": self._calculate_confidence(score),
                "top_factors": top_factors,
            })
        
        return results

    def _fallback_factors(self, row, top_k: int = 5):
        """Fallback explanations based on model feature importance when SHAP is unavailable."""
        if self.model is None:
            return []

        importances = self.model.feature_importance(importance_type="gain")
        if importances is None or len(importances) == 0:
            return []
            
        # Normalize importances to 0-100 scale relative to the total gain
        total_gain = np.sum(importances)
        if total_gain == 0:
            total_gain = 1

        names = self.feature_names or [f"feature_{i}" for i in range(len(importances))]
        ranked_idx = np.argsort(importances)[::-1]

        factors = []
        for idx in ranked_idx[:top_k]:
            imp = float(importances[idx])
            if imp <= 0:
                continue
            
            # Calculate percentage contribution
            normalized_imp = (imp / total_gain) * 100
            
            name = names[idx] if idx < len(names) else f"feature_{idx}"
            val = float(row[name]) if name in row else None
            factors.append({
                "feature": name,
                "contribution": round(normalized_imp, 1), # Round to 1 decimal place
                "direction": "increases",  # direction unknown without SHAP; keep schema stable
                "value": val
            })

        return factors
    
    def _calculate_confidence(self, score):
        """Calculate confidence based on how far from decision boundaries"""
        if score >= 85 or score <= 25:
            return "high"
        elif score >= 75 or score <= 35:
            return "medium"
        else:
            return "low"
    
    def get_recommendations(self, df, current_crop):
        """Get alternative crop recommendations with crop-specific recalculation."""
        from crops_database import (
            get_all_crops,
            get_crop_info,
            DROUGHT_SENSITIVITY_SCORES,
            FROST_SENSITIVITY_SCORES,
        )
        from feature_engineering import (
            calculate_region_suitability,
            calculate_seasonal_suitability,
            calculate_risk_flags,
        )

        all_crops = get_all_crops()
        recommendations = []

        base_row = df.iloc[0].to_dict()
        month = int(base_row.get("month", pd.Timestamp.now().month))
        region = base_row.get("region")
        lst_mean = float(base_row.get("lst_mean_c", base_row.get("current_temp_mean", 20.0)) or 20.0)
        lst_min = float(base_row.get("lst_min_c", lst_mean - 5.0) or lst_mean - 5.0)
        lst_max = float(base_row.get("lst_max_c", lst_mean + 5.0) or lst_mean + 5.0)
        precip_annual = float(base_row.get("precipitation_annual_mm", base_row.get("hist_precip_annual", 200.0)) or 200.0)
        ndvi_mean = float(base_row.get("ndvi_mean", base_row.get("ndvi_current", 0.3)) or 0.3)

        for crop in all_crops:
            if crop == current_crop:
                continue

            crop_info = get_crop_info(crop)
            if not crop_info:
                continue

            crop_ndvi_min = float(crop_info.get("ndvi_healthy_min", 0.3) or 0.3)
            temp_mid = (crop_info["optimal_temp_min"] + crop_info["optimal_temp_max"]) / 2
            temp_span = max(1.0, crop_info["optimal_temp_max"] - crop_info["optimal_temp_min"])
            temp_match = np.clip(1 - abs(lst_mean - temp_mid) / (temp_span / 2 + 5), 0, 1)
            water_match = np.clip(precip_annual / max(1.0, crop_info["water_need_mm"]), 0, 1.5)
            ndvi_score = np.clip(ndvi_mean / max(0.1, crop_ndvi_min), 0, 2)
            frost_risk, drought_risk = calculate_risk_flags(
                crop, lst_min, lst_max, precip_annual, lst_mean
            )

            test_row = base_row.copy()
            test_row.update({
                "crop": crop,
                "crop_category": crop_info["category"],
                "crop_temp_min": crop_info["optimal_temp_min"],
                "crop_temp_max": crop_info["optimal_temp_max"],
                "crop_water_need": crop_info["water_need_mm"],
                "crop_moisture_min": crop_info["soil_moisture_min"],
                "crop_ndvi_min": crop_ndvi_min,
                "crop_drought_sens": DROUGHT_SENSITIVITY_SCORES.get(crop_info["drought_sensitivity"], 0.5),
                "crop_frost_sens": FROST_SENSITIVITY_SCORES.get(crop_info["frost_sensitivity"], 0.5),
                "region_suitable": calculate_region_suitability(crop, region),
                "season_suitable": calculate_seasonal_suitability(crop, month),
                "temp_match": temp_match,
                "water_match": water_match,
                "ndvi_score": ndvi_score,
                "frost_risk": frost_risk,
                "drought_risk": drought_risk,
            })

            test_df = pd.DataFrame([test_row])
            result = self.predict(test_df)[0]

            recommendations.append({
                "crop": crop,
                "crop_uz": crop_info["name_uz"],
                "category": crop_info["category"],
                "risk_score": result["risk_score"],
                "risk_category": result["risk_category"],
            })

        recommendations.sort(key=lambda x: x["risk_score"], reverse=True)
        return recommendations[:5]
    
    def save(self, output_dir=None):
        """Save model and associated files"""
        if output_dir is None:
            from config import MODELS_DIR
            output_dir = MODELS_DIR
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        model_path = output_path / "agrorisk_model.txt"
        self.model.save_model(str(model_path))
        print(f"Saved model: {model_path}")
        
        meta = {
            "feature_names": self.feature_names,
            "label_encoders": {k: list(v.classes_) for k, v in self.label_encoders.items()},
            "feature_importance": self.feature_importance,
        }
        meta_path = output_path / "model_metadata.json"
        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2)
        print(f"Saved metadata: {meta_path}")
        
        joblib_path = output_path / "agrorisk_model.joblib"
        joblib.dump(self, joblib_path)
        print(f"Saved full model object: {joblib_path}")
        
        return model_path
    
    @classmethod
    def load(cls, model_dir=None):
        """Load saved model"""
        if model_dir is None:
            from config import MODELS_DIR
            model_dir = MODELS_DIR
        model_path = Path(model_dir) / "agrorisk_model.joblib"
        return joblib.load(model_path)


def format_explanation(result, include_values=True):
    """Format prediction result for display"""
    output = []
    output.append(f"Risk Score: {result['risk_score']}/100")
    output.append(f"Category: {result['risk_category'].upper()}")
    output.append(f"Confidence: {result['confidence']}")
    output.append("\nTop factors:")
    
    for factor in result["top_factors"]:
        direction = "↑" if factor["direction"] == "increases" else "↓"
        line = f"  {direction} {factor['feature']}: {factor['contribution']:+.2f}"
        if include_values and factor["value"] is not None:
            line += f" (value: {factor['value']:.2f})"
        output.append(line)
    
    return "\n".join(output)


if __name__ == "__main__":
    from config import DATA_SYNTHETIC_DIR
    print("Loading training data...")
    df = pd.read_csv(DATA_SYNTHETIC_DIR / "training_data.csv")
    print(f"Loaded {len(df)} samples")
    
    print("\n" + "="*60)
    print("TRAINING AGRORISK MODEL")
    print("="*60)
    
    model = AgroRiskModel()
    metrics = model.train(df)
    
    model.save()
    
    print("\n" + "="*60)
    print("FEATURE IMPORTANCE (Top 10)")
    print("="*60)
    sorted_importance = sorted(model.feature_importance.items(), key=lambda x: x[1], reverse=True)
    for feat, importance in sorted_importance[:10]:
        print(f"  {feat}: {importance:.1f}")
    
    print("\n" + "="*60)
    print("TEST PREDICTIONS")
    print("="*60)
    
    test_samples = df.sample(3, random_state=123)
    predictions = model.predict(test_samples)
    
    for i, (idx, row) in enumerate(test_samples.iterrows()):
        print(f"\n--- Sample {i+1}: {row['region']} / {row['district']} / {row['crop']} ---")
        print(f"Actual score: {row['risk_score']}")
        print(format_explanation(predictions[i]))

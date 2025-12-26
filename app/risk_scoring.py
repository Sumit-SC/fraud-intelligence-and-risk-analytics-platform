"""
Risk scoring logic for transactions.

Stage 8B: ML-lite fraud risk scoring using ensemble models.
Focus: Explainable risk ranking with industry-standard approaches.
"""

import os
import pickle
from pathlib import Path

import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import shap

# Initialize SHAP explainer (will be set after model training)
_shap_explainer = None
_shap_model = None
_shap_features = None


def cleanup_resources():
    """
    Clean up SHAP explainer and model references.
    Call this when shutting down the app to free memory.
    """
    global _shap_explainer, _shap_model, _shap_features
    _shap_explainer = None
    _shap_model = None
    _shap_features = None

# Model persistence paths
MODELS_DIR = Path(__file__).parent.parent / "models"
MODELS_DIR.mkdir(exist_ok=True)

LR_MODEL_PATH = MODELS_DIR / "lr_model.pkl"
RF_MODEL_PATH = MODELS_DIR / "rf_model.pkl"
SCALER_PATH = MODELS_DIR / "scaler.pkl"
MODEL_METADATA_PATH = MODELS_DIR / "model_metadata.pkl"


def calculate_risk_score(df: pd.DataFrame) -> pd.Series:
    """
    Calculate placeholder risk scores for transactions.

    This is a simple rule-based scoring system that will be replaced
    with ML-lite scoring in Stage 8B.

    Args:
        df: DataFrame with transaction features

    Returns:
        Series of risk scores (0-100, higher = more risky)
    """
    if df.empty:
        return pd.Series(dtype=float)
    
    # Initialize risk score
    risk_score = pd.Series(0.0, index=df.index)
    
    # Rule 1: High transaction velocity (last 24h)
    if "txns_last_24h" in df.columns:
        # Normalize to 0-30 scale (assuming max ~30 txns in 24h is very high)
        velocity_risk = (df["txns_last_24h"].fillna(0) / 30.0 * 25).clip(0, 25)
        risk_score += velocity_risk
    
    # Rule 2: Amount deviation from card average
    if "amount_vs_card_avg" in df.columns:
        # Higher deviation = higher risk (normalize to 0-20 scale)
        amount_dev_risk = (df["amount_vs_card_avg"].fillna(1.0).abs() - 1.0) * 10
        amount_dev_risk = amount_dev_risk.clip(0, 20)
        risk_score += amount_dev_risk
    
    # Rule 3: High-risk merchant
    if "is_high_risk_merchant" in df.columns:
        risk_score += df["is_high_risk_merchant"].fillna(False).astype(int) * 15
    
    # Rule 4: Emulator device
    if "is_emulator_device" in df.columns:
        risk_score += df["is_emulator_device"].fillna(False).astype(int) * 15
    
    # Rule 5: Merchant fraud rate
    if "merchant_fraud_rate_30d" in df.columns:
        # Normalize to 0-15 scale (assuming max ~0.5 = 50% fraud rate)
        merchant_risk = (df["merchant_fraud_rate_30d"].fillna(0) / 0.5 * 15).clip(0, 15)
        risk_score += merchant_risk
    
    # Rule 6: Decline history
    if "declined_txns_last_24h" in df.columns:
        decline_risk = (df["declined_txns_last_24h"].fillna(0) / 5.0 * 10).clip(0, 10)
        risk_score += decline_risk
    
    # Clip final score to 0-100 range
    risk_score = risk_score.clip(0, 100)
    
    return risk_score


def explain_risk_score(row: pd.Series) -> list[str]:
    """
    Generate SHAP-based explanation for why a transaction is risky.
    
    Uses SHAP (SHapley Additive exPlanations) for model-agnostic, 
    mathematically principled feature importance.
    
    Args:
        row: Single transaction row (Series)
        
    Returns:
        List of explanation strings with SHAP values
    """
    global _shap_explainer, _shap_model, _shap_features
    
    explanations = []
    
    # Try SHAP explanation if available
    # Initialize SHAP explainer lazily if model exists but explainer doesn't
    if _shap_model is not None and _shap_features is not None and _shap_explainer is None:
        try:
            # Suppress SHAP warnings and use a simpler explainer for faster cleanup
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                _shap_explainer = shap.TreeExplainer(_shap_model)
        except Exception as e:
            # If SHAP fails, just use fallback - don't block
            _shap_explainer = None
    
    if _shap_explainer is not None and _shap_model is not None and _shap_features is not None:
        try:
            # Prepare feature vector for this transaction
            feature_values = []
            for feat in _shap_features:
                if feat in row.index:
                    val = row[feat]
                    if pd.isna(val):
                        val = 0
                    elif isinstance(val, bool):
                        val = int(val)
                    feature_values.append(val)
                else:
                    feature_values.append(0)
            
            # Calculate SHAP values
            # For binary classification, TreeExplainer returns shape (n_samples, n_classes, n_features)
            # We want class 1 (fraud) values for the first (and only) sample
            shap_output = _shap_explainer.shap_values(np.array([feature_values]))
            
            # Handle different SHAP output formats
            if isinstance(shap_output, list):
                # List format: [class_0_values, class_1_values]
                shap_values = shap_output[1][0]  # Class 1, first sample
            elif isinstance(shap_output, np.ndarray):
                # Array format: (n_samples, n_classes, n_features) or (n_samples, n_features)
                if len(shap_output.shape) == 3:
                    shap_values = shap_output[0, 1, :]  # First sample, class 1, all features
                else:
                    shap_values = shap_output[0, :]  # First sample, all features
            else:
                # Fallback
                shap_values = shap_output[0] if hasattr(shap_output, '__getitem__') else np.zeros(len(_shap_features))
            
            # Create feature importance pairs
            feature_importance = list(zip(_shap_features, shap_values))
            feature_importance.sort(key=lambda x: abs(x[1]), reverse=True)
            
            # Generate explanations from top contributing features
            for feat, shap_val in feature_importance[:5]:  # Top 5 features
                if abs(shap_val) > 0.01:  # Only show significant contributions
                    direction = "increases" if shap_val > 0 else "decreases"
                    impact = abs(shap_val) * 100
                    feat_value = row.get(feat, "N/A")
                    
                    # Format feature-specific explanations
                    if feat == "txns_last_24h":
                        explanations.append(
                            f"Transaction velocity {direction} risk by {impact:.1f}% "
                            f"({feat_value:.0f} transactions in last 24h)"
                        )
                    elif feat == "declined_txns_last_24h":
                        explanations.append(
                            f"Decline history {direction} risk by {impact:.1f}% "
                            f"({feat_value:.0f} declined transactions)"
                        )
                    elif feat == "merchant_fraud_rate_30d":
                        explanations.append(
                            f"Merchant fraud rate {direction} risk by {impact:.1f}% "
                            f"({feat_value*100:.1f}% historical fraud rate)"
                        )
                    elif feat == "is_high_risk_merchant":
                        explanations.append(
                            f"High-risk merchant flag {direction} risk by {impact:.1f}%"
                        )
                    elif feat == "is_emulator_device":
                        explanations.append(
                            f"Emulator device {direction} risk by {impact:.1f}%"
                        )
            
            if not explanations:
                explanations.append("SHAP analysis: No significant feature contributions identified")
                
        except Exception as e:
            # Fallback to rule-based if SHAP fails
            explanations = _fallback_explanation(row)
    else:
        # Fallback to rule-based explanation if SHAP not available
        explanations = _fallback_explanation(row)
    
    return explanations


def _fallback_explanation(row: pd.Series) -> list[str]:
    """Fallback rule-based explanation if SHAP is not available."""
    explanations = []
    
    # Check each risk factor
    if "txns_last_24h" in row and pd.notna(row["txns_last_24h"]) and row["txns_last_24h"] > 10:
        explanations.append(f"High transaction velocity: {row['txns_last_24h']:.0f} transactions in the last 24 hours")
    
    if "amount_vs_card_avg" in row and pd.notna(row["amount_vs_card_avg"]):
        ratio = row["amount_vs_card_avg"]
        if abs(ratio - 1.0) > 0.5:
            explanations.append(f"Unusual amount: {ratio:.2f}x the card's average transaction amount")
    
    if "is_high_risk_merchant" in row and row.get("is_high_risk_merchant", False):
        explanations.append("Merchant is flagged as high-risk tier")
    
    if "is_emulator_device" in row and row.get("is_emulator_device", False):
        explanations.append("Transaction originated from an emulator device")
    
    if "merchant_fraud_rate_30d" in row and pd.notna(row["merchant_fraud_rate_30d"]) and row["merchant_fraud_rate_30d"] > 0.1:
        explanations.append(f"Merchant has elevated fraud rate: {row['merchant_fraud_rate_30d']*100:.1f}% in last 30 days")
    
    if "declined_txns_last_24h" in row and pd.notna(row["declined_txns_last_24h"]) and row["declined_txns_last_24h"] > 2:
        explanations.append(f"Multiple declined transactions: {row['declined_txns_last_24h']:.0f} in the last 24 hours")
    
    if not explanations:
        explanations.append("No significant risk factors identified")
    
    return explanations


def _save_models(lr_model, rf_model, scaler, feature_names):
    """
    Save trained models and scaler to disk for persistence.
    
    Args:
        lr_model: Trained Logistic Regression model
        rf_model: Trained Random Forest model
        scaler: Trained StandardScaler
        feature_names: List of feature names used for training
    """
    try:
        # Save models
        with open(LR_MODEL_PATH, 'wb') as f:
            pickle.dump(lr_model, f)
        
        with open(RF_MODEL_PATH, 'wb') as f:
            pickle.dump(rf_model, f)
        
        with open(SCALER_PATH, 'wb') as f:
            pickle.dump(scaler, f)
        
        # Save metadata (feature names, training info)
        metadata = {
            'feature_names': feature_names,
            'model_version': '1.0',
            'ensemble_weights': {'lr': 0.5, 'rf': 0.5}
        }
        
        with open(MODEL_METADATA_PATH, 'wb') as f:
            pickle.dump(metadata, f)
        
    except Exception as e:
        # Log error but don't fail - models will retrain next time
        print(f"Warning: Could not save models: {e}")


def _load_models(expected_features):
    """
    Load saved models from disk if they exist and match expected features.
    
    Args:
        expected_features: List of feature names expected by the models
        
    Returns:
        Tuple of (lr_model, rf_model, scaler) if models exist and match, else None
    """
    try:
        # Check if all model files exist
        if not all([LR_MODEL_PATH.exists(), RF_MODEL_PATH.exists(), 
                   SCALER_PATH.exists(), MODEL_METADATA_PATH.exists()]):
            return None
        
        # Load metadata to check feature compatibility
        with open(MODEL_METADATA_PATH, 'rb') as f:
            metadata = pickle.load(f)
        
        # Check if features match
        saved_features = metadata.get('feature_names', [])
        if set(saved_features) != set(expected_features):
            # Features don't match - models need retraining
            return None
        
        # Load models
        with open(LR_MODEL_PATH, 'rb') as f:
            lr_model = pickle.load(f)
        
        with open(RF_MODEL_PATH, 'rb') as f:
            rf_model = pickle.load(f)
        
        with open(SCALER_PATH, 'rb') as f:
            scaler = pickle.load(f)
        
        return (lr_model, rf_model, scaler)
        
    except Exception as e:
        # If loading fails, return None to trigger retraining
        print(f"Warning: Could not load models: {e}")
        return None


def score_transactions(df: pd.DataFrame) -> pd.DataFrame:
    """
    ML-lite fraud risk scoring using ensemble models (Logistic Regression + Random Forest).
    
    Industry-standard approach: Ensemble of interpretable models for robust risk assessment.
    - Logistic Regression: Linear, interpretable, fast
    - Random Forest: Captures non-linear patterns, feature importance
    
    Why Ensemble?
    - Combines strengths of both models
    - More robust than single model
    - Industry-standard for fraud detection
    - Still interpretable via SHAP
    
    Note: In production, you would train on historical data once, save the models,
    and load them to score new transactions. For this demo, we train on the data
    passed to the function for simplicity.
    
    Args:
        df: DataFrame with transaction features and is_fraud label
        
    Returns:
        DataFrame with added columns:
        - risk_score: Ensemble probability of fraud (0-1)
        - risk_band: LOW (<0.3), MEDIUM (0.3-0.6), HIGH (≥0.6)
    """
    global _shap_explainer, _shap_model, _shap_features
    
    if df.empty:
        df["risk_score"] = 0.0
        df["risk_band"] = "LOW"
        return df
    
    # Create a copy to avoid modifying original
    df_scored = df.copy()
    
    # Feature selection: business-interpretable signals
    feature_columns = [
        "txns_last_24h",              # Velocity: fraudsters act quickly
        "declined_txns_last_24h",     # Decline history: testing stolen cards
        "merchant_fraud_rate_30d",    # Merchant risk: some merchants attract fraud
        "is_high_risk_merchant",       # Merchant tier: categorical risk indicator
        "is_emulator_device"          # Device type: emulators often used for fraud
    ]
    
    # Check which features are available
    available_features = [col for col in feature_columns if col in df_scored.columns]
    
    if not available_features:
        # Fallback: use placeholder scoring if no features available
        df_scored["risk_score"] = calculate_risk_score(df_scored) / 100.0
        df_scored["risk_band"] = df_scored["risk_score"].apply(
            lambda x: "HIGH" if x >= 0.6 else ("MEDIUM" if x >= 0.3 else "LOW")
        )
        return df_scored
    
    # Prepare features and label
    X = df_scored[available_features].copy()
    y = df_scored["is_fraud"] if "is_fraud" in df_scored.columns else None
    
    # Handle missing values: fill with median for numeric, False for boolean
    for col in X.columns:
        if X[col].dtype in ['int64', 'float64']:
            X[col] = X[col].fillna(X[col].median() if X[col].notna().any() else 0)
        elif X[col].dtype == 'bool':
            X[col] = X[col].fillna(False).astype(int)  # Convert bool to int for models
        else:
            X[col] = X[col].fillna(0)
    
    # Try to load existing models first
    models_loaded = _load_models(available_features)
    
    if models_loaded:
        # Use loaded models for scoring
        # Note: X already has missing values filled from preprocessing above (lines 372-378)
        lr_model, rf_model, scaler = models_loaded
        
        # Score using loaded models (X is already preprocessed)
        # OPTIMIZATION: For large datasets, score in smaller batches to avoid memory issues
        try:
            if len(X) > 50000:
                # Score in batches of 50k for very large datasets
                batch_size = 50000
                all_lr_proba = []
                all_rf_proba = []
                
                for i in range(0, len(X), batch_size):
                    batch_X = X.iloc[i:i+batch_size]
                    batch_X_scaled = scaler.transform(batch_X)
                    all_lr_proba.append(lr_model.predict_proba(batch_X_scaled)[:, 1])
                    all_rf_proba.append(rf_model.predict_proba(batch_X)[:, 1])
                
                lr_proba = np.concatenate(all_lr_proba)
                rf_proba = np.concatenate(all_rf_proba)
            else:
                # Small dataset - score all at once
                X_scaled = scaler.transform(X)
                lr_proba = lr_model.predict_proba(X_scaled)[:, 1]
                rf_proba = rf_model.predict_proba(X)[:, 1]
        except Exception as e:
            # If scoring fails, return placeholder scores
            print(f"Warning: Scoring failed: {e}")
            lr_proba = np.full(len(X), 0.5)
            rf_proba = np.full(len(X), 0.5)
        
        # Weighted ensemble
        ensemble_proba = 0.5 * lr_proba + 0.5 * rf_proba
        df_scored["risk_score"] = ensemble_proba
        
        # Store model and features for SHAP (but don't initialize explainer yet - lazy loading)
        # SHAP explainer will be initialized on-demand in explain_risk_score() to avoid blocking
        _shap_model = rf_model
        _shap_features = available_features
        _shap_explainer = None  # Lazy initialization - only when needed
    
    # Train new models if labels are available and models don't exist
    elif y is not None and y.notna().any() and y.sum() > 0:
        # Filter to rows with valid labels
        valid_mask = y.notna()
        X_train = X[valid_mask]
        y_train = y[valid_mask].astype(int)
        
        if len(X_train) > 0 and y_train.sum() > 0:  # Need at least some fraud cases
            # Model 1: Logistic Regression (interpretable, linear)
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            
            lr_model = LogisticRegression(
                max_iter=1000,
                random_state=42,
                class_weight='balanced'
            )
            lr_model.fit(X_train_scaled, y_train)
            
            # Model 2: Random Forest (non-linear patterns, feature importance)
            # Optimize for large datasets: reduce n_estimators if dataset is very large
            n_estimators = 100
            if len(X_train) > 100000:
                n_estimators = 50  # Fewer trees for very large datasets (faster training)
            
            rf_model = RandomForestClassifier(
                n_estimators=n_estimators,
                max_depth=10,
                min_samples_split=50,
                class_weight='balanced',
                random_state=42,
                n_jobs=1  # Use 1 job to avoid multiprocessing issues in Streamlit
            )
            rf_model.fit(X_train, y_train)
            
            # Save models for future use
            _save_models(lr_model, rf_model, scaler, available_features)
            
            # Ensemble: Average probabilities from both models
            # Weight: 50% Logistic Regression, 50% Random Forest
            X_scaled = scaler.transform(X)
            lr_proba = lr_model.predict_proba(X_scaled)[:, 1]
            rf_proba = rf_model.predict_proba(X)[:, 1]
            
            # Weighted ensemble (can adjust weights based on validation performance)
            ensemble_proba = 0.5 * lr_proba + 0.5 * rf_proba
            
            df_scored["risk_score"] = ensemble_proba
            
            # Store model and features for SHAP explanations
            # Use Random Forest for SHAP (TreeExplainer is faster and more accurate for RF)
            _shap_model = rf_model
            _shap_features = available_features
            
            # Initialize SHAP explainer (TreeExplainer for Random Forest)
            # Defer SHAP initialization to avoid blocking - it's only needed for explanations
            # We'll initialize it lazily when needed
            _shap_explainer = None  # Will be initialized on-demand in explain_risk_score
            _shap_model = rf_model
            _shap_features = available_features
            
        else:
            # Not enough fraud cases to train - use placeholder
            df_scored["risk_score"] = calculate_risk_score(df_scored) / 100.0
            _shap_explainer = None
            _shap_model = None
    else:
        # No labels available and no saved models - use placeholder scoring
        df_scored["risk_score"] = calculate_risk_score(df_scored) / 100.0
        _shap_explainer = None
        _shap_model = None
    
    # Create risk bands: business-interpretable categories
    # LOW: <30% probability - likely legitimate
    # MEDIUM: 30-60% - needs review
    # HIGH: ≥60% - strong fraud signal
    df_scored["risk_band"] = df_scored["risk_score"].apply(
        lambda x: "HIGH" if x >= 0.6 else ("MEDIUM" if x >= 0.3 else "LOW")
    )
    
    return df_scored


def retrain_models(df: pd.DataFrame, force: bool = False):
    """
    Explicitly retrain models and save them.
    
    Args:
        df: DataFrame with transaction features and is_fraud label
        force: If True, retrain even if models exist
        
    Returns:
        True if models were trained and saved, False otherwise
    """
    global _shap_explainer, _shap_model, _shap_features
    
    # Check if models exist and force is False
    if not force:
        feature_columns = [
            "txns_last_24h",
            "declined_txns_last_24h",
            "merchant_fraud_rate_30d",
            "is_high_risk_merchant",
            "is_emulator_device"
        ]
        available_features = [col for col in feature_columns if col in df.columns]
        
        if _load_models(available_features) is not None:
            return False  # Models already exist
    
    # Train models using score_transactions (which will save them)
    _ = score_transactions(df)
    return True


def get_feature_importance(model, feature_names):
    """
    Extract feature importance from trained Logistic Regression model.
    
    Logistic Regression coefficients indicate how much each feature
    contributes to the risk score. Positive = increases fraud probability,
    Negative = decreases fraud probability.
    
    Args:
        model: Trained LogisticRegression model
        feature_names: List of feature names
        
    Returns:
        DataFrame with features and their coefficients
    """
    if model is None or not hasattr(model, 'coef_'):
        return pd.DataFrame()
    
    importance_df = pd.DataFrame({
        "feature": feature_names,
        "coefficient": model.coef_[0],
        "abs_coefficient": np.abs(model.coef_[0])
    }).sort_values("abs_coefficient", ascending=False)
    
    return importance_df


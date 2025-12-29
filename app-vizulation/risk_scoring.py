"""
Risk scoring logic for transactions.

Stage 8B: ML-lite fraud risk scoring using Logistic Regression.
Focus: Explainable risk ranking for investigators (not prediction accuracy).

Why Logistic Regression?
- Interpretable: Coefficients show feature importance
- Fast: Quick training and scoring
- Business-friendly: Easy to explain to stakeholders
- No hyperparameter tuning needed for this use case
"""

import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

# SHAP for model explanations
try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    shap = None


# Global model storage (trained once, reused for scoring)
_model = None
_scaler = None
_feature_names = None
_shap_explainer = None  # SHAP explainer for detailed explanations


def score_transactions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Score transactions using ML-lite Logistic Regression model.
    
    Stage 8B: ML-lite implementation for explainable risk ranking.
    
    Approach:
    1. Select interpretable features
    2. Handle missing values safely
    3. Train LogisticRegression model (if labels available)
    4. Generate risk_score using predict_proba
    5. Create risk_band categories
    
    Args:
        df: DataFrame with transaction features and optional is_fraud label
        
    Returns:
        DataFrame with added columns:
        - risk_score: Fraud probability (0-1)
        - risk_band: LOW (<0.3), MEDIUM (0.3-0.6), HIGH (≥0.6)
    """
    # Declare global variables at the start (before any use)
    global _model, _scaler, _feature_names
    
    if df.empty:
        # Return empty DataFrame with required columns
        df_result = df.copy()
        if len(df_result) == 0:
            # Create empty Series with correct dtypes
            df_result["risk_score"] = pd.Series(dtype=float)
            df_result["risk_band"] = pd.Series(dtype=str)
        else:
            df_result["risk_score"] = 0.0
            df_result["risk_band"] = "LOW"
        return df_result
    
    # Create a copy to avoid modifying original
    df_scored = df.copy()
    
    # Step 1: Select features (business-interpretable signals)
    feature_columns = [
        "txns_last_24h",              # Velocity: Fraudsters act quickly, testing cards
        "declined_txns_last_24h",     # Decline history: Testing stolen cards
        "merchant_fraud_rate_30d",    # Merchant risk: Some merchants attract fraud
        "is_high_risk_merchant",      # Merchant tier: Categorical risk indicator
        "is_emulator_device"          # Device type: Emulators often used for fraud
    ]
    
    # Check which features are available
    available_features = [col for col in feature_columns if col in df_scored.columns]
    
    if not available_features:
        # Fallback: Use placeholder scoring if no features available
        df_scored["risk_score"] = 0.5
        df_scored["risk_band"] = "MEDIUM"
        return df_scored
    
    # Step 2: Prepare features and label
    X = df_scored[available_features].copy()
    y = df_scored["is_fraud"] if "is_fraud" in df_scored.columns else None
    
    # Step 3: Handle missing values safely
    # Numeric features: fill with median (or 0 if all NaN)
    # Boolean features: fill with False (most common case)
    for col in X.columns:
        if X[col].dtype in ['int64', 'float64']:
            median_val = X[col].median() if X[col].notna().any() else 0
            X[col] = X[col].fillna(median_val)
        elif X[col].dtype == 'bool':
            X[col] = X[col].fillna(False).astype(int)  # Convert bool to int for model
        else:
            X[col] = X[col].fillna(0)
    
    # Step 4: Train model if labels available and model doesn't exist
    # Only train if model hasn't been trained yet (to avoid retraining on filtered data)
    if _model is None and y is not None and y.notna().any() and y.sum() > 0:
        # Filter to rows with valid labels
        valid_mask = y.notna()
        X_train = X[valid_mask]
        y_train = y[valid_mask].astype(int)
        
        # Only train if we have fraud cases
        if len(X_train) > 0 and y_train.sum() > 0:
            # Standardize features for Logistic Regression
            # Why StandardScaler? Logistic Regression benefits from normalized features
            _scaler = StandardScaler()
            X_train_scaled = _scaler.fit_transform(X_train)
            
            # Train Logistic Regression model
            # Why Logistic Regression?
            # - Interpretable coefficients (feature importance)
            # - Fast training and prediction
            # - Probabilistic output (perfect for risk scoring)
            # - No hyperparameter tuning needed for this use case
            _model = LogisticRegression(
                max_iter=1000,           # Enough iterations for convergence
                random_state=42,         # Reproducibility
                class_weight='balanced'  # Handle class imbalance (fraud is rare)
            )
            _model.fit(X_train_scaled, y_train)
            _feature_names = available_features
            
            # Initialize SHAP explainer for Logistic Regression
            # Use LinearExplainer for Logistic Regression (faster and exact)
            if SHAP_AVAILABLE:
                try:
                    # Create background dataset for SHAP (use more data for better explanations)
                    # Use up to 1000 rows for background (more representative of the data distribution)
                    background_size = min(1000, len(X_train_scaled))
                    background_data = X_train_scaled[:background_size]
                    _shap_explainer = shap.LinearExplainer(_model, background_data)
                except Exception as e:
                    # If SHAP fails, continue without it
                    _shap_explainer = None
            else:
                _shap_explainer = None
    
    # Step 5: Generate risk scores
    if _model is not None and _scaler is not None and _feature_names is not None:
        # Ensure we're using the same features the model was trained on
        X_score = df_scored[_feature_names].copy()
        
        # Handle missing values (same as training)
        for col in X_score.columns:
            if X_score[col].dtype in ['int64', 'float64']:
                median_val = X_score[col].median() if X_score[col].notna().any() else 0
                X_score[col] = X_score[col].fillna(median_val)
            elif X_score[col].dtype == 'bool':
                X_score[col] = X_score[col].fillna(False).astype(int)
            else:
                X_score[col] = X_score[col].fillna(0)
        
        # Scale features and predict probabilities
        X_score_scaled = _scaler.transform(X_score)
        # predict_proba returns [prob_class_0, prob_class_1]
        # We want prob_class_1 (fraud probability)
        risk_scores = _model.predict_proba(X_score_scaled)[:, 1]
        df_scored["risk_score"] = risk_scores
    else:
        # No model available - use placeholder scores
        # This happens if:
        # - No labels in data
        # - No fraud cases in training data
        # - Model training failed
        df_scored["risk_score"] = 0.5
    
    # Step 6: Create risk bands (business-interpretable categories)
    # LOW: <30% probability - likely legitimate, low priority
    # MEDIUM: 30-60% - needs review, moderate priority
    # HIGH: ≥60% - strong fraud signal, high priority
    df_scored["risk_band"] = df_scored["risk_score"].apply(
        lambda x: "HIGH" if x >= 0.6 else ("MEDIUM" if x >= 0.3 else "LOW")
    )
    
    return df_scored


def explain_risk_score(row: pd.Series, use_shap: bool = True) -> list[str]:
    """
    Generate explanation for why a transaction is risky using SHAP or model coefficients.
    
    Stage 8B: Uses SHAP (preferred) or Logistic Regression coefficients to explain risk.
    
    Why SHAP?
    - Model-agnostic: Works with any model
    - Mathematically principled: Based on Shapley values from game theory
    - Shows exact contribution of each feature to the prediction
    
    Why coefficients (fallback)?
    - Interpretable: Shows feature importance
    - Fast: No additional computation needed
    
    Args:
        row: Single transaction row (Series)
        use_shap: If True, use SHAP explanations (default). If False, use coefficients.
        
    Returns:
        List of explanation strings
    """
    global _model, _scaler, _feature_names, _shap_explainer
    
    explanations = []
    
    # Try SHAP first if available and model exists
    if use_shap and SHAP_AVAILABLE and _model is not None and _scaler is not None and _feature_names is not None and _shap_explainer is not None:
        try:
            # Prepare feature vector for this transaction
            feature_values = []
            for feat in _feature_names:
                if feat in row.index:
                    val = row[feat]
                    if pd.isna(val):
                        if feat in ["is_high_risk_merchant", "is_emulator_device"]:
                            val = False
                        else:
                            val = 0
                    elif isinstance(val, bool):
                        val = int(val)
                    feature_values.append(val)
                else:
                    feature_values.append(0)
            
            # Scale features (same as training)
            feature_array = np.array([feature_values])
            feature_scaled = _scaler.transform(feature_array)
            
            # Calculate SHAP values with error handling
            # Use try-except to catch any SHAP computation errors
            try:
                shap_values = _shap_explainer.shap_values(feature_scaled[0])
            except Exception as shap_error:
                # If SHAP fails, fall through to coefficient-based explanation
                raise shap_error
            
            # Handle SHAP output format (LinearExplainer returns array)
            if isinstance(shap_values, np.ndarray):
                if len(shap_values.shape) > 1:
                    shap_values = shap_values[0]  # Get first (and only) sample
            
            # Create feature importance pairs
            feature_importance = list(zip(_feature_names, shap_values, feature_values))
            
            # Sort by absolute SHAP value (most important features first)
            feature_importance.sort(key=lambda x: abs(x[1]), reverse=True)
            
            # Generate explanations from SHAP values
            for feat, shap_val, value in feature_importance:
                if abs(shap_val) > 0.001:  # Only show meaningful contributions
                    direction = "increases" if shap_val > 0 else "decreases"
                    impact = abs(shap_val) * 100  # Convert to percentage-like impact
                    
                    # Format feature-specific explanations with statistical context
                    if feat == "txns_last_24h":
                        # Add context: typical fraud patterns show >10 txns/24h
                        context = " (High velocity - typical fraud pattern)" if value > 10 else " (Normal velocity)"
                        explanations.append(
                            f"**Transaction Velocity** (SHAP: {shap_val:+.3f}): "
                            f"{direction} fraud probability by {impact:.1f}% - "
                            f"{value:.0f} transactions in last 24h{context}"
                        )
                    elif feat == "declined_txns_last_24h":
                        # Add context: >2 declines suggests card testing
                        context = " (Card testing pattern detected)" if value > 2 else " (Normal decline rate)"
                        explanations.append(
                            f"**Decline History** (SHAP: {shap_val:+.3f}): "
                            f"{direction} fraud probability by {impact:.1f}% - "
                            f"{value:.0f} declined transactions{context}"
                        )
                    elif feat == "merchant_fraud_rate_30d":
                        # Add context: >10% is high risk merchant
                        context = " (High-risk merchant)" if value > 0.1 else " (Normal merchant risk)"
                        explanations.append(
                            f"**Merchant Fraud Rate** (SHAP: {shap_val:+.3f}): "
                            f"{direction} fraud probability by {impact:.1f}% - "
                            f"{value*100:.1f}% historical fraud rate{context}"
                        )
                    elif feat == "is_high_risk_merchant":
                        status = "Yes" if value else "No"
                        explanations.append(
                            f"**High-Risk Merchant Flag** (SHAP: {shap_val:+.3f}): "
                            f"{direction} fraud probability by {impact:.1f}% - "
                            f"Merchant risk tier: {status}"
                        )
                    elif feat == "is_emulator_device":
                        status = "Yes" if value else "No"
                        explanations.append(
                            f"**Emulator Device** (SHAP: {shap_val:+.3f}): "
                            f"{direction} fraud probability by {impact:.1f}% - "
                            f"Emulator detected: {status}"
                        )
                    else:
                        explanations.append(
                            f"**{feat.replace('_', ' ').title()}** (SHAP: {shap_val:+.3f}): "
                            f"{direction} fraud probability by {impact:.1f}% - Value: {value}"
                        )
            
            if not explanations:
                explanations.append("SHAP analysis: No significant feature contributions identified")
                
        except Exception as e:
            # Fallback to coefficients if SHAP fails
            # Log the error but continue to coefficient-based explanation
            explanations = []
            # Continue to coefficient-based explanation below
            pass
    
    # Fallback: Use coefficients if SHAP not available or failed
    # Only use coefficients if SHAP didn't produce explanations
    if not explanations and _model is not None and _feature_names is not None:
        # Get feature values for this transaction
        feature_values = {}
        for feat in _feature_names:
            if feat in row.index:
                val = row[feat]
                if pd.isna(val):
                    # Default based on feature name (heuristic)
                    if feat in ["is_high_risk_merchant", "is_emulator_device"]:
                        val = False
                    else:
                        val = 0
                elif isinstance(val, bool):
                    val = int(val)
                feature_values[feat] = val
            else:
                feature_values[feat] = 0
        
        # Get coefficients (feature importance)
        coefficients = _model.coef_[0]
        
        # Create feature importance pairs
        feature_importance = list(zip(_feature_names, coefficients, 
                                      [feature_values.get(f, 0) for f in _feature_names]))
        
        # Sort by absolute coefficient (most important features first)
        feature_importance.sort(key=lambda x: abs(x[1]), reverse=True)
        
        # Generate explanations from all contributing features
        # Sort by absolute coefficient to show most important first
        # Always show at least top 3 features, even if coefficients are small
        shown_count = 0
        for feat, coef, value in feature_importance:
            # Show all features - lower threshold to ensure we show something
            # Even small coefficients can be meaningful when combined
            if abs(coef) > 0.0001 or shown_count < 3:  # Show top 3 or significant features
                direction = "increases" if coef > 0 else "decreases"
                # Show coefficient magnitude as relative importance
                coef_magnitude = abs(coef)
                importance_level = "high" if coef_magnitude > 0.5 else ("medium" if coef_magnitude > 0.2 else "low")
                
                # Format feature-specific explanations with statistical context
                if feat == "txns_last_24h":
                    context = " (High velocity - typical fraud pattern)" if value > 10 else " (Normal velocity)"
                    explanations.append(
                        f"**Transaction Velocity** ({importance_level} impact): "
                        f"{direction} fraud risk - {value:.0f} transactions in last 24h{context} "
                        f"[Coefficient: {coef:.3f}]"
                    )
                elif feat == "declined_txns_last_24h":
                    explanations.append(
                        f"**Decline History** ({importance_level} impact): "
                        f"{direction} fraud risk - {value:.0f} declined transactions "
                        f"[Coefficient: {coef:.3f}]"
                    )
                elif feat == "merchant_fraud_rate_30d":
                    explanations.append(
                        f"**Merchant Fraud Rate** ({importance_level} impact): "
                        f"{direction} fraud risk - {value*100:.1f}% historical fraud rate "
                        f"[Coefficient: {coef:.3f}]"
                    )
                elif feat == "is_high_risk_merchant":
                    status = "Yes" if value else "No"
                    explanations.append(
                        f"**High-Risk Merchant Flag** ({importance_level} impact): "
                        f"{direction} fraud risk - Merchant risk tier: {status} "
                        f"[Coefficient: {coef:.3f}]"
                    )
                elif feat == "is_emulator_device":
                    status = "Yes" if value else "No"
                    explanations.append(
                        f"**Emulator Device** ({importance_level} impact): "
                        f"{direction} fraud risk - Emulator detected: {status} "
                        f"[Coefficient: {coef:.3f}]"
                    )
                else:
                    # Generic explanation for any other features
                    explanations.append(
                        f"**{feat.replace('_', ' ').title()}** ({importance_level} impact): "
                        f"{direction} fraud risk - Value: {value} [Coefficient: {coef:.3f}]"
                    )
                shown_count += 1
        
        # Always show at least the top 3 features, even if coefficients are small
        if not explanations and len(feature_importance) > 0:
            # Show top 3 features regardless of coefficient size
            for feat, coef, value in feature_importance[:3]:
                direction = "increases" if coef > 0 else "decreases"
                coef_magnitude = abs(coef)
                importance_level = "high" if coef_magnitude > 0.5 else ("medium" if coef_magnitude > 0.2 else "low")
                
                if feat == "txns_last_24h":
                    context = " (High velocity - typical fraud pattern)" if value > 10 else " (Normal velocity)"
                    explanations.append(
                        f"**Transaction Velocity** ({importance_level} impact): "
                        f"{direction} fraud risk - {value:.0f} transactions in last 24h{context} "
                        f"[Coefficient: {coef:.3f}]"
                    )
                elif feat == "declined_txns_last_24h":
                    context = " (Card testing pattern detected)" if value > 2 else " (Normal decline rate)"
                    explanations.append(
                        f"**Decline History** ({importance_level} impact): "
                        f"{direction} fraud risk - {value:.0f} declined transactions{context} "
                        f"[Coefficient: {coef:.3f}]"
                    )
                elif feat == "merchant_fraud_rate_30d":
                    context = " (High-risk merchant)" if value > 0.1 else " (Normal merchant risk)"
                    explanations.append(
                        f"**Merchant Fraud Rate** ({importance_level} impact): "
                        f"{direction} fraud risk - {value*100:.1f}% historical fraud rate{context} "
                        f"[Coefficient: {coef:.3f}]"
                    )
                elif feat == "is_high_risk_merchant":
                    status = "Yes" if value else "No"
                    explanations.append(
                        f"**High-Risk Merchant Flag** ({importance_level} impact): "
                        f"{direction} fraud risk - Merchant risk tier: {status} "
                        f"[Coefficient: {coef:.3f}]"
                    )
                elif feat == "is_emulator_device":
                    status = "Yes" if value else "No"
                    explanations.append(
                        f"**Emulator Device** ({importance_level} impact): "
                        f"{direction} fraud risk - Emulator detected: {status} "
                        f"[Coefficient: {coef:.3f}]"
                    )
                else:
                    explanations.append(
                        f"**{feat.replace('_', ' ').title()}** ({importance_level} impact): "
                        f"{direction} fraud risk - Value: {value} [Coefficient: {coef:.3f}]"
                    )
        
        if not explanations:
            explanations.append("Model analysis: Unable to generate feature explanations. Check model training status.")
    
    else:
        # Fallback: Rule-based explanations if model not available
        if "txns_last_24h" in row and pd.notna(row["txns_last_24h"]) and row["txns_last_24h"] > 10:
            explanations.append(f"High transaction velocity: {row['txns_last_24h']:.0f} transactions in the last 24 hours")
        
        if "declined_txns_last_24h" in row and pd.notna(row["declined_txns_last_24h"]) and row["declined_txns_last_24h"] > 2:
            explanations.append(f"Multiple declined transactions: {row['declined_txns_last_24h']:.0f} in the last 24 hours")
        
        if "is_high_risk_merchant" in row and row.get("is_high_risk_merchant", False):
            explanations.append("Merchant is flagged as high-risk tier")
        
        if "is_emulator_device" in row and row.get("is_emulator_device", False):
            explanations.append("Transaction originated from an emulator device")
        
        if "merchant_fraud_rate_30d" in row and pd.notna(row["merchant_fraud_rate_30d"]) and row["merchant_fraud_rate_30d"] > 0.1:
            explanations.append(f"Merchant has elevated fraud rate: {row['merchant_fraud_rate_30d']*100:.1f}% in last 30 days")
        
        if not explanations:
            explanations.append("No significant risk factors identified")
    
    return explanations


def get_shap_values(row: pd.Series) -> dict:
    """
    Get SHAP values for a transaction (for visualization).
    
    Args:
        row: Single transaction row (Series)
        
    Returns:
        Dictionary with SHAP values and feature names, or None if SHAP not available
    """
    global _model, _scaler, _feature_names, _shap_explainer
    
    if not SHAP_AVAILABLE or _model is None or _scaler is None or _feature_names is None or _shap_explainer is None:
        return None
    
    try:
        # Prepare feature vector
        feature_values = []
        for feat in _feature_names:
            if feat in row.index:
                val = row[feat]
                if pd.isna(val):
                    val = 0 if feat not in ["is_high_risk_merchant", "is_emulator_device"] else False
                if isinstance(val, bool):
                    val = int(val)
                feature_values.append(val)
            else:
                feature_values.append(0)
        
        # Scale and get SHAP values
        feature_array = np.array([feature_values])
        feature_scaled = _scaler.transform(feature_array)
        shap_values = _shap_explainer.shap_values(feature_scaled[0])
        
        if isinstance(shap_values, np.ndarray) and len(shap_values.shape) > 1:
            shap_values = shap_values[0]
        
        return {
            "feature_names": _feature_names,
            "shap_values": shap_values.tolist() if isinstance(shap_values, np.ndarray) else shap_values,
            "feature_values": feature_values,
            "base_value": float(_shap_explainer.expected_value) if hasattr(_shap_explainer, 'expected_value') else 0.0
        }
    except Exception as e:
        return None


def get_model_info() -> dict:
    """
    Get information about the trained model.
    
    Returns:
        Dictionary with model information (feature names, coefficients, etc.)
    """
    global _model, _feature_names
    
    if _model is None or _feature_names is None:
        return {"status": "No model trained"}
    
    coefficients = _model.coef_[0] if _model.coef_ is not None else []
    
    return {
        "status": "Model trained",
        "features": _feature_names,
        "coefficients": dict(zip(_feature_names, coefficients.tolist())),
        "intercept": float(_model.intercept_[0]) if _model.intercept_ is not None else None
    }

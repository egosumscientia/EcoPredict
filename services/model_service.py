import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, precision_score, recall_score, f1_score
from sklearn.preprocessing import StandardScaler
from datetime import datetime, timezone, timedelta


def _get_lags_for_target(target: str):
    """
    Return a tuple of lags depending on the target variable.
    """
    custom = {
        "relative_humidity_2m": (1, 2, 3, 6),
        "pressure_msl": (1, 2, 3, 6),
        "wind_speed_10m": (1, 2),
    }
    return custom.get(target, (1, 2, 3))


def _add_lag_features(df: pd.DataFrame, target: str) -> pd.DataFrame:
    """
    Adds lagged versions of the target to capture short-term autocorrelation.
    Drops rows made NaN by the shifts.
    """
    df = df.copy()
    for lag in _get_lags_for_target(target):
        df[f"{target}_lag{lag}"] = df[target].shift(lag)
    df = df.dropna().reset_index(drop=True)
    return df


def train_and_predict(df: pd.DataFrame, target="temperature_2m", retrain=False):
    """
    Trains a blended LR + RandomForest model with lag features on past data
    and predicts the next 24 hours (or available future rows) using forecast features.
    Returns predictions, MAE (vs futuros conocidos) y los valores reales/timestamps del horizonte futuro.
    """

    if target not in df.columns:
        raise ValueError(f"Variable '{target}' not found in dataset")

    df_aug = _add_lag_features(df, target)

    # Use all columns except target and time as features (includes lags)
    features = [col for col in df_aug.columns if col not in ["time", target]]
    X = df_aug[features]
    y = df_aug[target]

    if X.empty or y.empty:
        print(f"?? No data available for {target} after lagging.")
        return {
            "predictions": [],
            "mae": None,
            "actual": [],
            "timestamps": [],
        }

    # Split past vs future based on current UTC time
    now_utc = datetime.utcnow().replace(tzinfo=timezone.utc)
    times_utc = pd.to_datetime(df_aug["time"], utc=True)

    df_past = df_aug.loc[times_utc < now_utc]
    df_future = df_aug.loc[times_utc >= now_utc]

    # Past observed (últimas 24h reales)
    obs_tail = df_past.tail(24)
    obs_past = obs_tail[target] if not obs_tail.empty else pd.Series([], dtype=float)
    obs_past_ts = obs_tail["time"] if not obs_tail.empty else pd.Series([], dtype=str)

    # Futuro: limitar a próximas 24 filas
    df_future = df_future.head(24)

    # Si no hay futuro, usar filas recientes como fallback, pero no mezclar con pasado observado
    if df_future.empty:
        df_future = df_aug.tail(24)
        df_past = df_aug.iloc[:-len(df_future)] if len(df_aug) > len(df_future) else df_aug.head(0)

    X_train = df_past[features]
    y_train = df_past[target]
    X_future = df_future[features]
    y_future = df_future[target]

    # Transform target for precipitation to handle skew/zeros
    transform_target = target == "precipitation"
    rain_metrics = None
    rain_threshold = 0.05  # mm (ligera llovizna)
    if transform_target:
        y_train_model = np.log1p(np.clip(y_train, a_min=0, a_max=None))
    else:
        y_train_model = y_train

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_future_scaled = scaler.transform(X_future)

    lr = LinearRegression()
    rf = RandomForestRegressor(n_estimators=200, random_state=42)

    lr.fit(X_train_scaled, y_train_model)
    rf.fit(X_train, y_train_model)  # RF no necesita escalado

    preds_lr = lr.predict(X_future_scaled)
    preds_rf = rf.predict(X_future)
    blended = (preds_lr + preds_rf) / 2

    if transform_target:
        blended = np.expm1(blended)
        blended = np.clip(blended, a_min=0, a_max=None)

        # Classification metrics for rain/no rain and thresholded regression output
        y_true_rain = (y_future > rain_threshold).astype(int)
        y_pred_rain = (blended > rain_threshold).astype(int)

        rain_metrics = {
            "threshold": rain_threshold,
            "precision": precision_score(y_true_rain, y_pred_rain, zero_division=0),
            "recall": recall_score(y_true_rain, y_pred_rain, zero_division=0),
            "f1": f1_score(y_true_rain, y_pred_rain, zero_division=0),
        }

        # Force small values to zero for the regression output
        blended = np.where(blended < rain_threshold, 0.0, blended)

    mae_test = mean_absolute_error(y_future, blended) if len(y_future) else None
    if mae_test is not None:
        print(f"Future MAE (next horizon) for {target}: {mae_test:.3f}")
    else:
        print(f"No MAE computed for {target}.")

    return {
        "predictions": blended.tolist(),
        "mae": mae_test,
        "actual": y_future.tolist(),
        "timestamps": df_future["time"].astype(str).tolist(),
        "rain_metrics": rain_metrics,
        "observed_past": obs_past.tolist(),
        "observed_timestamps": obs_past_ts.astype(str).tolist(),
    }

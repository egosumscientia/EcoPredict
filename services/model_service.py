import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error


def train_and_predict(df: pd.DataFrame, target="temperature_2m", retrain=False):
    """
    Train blended Linear Regression + Random Forest model
    to predict the selected weather variable for all available hours.
    """

    if target not in df.columns:
        raise ValueError(f"Variable '{target}' not found in dataset")

    # Use all other features except the target and time
    features = [col for col in df.columns if col not in ["time", target]]
    X = df[features]
    y = df[target]

    if X.empty or y.empty:
        print(f"⚠️ No data available for {target}.")
        return [None] * 24  # placeholder array

    # Train using all data (demo mode)
    lr = LinearRegression()
    rf = RandomForestRegressor(n_estimators=100, random_state=42)

    lr.fit(X, y)
    rf.fit(X, y)

    preds_lr = lr.predict(X)
    preds_rf = rf.predict(X)
    blended = (preds_lr + preds_rf) / 2

    # Compute approximate error on same data (demo mode)
    mae = mean_absolute_error(y, blended)
    print(f"MAE for {target}: {mae:.3f}")

    # Return last 24 predictions (simulating 24h forecast)
    if len(blended) > 24:
        blended = blended[-24:]

    return blended.tolist()

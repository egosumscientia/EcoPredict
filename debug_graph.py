
import pandas as pd
from datetime import datetime, timezone
import sys
import os

# Adjust path to import services
sys.path.append(os.getcwd())

from services.model_service import train_and_predict

# Mock data creation
def create_mock_data():
    # Generate hourly timestamps around "now"
    # User's local time is approx 2025-12-24 16:28-05:00 -> 21:28 UTC
    # Let's create data from 12:00 UTC to 23:00 UTC
    times = pd.date_range(start="2025-12-24 12:00", end="2025-12-24 23:00", freq="H")
    
    # Create simple dataframe
    df = pd.DataFrame({
        "time": times,
        "temperature_2m": [20 + i for i in range(len(times))],
        "relative_humidity_2m": [50] * len(times),
        "pressure_msl": [1013] * len(times),
        "precipitation": [0] * len(times),
        "wind_speed_10m": [5] * len(times)
    })
    return df

def debug_filtering():
    print("--- Debugging Filtering Logic ---")
    df = create_mock_data()
    
    print("Mock Data (Tail):")
    print(df.tail(5))
    
    now_utc = datetime.utcnow().replace(tzinfo=timezone.utc)
    print(f"\nCurrent UTC Time (Python): {now_utc}")
    
    # Simulate logic from model_service.py
    # Note: verify if the time column in df needs to be string or datetime
    # In weather_service.py it's converted to datetime: df_all["time"] = pd.to_datetime(df_all["time"])
    # But here created with pd.date_range so it already is datetime64[ns]
    
    # Replicate model_service.py lines 61-65
    target = "temperature_2m"
    
    # Need to add lags as train_and_predict does
    # But let's just inspect the logic directly first
    
    times_utc = pd.to_datetime(df["time"], utc=True)
    
    df_past = df.loc[times_utc < now_utc]
    df_future = df.loc[times_utc >= now_utc]
    
    print(f"\nPast DataFrame (Last 3):")
    print(df_past.tail(3))
    
    print(f"\nFuture DataFrame (First 3):")
    print(df_future.head(3))
    
    # Check specifically if 22:00 is in past
    is_22_in_past = False
    if not df_past.empty:
        last_past_time = df_past.iloc[-1]["time"]
        # Convert to pydatetime if needed
        # Depending on pandas version, it might be Timestamp
        print(f"\nLast Past Timestamp: {last_past_time}")
        
    # Also run the actual function to see what it returns
    print("\n--- Running train_and_predict ---")
    try:
        result = train_and_predict(df, target=target)
        obs_timestamps = result["observed_timestamps"]
        print("Observed Timestamps returned by API:")
        print(obs_timestamps[-5:])
    except Exception as e:
        print(f"Error running train_and_predict: {e}")

if __name__ == "__main__":
    debug_filtering()

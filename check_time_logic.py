
import pandas as pd
from datetime import datetime, timezone

def check():
    # 1. Setup Time
    now_utc = datetime.utcnow().replace(tzinfo=timezone.utc)
    print(f"Now UTC: {now_utc}")
    
    # 2. Create Data
    # Simulate data around the current hour
    # If now is 21:30, we create 20:00, 21:00, 22:00, 23:00
    current_hour = now_utc.hour
    base_date = now_utc.strftime("%Y-%m-%d")
    
    times_str = [
        f"{base_date} {current_hour-1:02d}:00:00",
        f"{base_date} {current_hour:02d}:00:00",
        f"{base_date} {current_hour+1:02d}:00:00",
        f"{base_date} {current_hour+2:02d}:00:00"
    ]
    
    df = pd.DataFrame({"time": times_str, "val": [1, 2, 3, 4]})
    
    # 3. Simulate Weather Service parsing
    df["time"] = pd.to_datetime(df["time"])
    print("\nDataframe Naive Times:")
    print(df)
    
    # 4. Simulate Model Service Filtering
    times_utc = pd.to_datetime(df["time"], utc=True)
    print("\nTimes UTC Series:")
    print(times_utc)
    
    df_past = df.loc[times_utc < now_utc]
    df_future = df.loc[times_utc >= now_utc]
    
    print("\nPast Data (Should exclude future hours):")
    print(df_past)
    
    print("\nFuture Data:")
    print(df_future)
    
    # Check if any future hour leaked into past
    if not df_future.empty:
        future_start = df_future.iloc[0]["time"]
        # naive comparison
        # if df_past has something >= future_start
        pass

if __name__ == "__main__":
    check()

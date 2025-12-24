
import pandas as pd
from datetime import datetime, timezone
import sys
import os

# Adjust path
sys.path.append(os.getcwd())

from services.weather_service import fetch_weather_data

def check_real():
    print("--- Checking Real Data from Service ---")
    
    # Bogota coordinates
    lat, lon = 4.61, -74.08
    
    try:
        df = fetch_weather_data(lat, lon)
        print(f"Fetched {len(df)} rows.")
        
        # Check last few rows
        print("Last 10 rows of raw data:")
        print(df.tail(10)[["time", "temperature_2m"]])
        
        now_utc = datetime.utcnow().replace(tzinfo=timezone.utc)
        print(f"\nNow UTC: {now_utc}")
        
        # Check filtering logic on this real data
        times_utc = pd.to_datetime(df["time"], utc=True)
        
        df_past = df.loc[times_utc < now_utc]
        df_future = df.loc[times_utc >= now_utc]
        
        print("\nReal Past Data (Tail):")
        if not df_past.empty:
            print(df_past.tail(5)[["time", "temperature_2m"]])
        else:
            print("Past data is empty")
            
        print("\nReal Future Data (Head):")
        if not df_future.empty:
            print(df_future.head(5)[["time", "temperature_2m"]])
        else:
            print("Future data is empty")

        # Explicitly check for leakage
        if not df_past.empty:
            last_past_time = df_past.iloc[-1]["time"]
            # Convert to aware if needed for display/comparison logic validation
            # But the 'time' column is naive in the DF usually
            print(f"\nLast timestamp in 'Observed' would be: {last_past_time}")
            
            # Is this > now?
            # We need to manually compare naive(last_past_time) vs naive(now_utc) or aware vs aware
            last_past_aware = pd.to_datetime(last_past_time).tz_localize("UTC")
            print(f"Is {last_past_aware} < {now_utc}? {last_past_aware < now_utc}")
            
    except Exception as e:
        print(f"Error fetching data: {e}")

if __name__ == "__main__":
    check_real()

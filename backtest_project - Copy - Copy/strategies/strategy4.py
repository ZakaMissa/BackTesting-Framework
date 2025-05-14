import pandas as pd
import numpy as np

def generate_signals(df):
    """
    Generate trading signals based on range contraction and 200-day SMA.
    Returns DataFrame with Date, Close, Signal (1=Buy, -1=Sell, 0=Hold), and EquityCurve columns.
    """
    # Make a copy to avoid modifying the original
    df = df.copy()
    
    # Ensure we're working with a proper DatetimeIndex
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
    
    # Calculate indicators
    df["Range"] = df["High"] - df["Low"]
    df["Min_Range_6D"] = df["Range"].shift(1).rolling(window=6).min()
    df["SMA_200"] = df["Close"].rolling(window=200).mean()
    
    # Drop NaN values and create a fresh copy to avoid alignment issues
    df = df.dropna().copy()

    # Define Buy & Sell conditions
    buy_condition = (df["Range"] < df["Min_Range_6D"]) & (df["Close"] > df["SMA_200"])
    sell_condition = df["Close"] > df["High"].shift(1)
    
    # Initialize Signal column with zeros
    df["Signal"] = 0
    
    # Implement strict position tracking to ensure we get a clean buy/sell pattern
    in_position = False
    
    # Process one bar at a time and set signals
    for i in range(len(df)):
        # Only consider a buy if we're not in a position and buy condition is met
        if not in_position and buy_condition.iloc[i]:
            df.iloc[i, df.columns.get_loc("Signal")] = 1  # Signal a buy
            in_position = True
        # Only consider a sell if we are in a position and sell condition is met
        elif in_position and sell_condition.iloc[i]:
            df.iloc[i, df.columns.get_loc("Signal")] = -1  # Signal a sell
            in_position = False
        # All other cases get a zero signal
        else:
            df.iloc[i, df.columns.get_loc("Signal")] = 0
    
    # Calculate equity curve (starting with $1)
    df["EquityCurve"] = 1.0
    in_position = False
    entry_price = 0
    
    for i in range(1, len(df)):
        # Check for buy signal
        if df["Signal"].iloc[i-1] == 1:
            in_position = True
            entry_price = df["Close"].iloc[i-1]
            df.iloc[i, df.columns.get_loc("EquityCurve")] = df["EquityCurve"].iloc[i-1]
        # Check for sell signal
        elif df["Signal"].iloc[i-1] == -1 and in_position:
            in_position = False
            exit_price = df["Close"].iloc[i-1]
            pct_change = (exit_price - entry_price) / entry_price
            df.iloc[i, df.columns.get_loc("EquityCurve")] = df["EquityCurve"].iloc[i-1] * (1 + pct_change)
        # No signal or already in position
        else:
            df.iloc[i, df.columns.get_loc("EquityCurve")] = df["EquityCurve"].iloc[i-1]
    
    # Ensure we have a Date column (from index)
    df = df.reset_index()
    df = df.rename(columns={"index": "Date"})
    
    # Return only required columns
    return df[["Date", "Close", "Signal", "EquityCurve"]]

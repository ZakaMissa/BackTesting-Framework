import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def get_data(ticker):
    """
    Downloads historical stock data for the given ticker using yfinance.
    
    Args:
        ticker (str): Stock ticker symbol (e.g., 'SPY', 'AAPL')
        
    Returns:
        pd.DataFrame: DataFrame with OHLCV data and datetime index
        
    Raises:
        ValueError: If ticker is invalid or data cannot be downloaded
    """
    try:
        # Download 20 years of daily data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365*20)
        
        df = yf.download(
            ticker,
            start=start_date,
            end=end_date,
            progress=False
        )
        
        if df.empty:
            raise ValueError(f"No data found for ticker {ticker}")
            
        # Fix for multi-index columns
        if isinstance(df.columns, pd.MultiIndex):
            # Select the level we need, typically 'Price' or 'Adj Close'
            for level in df.columns.names:
                if level is not None and level != 'Ticker':
                    price_level = level
                    break
            else:
                # If none found, get first column level
                price_level = df.columns.names[0]
            
            # Get the OHLCV columns without the multi-index
            df = df.xs(ticker, level='Ticker', axis=1) if 'Ticker' in df.columns.names else df
        
        # Ensure we have all required columns
        required_columns = ["Open", "High", "Low", "Close", "Volume"]
        if not all(col in df.columns for col in required_columns):
            raise ValueError(f"Missing required columns for {ticker}")
            
        # Clean the data
        df = df[required_columns]  # Keep only required columns
        df = df.dropna()  # Remove rows with missing values
        
        # Ensure index is datetime
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
            
        return df
        
    except Exception as e:
        raise ValueError(f"Error downloading data for {ticker}: {str(e)}")

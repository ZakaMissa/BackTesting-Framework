# backtest.py

# These are built-in libraries that help us do important stuff:
import argparse         # lets us read values like --ticker AAPL from the command line
import importlib        # helps us load the strategy file chosen by the user
import pandas as pd     # used for working with tables (like Excel in Python)
import numpy as np      # used for math stuff
import matplotlib.pyplot as plt  # used for plotting graphs
from scipy import stats

# We import our custom function from the utils folder
from utils import get_data

# -----------------------------------------------------
# This function calculates all the stats like return, Sharpe ratio, etc.
# -----------------------------------------------------
def calculate_metrics(df):
    """Calculate comprehensive trading performance metrics."""
    # Check if we have any signal changes
    signal_changes = df["Signal"].diff().fillna(0)
    entries = signal_changes[signal_changes == 1].index
    exits = signal_changes[signal_changes == -2].index
    
    if len(entries) == 0 or len(exits) == 0:
        print("⚠️ No trades executed.")
        return None

    # Calculate total return from equity curve
    start_equity = df["EquityCurve"].iloc[0]
    end_equity = df["EquityCurve"].iloc[-1]
    total_return = (end_equity / start_equity) - 1
    
    # Calculate trade stats
    num_years = (df["Date"].iloc[-1] - df["Date"].iloc[0]).days / 365
    cagr = (1 + total_return) ** (1 / num_years) - 1
    
    # Calculate Sharpe Ratio (daily returns)
    df["Daily_Return"] = df["EquityCurve"].pct_change().fillna(0)
    avg_daily_return = df["Daily_Return"].mean()
    daily_std = df["Daily_Return"].std()
    sharpe_ratio = np.sqrt(252) * avg_daily_return / daily_std
    
    # Calculate max drawdown
    df["Peak"] = df["EquityCurve"].cummax()
    df["Drawdown"] = (df["EquityCurve"] - df["Peak"]) / df["Peak"]
    max_drawdown = df["Drawdown"].min()
    
    # Calculate win rate and profit factor
    trades = []
    position = 0
    entry_price = 0
    entry_date = None
    
    for i in range(len(df)):
        if df["Signal"].iloc[i] == 1 and position == 0:
            position = 1
            entry_price = df["Close"].iloc[i]
            entry_date = df["Date"].iloc[i]
        elif df["Signal"].iloc[i] == -1 and position == 1:
            position = 0
            exit_price = df["Close"].iloc[i]
            exit_date = df["Date"].iloc[i]
            trades.append({
                "Entry Date": entry_date,
                "Exit Date": exit_date,
                "Entry Price": entry_price,
                "Exit Price": exit_price,
                "Return %": (exit_price - entry_price) / entry_price * 100
            })
    
    trades_df = pd.DataFrame(trades)
    if len(trades_df) == 0:
        print("⚠️ No complete trades found.")
        return None
        
    win_rate = (trades_df["Return %"] > 0).mean()
    profits = trades_df[trades_df["Return %"] > 0]["Return %"].sum()
    losses = abs(trades_df[trades_df["Return %"] < 0]["Return %"].sum())
    profit_factor = profits / losses if losses != 0 else float('inf')
    
    # Calculate average trade metrics
    avg_trade = trades_df["Return %"].mean()
    avg_win = trades_df[trades_df["Return %"] > 0]["Return %"].mean() if len(trades_df[trades_df["Return %"] > 0]) > 0 else 0
    avg_loss = trades_df[trades_df["Return %"] < 0]["Return %"].mean() if len(trades_df[trades_df["Return %"] < 0]) > 0 else 0
    
    # Print results
    metrics = {
        "Total Trades": len(trades_df),
        "Total Return": f"{total_return:.2%}",
        "CAGR": f"{cagr:.2%}",
        "Sharpe Ratio": f"{sharpe_ratio:.2f}",
        "Max Drawdown": f"{max_drawdown:.2%}",
        "Win Rate": f"{win_rate:.2%}",
        "Profit Factor": f"{profit_factor:.2f}",
        "Avg Trade": f"{avg_trade:.2f}%",
        "Avg Win": f"{avg_win:.2f}%",
        "Avg Loss": f"{avg_loss:.2f}%",
        "Volatility (Ann.)": f"{daily_std * np.sqrt(252):.2%}"
    }
    
    print("\n📈 Performance Metrics:")
    for metric, value in metrics.items():
        print(f"{metric:<20}: {value}")
    
    return metrics, trades_df

# -----------------------------------------------------
# This function draws the equity curve (like a performance chart)
# -----------------------------------------------------
# -----------------------------------------------------
# This function draws the equity curve (like a performance chart)
# -----------------------------------------------------
def plot_equity_curve(df):
    """Plot equity curve with buy/sell markers and drawdown."""
    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(12, 8), gridspec_kw={'height_ratios': [3, 1]}
    )

    # -- Plot equity curve line --
    ax1.plot(df["Date"], df["EquityCurve"], label="Equity Curve", linewidth=2)

    # -- Find entry and exit points directly from Signal column --
    buy_mask  = df["Signal"] == 1
    sell_mask = df["Signal"] == -1

    buys  = df.loc[buy_mask,  ["Date", "EquityCurve"]]
    sells = df.loc[sell_mask, ["Date", "EquityCurve"]]

    # Scatter buys & sells
    if not buys.empty:
        ax1.scatter(
            buys["Date"], buys["EquityCurve"],
            marker="^", color="green", s=100, label="Buy"
        )
    if not sells.empty:
        ax1.scatter(
            sells["Date"], sells["EquityCurve"],
            marker="v", color="red", s=100, label="Sell"
        )

    ax1.set_title("Equity Curve")
    ax1.set_ylabel("Equity")
    ax1.grid(True)

    # Custom legend
    handles = [
        plt.Line2D([0], [0], color='blue', linewidth=2),
        plt.Line2D([0], [0], marker='^', color='w',
                   markerfacecolor='green', markersize=10),
        plt.Line2D([0], [0], marker='v', color='w',
                   markerfacecolor='red', markersize=10),
    ]
    labels = ["Equity Curve", "Buy", "Sell"]
    ax1.legend(handles, labels)

    # -- Plot drawdown --
    df["Peak"]     = df["EquityCurve"].cummax()
    df["Drawdown"] = (df["EquityCurve"] - df["Peak"]) / df["Peak"]
    ax2.fill_between(df["Date"], df["Drawdown"], 0, color="red", alpha=0.3)

    ax2.set_title("Drawdown")
    ax2.set_xlabel("Date")
    ax2.set_ylabel("Drawdown")
    ax2.grid(True)

    plt.tight_layout()
    plt.show()


# -----------------------------------------------------
# This is the main function that runs everything
# -----------------------------------------------------
def main(ticker, strategy_name):
    """Main backtesting function."""
    print(f"🔍 Getting {ticker} data...")
    
    # Get price data
    df = get_data.get_data(ticker)
    
    # Load and run strategy
    print(f"📊 Applying strategy: {strategy_name}")
    strategy_module = importlib.import_module(f"strategies.{strategy_name}")
    strategy_df = strategy_module.generate_signals(df.copy())
    
    # Calculate and display metrics
    result = calculate_metrics(strategy_df)
    
    if result is None:
        print("No trades were executed. Try a different ticker or strategy.")
        return None, None, strategy_df
    
    metrics, trades_df = result
    
    # Plot results
    plot_equity_curve(strategy_df)

    
    
    return metrics, trades_df, strategy_df
def calculate_monthly_returns(strategy_df):
    """Generate a DataFrame of monthly returns with Year, Jan-Dec, StratReturns, and bh_returns."""
    df = strategy_df.copy()
    df["Year"] = df["Date"].dt.year
    df["Month"] = df["Date"].dt.month

    # Strategy monthly returns
    df["Daily_Return"] = df["EquityCurve"].pct_change()
    monthly_returns = df.groupby(["Year", "Month"])["Daily_Return"].apply(lambda x: (x + 1).prod() - 1).unstack()

    # Buy and hold monthly returns
    df["BH_Daily"] = df["Close"].pct_change()
    bh_returns = df.groupby(["Year", "Month"])["BH_Daily"].apply(lambda x: (x + 1).prod() - 1).unstack()

    # Format month columns
    monthly_returns.columns = [pd.to_datetime(str(m), format="%m").strftime("%b") for m in monthly_returns.columns]
    bh_returns.columns = [pd.to_datetime(str(m), format="%m").strftime("%b") for m in bh_returns.columns]

    monthly_returns["StratReturns"] = monthly_returns.sum(axis=1)
    bh_returns["bh_returns"] = bh_returns.sum(axis=1)

    final_df = monthly_returns.merge(bh_returns[["bh_returns"]], left_index=True, right_index=True)
    final_df = final_df.reset_index()
    return final_df

# -----------------------------------------------------
# This lets us run the program from command line
# -----------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run backtest on any ticker with any strategy.")
    parser.add_argument("--ticker", type=str, required=True, help="Ticker symbol (e.g., SPY, AAPL, TSLA)")
    parser.add_argument("--strategy", type=str, required=True, help="Strategy name without .py (e.g., strategy1)")
    args = parser.parse_args()
    main(args.ticker, args.strategy)


   
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import importlib
import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
from backtest import calculate_monthly_returns
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the backtest module
import backtest

class BacktestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Backtesting System")
        self.root.geometry("800x700")
        self.root.minsize(800, 700)

        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        input_frame = ttk.LabelFrame(main_frame, text="Backtest Parameters", padding="10")
        input_frame.pack(fill=tk.X, pady=10)

        ttk.Label(input_frame, text="Ticker Symbol:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.ticker_var = tk.StringVar(value="SPY")
        ticker_entry = ttk.Entry(input_frame, textvariable=self.ticker_var, width=10)
        ticker_entry.grid(row=0, column=1, sticky=tk.W, pady=5)

        ttk.Label(input_frame, text="Strategy:").grid(row=0, column=2, sticky=tk.W, pady=5, padx=(20, 0))

        self.strategies = self.get_available_strategies()
        self.strategy_var = tk.StringVar(value=self.strategies[0] if self.strategies else "")
        strategy_combo = ttk.Combobox(input_frame, textvariable=self.strategy_var, values=self.strategies, width=15)
        strategy_combo.grid(row=0, column=3, sticky=tk.W, pady=5)

        run_button = ttk.Button(input_frame, text="Run Backtest", command=self.run_backtest)
        run_button.grid(row=0, column=4, sticky=tk.E, padx=(20, 0), pady=5)

        self.results_frame = ttk.LabelFrame(main_frame, text="Results", padding="10")
        self.results_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.metrics_frame = ttk.Frame(self.results_frame)
        self.metrics_frame.pack(fill=tk.X, pady=5)

        self.plot_frame = ttk.Frame(self.results_frame)
        self.plot_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM, pady=2)

    def get_available_strategies(self):
        strategies_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "strategies")
        strategies = []
        for file in os.listdir(strategies_dir):
            if file.endswith(".py") and file != "__init__.py":
                strategies.append(os.path.splitext(file)[0])
        return sorted(strategies)

    def clear_frame(self, frame):
        for widget in frame.winfo_children():
            widget.destroy()

    def run_backtest(self):
        ticker = self.ticker_var.get().strip().upper()
        strategy = self.strategy_var.get()

        if not ticker:
            messagebox.showerror("Error", "Please enter a ticker symbol")
            return

        if not strategy:
            messagebox.showerror("Error", "Please select a strategy")
            return

        self.status_var.set(f"Running backtest for {ticker} with {strategy}...")
        self.root.update()

        try:
            result = backtest.main(ticker, strategy)
            self.display_results(result, ticker, strategy)
            self.status_var.set(f"Backtest completed for {ticker} with {strategy}")
        except Exception as e:
            messagebox.showerror("Error", f"Error running backtest: {str(e)}")
            self.status_var.set("Error running backtest")

    def export_trades_to_csv(self, trades_df, ticker, strategy):
        if trades_df is None or trades_df.empty:
            messagebox.showinfo("Export", "No trades to export")
            return
        if 'Profit %' not in trades_df.columns:
            trades_df['Profit %'] = (trades_df['Exit Price'] - trades_df['Entry Price']) / trades_df['Entry Price'] * 100
        export_df = trades_df[['Entry Date', 'Exit Date', 'Profit %']]
        filename = f"{ticker}_{strategy}_trades.csv"
        save_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
        export_df.to_csv(save_path, index=False)
        messagebox.showinfo("Export", f"Trades exported to {save_path}")
        return save_path

    def export_monthly_returns_to_csv(self, strategy_df, ticker, strategy):
        monthly_df = calculate_monthly_returns(strategy_df)
        filename = f"{ticker}_{strategy}_monthly_returns.csv"
        save_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
        monthly_df.to_csv(save_path, index=False)
        messagebox.showinfo("Export", f"Monthly returns exported to {save_path}")
        return save_path

    def display_results(self, result, ticker, strategy):
        self.clear_frame(self.metrics_frame)
        self.clear_frame(self.plot_frame)

        if not result or (isinstance(result, tuple) and len(result) >= 2 and result[1] is not None and result[1].empty):
            ttk.Label(self.metrics_frame, text="No trades executed").pack(pady=10)
            return

        metrics, trades_df, strategy_df = result

        metrics_frame = ttk.LabelFrame(self.metrics_frame, text=f"{ticker} - {strategy} Performance")
        metrics_frame.pack(fill=tk.X, pady=5)

        row, col = 0, 0
        for metric, value in metrics.items():
            ttk.Label(metrics_frame, text=f"{metric}:", font=("", 10, "bold")).grid(row=row, column=col*2, sticky=tk.W, padx=5, pady=2)
            ttk.Label(metrics_frame, text=value).grid(row=row, column=col*2+1, sticky=tk.W, padx=5, pady=2)
            col += 1
            if col > 2:
                col = 0
                row += 1

        export_button = ttk.Button(metrics_frame, text="Export Trades to CSV", command=lambda: self.export_trades_to_csv(trades_df, ticker, strategy))
        export_button.grid(row=row+1, column=0, columnspan=2, pady=10, sticky=tk.W)

        export_monthly_button = ttk.Button(metrics_frame, text="Export Monthly Returns to CSV", command=lambda: self.export_monthly_returns_to_csv(strategy_df, ticker, strategy))
        export_monthly_button.grid(row=row+1, column=2, columnspan=2, pady=10, sticky=tk.W)

        fig = plt.figure(figsize=(8, 6))
        ax1 = fig.add_subplot(2, 1, 1)
        ax1.plot(strategy_df["Date"], strategy_df["EquityCurve"], label="Equity Curve", linewidth=2)

        if trades_df is not None and not trades_df.empty:
            if isinstance(trades_df, pd.Series):
                trades_df = pd.DataFrame([trades_df])
            entry_dates = trades_df['Entry Date'].values
            entry_points = []
            exit_dates = trades_df['Exit Date'].values
            exit_points = []

            for date in entry_dates:
                mask = strategy_df['Date'] == date
                if any(mask):
                    idx = mask.idxmax()
                    entry_points.append((date, strategy_df.loc[idx, 'EquityCurve']))

            for date in exit_dates:
                mask = strategy_df['Date'] == date
                if any(mask):
                    idx = mask.idxmax()
                    exit_points.append((date, strategy_df.loc[idx, 'EquityCurve']))

            if entry_points:
                entries_df = pd.DataFrame(entry_points, columns=['Date', 'EquityCurve'])
                ax1.scatter(entries_df['Date'], entries_df['EquityCurve'], marker='^', color='green', s=120, label='Buy')
            if exit_points:
                exits_df = pd.DataFrame(exit_points, columns=['Date', 'EquityCurve'])
                ax1.scatter(exits_df['Date'], exits_df['EquityCurve'], marker='v', color='red', s=120, label='Sell')
        else:
            buys = strategy_df[strategy_df['Signal'] == 1]
            sells = strategy_df[strategy_df['Signal'] == -1]
            if not buys.empty:
                ax1.scatter(buys['Date'], buys['EquityCurve'], marker='^', color='green', s=120, label='Buy')
            if not sells.empty:
                ax1.scatter(sells['Date'], sells['EquityCurve'], marker='v', color='red', s=120, label='Sell')

        ax1.set_title(f"{ticker} - {strategy} Equity Curve")
        ax1.set_ylabel("Equity ($)")
        ax1.grid(True)

        handles = [
            plt.Line2D([0], [0], color='blue', linewidth=2),
            plt.Line2D([0], [0], marker='^', color='w', markerfacecolor='green', markersize=10),
            plt.Line2D([0], [0], marker='v', color='w', markerfacecolor='red', markersize=10)
        ]
        labels = ['Equity Curve', 'Buy', 'Sell']
        ax1.legend(handles, labels)

        ax2 = fig.add_subplot(2, 1, 2)
        strategy_df["Peak"] = strategy_df["EquityCurve"].cummax()
        strategy_df["Drawdown"] = (strategy_df["EquityCurve"] - strategy_df["Peak"]) / strategy_df["Peak"]
        ax2.fill_between(strategy_df["Date"], strategy_df["Drawdown"], 0, color="red", alpha=0.3)
        ax2.set_title("Drawdown")
        ax2.set_xlabel("Date")
        ax2.set_ylabel("Drawdown")
        ax2.grid(True)

        plt.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        toolbar_frame = ttk.Frame(self.plot_frame)
        toolbar_frame.pack(fill=tk.X)
        toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
        toolbar.update()

if __name__ == "__main__":
    root = tk.Tk()
    app = BacktestApp(root)
    root.mainloop()

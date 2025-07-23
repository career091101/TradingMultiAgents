import pandas as pd
import yfinance as yf
from stockstats import wrap
from typing import Annotated
import os
from .config import get_config


class StockstatsUtils:
    @staticmethod
    def get_stock_stats(
        symbol: Annotated[str, "ticker symbol for the company"],
        indicator: Annotated[
            str, "quantitative indicators based off of the stock data for the company"
        ],
        curr_date: Annotated[
            str, "curr date for retrieving stock price data, YYYY-mm-dd"
        ],
        data_dir: Annotated[
            str,
            "directory where the stock data is stored.",
        ],
        online: Annotated[
            bool,
            "whether to use online tools to fetch data or offline tools. If True, will use online tools.",
        ] = False,
    ):
        df = None
        data = None

        if not online:
            try:
                file_path = os.path.join(
                    data_dir,
                    f"{symbol}-YFin-data-2015-01-01-2025-03-25.csv",
                )
                
                # ファイルの存在とサイズをチェック
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"Data file not found: {file_path}")
                
                file_size = os.path.getsize(file_path)
                if file_size == 0:
                    raise Exception(f"Data file is empty: {file_path}")
                
                # CSVファイルを読み込み
                data = pd.read_csv(file_path)
                
                # データが空でないかチェック
                if data.empty:
                    raise Exception(f"No data found in file: {file_path}")
                
                # 必要なカラムが存在するかチェック
                required_columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
                missing_columns = [col for col in required_columns if col not in data.columns]
                if missing_columns:
                    raise Exception(f"Missing required columns: {missing_columns}")
                
                df = wrap(data)
            except FileNotFoundError:
                raise Exception("Stockstats fail: Yahoo Finance data not fetched yet!")
            except pd.errors.EmptyDataError:
                raise Exception(f"No columns to parse from file: {file_path}")
            except Exception as e:
                raise Exception(f"Error reading data file: {str(e)}")
        else:
            # Get today's date as YYYY-mm-dd to add to cache
            today_date = pd.Timestamp.today()
            curr_date = pd.to_datetime(curr_date)

            end_date = today_date
            start_date = today_date - pd.DateOffset(years=15)
            start_date = start_date.strftime("%Y-%m-%d")
            end_date = end_date.strftime("%Y-%m-%d")

            # Get config and ensure cache directory exists
            config = get_config()
            os.makedirs(config["data_cache_dir"], exist_ok=True)

            data_file = os.path.join(
                config["data_cache_dir"],
                f"{symbol}-YFin-data-{start_date}-{end_date}.csv",
            )

            if os.path.exists(data_file):
                try:
                    data = pd.read_csv(data_file)
                    if data.empty:
                        raise Exception(f"Cached data file is empty: {data_file}")
                    data["Date"] = pd.to_datetime(data["Date"])
                except pd.errors.EmptyDataError:
                    # キャッシュファイルが壊れている場合は削除して再取得
                    os.remove(data_file)
                    data = None
                except Exception as e:
                    print(f"Error reading cached file: {e}")
                    data = None
            
            if data is None or data.empty:
                # データをダウンロード
                print(f"Downloading data for {symbol} from {start_date} to {end_date}")
                data = yf.download(
                    symbol,
                    start=start_date,
                    end=end_date,
                    multi_level_index=False,
                    progress=False,
                    auto_adjust=True,
                )
                
                if data.empty:
                    raise Exception(f"No data available for {symbol} from Yahoo Finance")
                
                data = data.reset_index()
                
                # データを保存（エラーが発生しても続行）
                try:
                    data.to_csv(data_file, index=False)
                except Exception as e:
                    print(f"Warning: Failed to save cache file: {e}")

            df = wrap(data)
            df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")
            curr_date = curr_date.strftime("%Y-%m-%d")

        df[indicator]  # trigger stockstats to calculate the indicator
        matching_rows = df[df["Date"].str.startswith(curr_date)]

        if not matching_rows.empty:
            indicator_value = matching_rows[indicator].values[0]
            return indicator_value
        else:
            return "N/A: Not a trading day (weekend or holiday)"

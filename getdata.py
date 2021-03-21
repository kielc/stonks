from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf


# aws s3 keys set as environment variables
tickers = pd.read_csv("s3://stonks-kmc/tickers.csv", index_col=0)

for tic in tickers.index:
    try:
        info = yf.Ticker(tic).info
        for key in [
            "shortName",
            "sector",
            "industry",
            "marketCap",
            "dividendYield",
            "currency",
        ]:
            tickers.at[tic, key] = info[key]
    except:
        # if info dict cannot be retrieved value in df will be nan
        pass

# replace with empty string so that nan isnt displayed on graph or notes section
for column in ["notes", "sector", "industry", "currency"]:
    tickers[column].fillna("", inplace=True)

# use ticker symbol as shortName if nan
tickers["shortName"].fillna(tickers.index.to_series(), inplace=True)

# empty string or nan date value would cause error when converting to datetime
# use date greater than today so that it doesnt show up on the graph
tickers["purchase dates"].fillna("2100-01-01", inplace=True)
tickers["purchase dates"] = tickers["purchase dates"].apply(
    lambda dates: [datetime.strptime(date, "%Y-%m-%d") for date in dates.split()]
)

tickers.sort_values(["sector", "industry", "tic"], inplace=True)

tickers.to_pickle("s3://stonks-kmc/tickers_data.pickle")

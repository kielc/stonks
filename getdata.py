import os
from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf


S3_BUCKET = os.environ["S3_BUCKET"]

# aws s3 keys set as environment variables
tickers = pd.read_csv(S3_BUCKET + "tickers.csv", index_col=0)

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

# sort before replacing nan values so they are last in the sort order
tickers.sort_values(["sector", "industry", "tic"], inplace=True, na_position="last")

# move stock index tickers to the beginning
tickers = pd.concat(
    [
        tickers.loc[tickers.index.str.startswith("^")],
        tickers.loc[~tickers.index.str.startswith("^")],
    ]
)

# replace with empty string so that nan isn't displayed on graph or for empty notes
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

tickers.to_pickle(S3_BUCKET + "tickers_data.pickle")

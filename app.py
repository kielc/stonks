import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import yfinance as yf
from dash.dependencies import Input, Output
from datetime import datetime, timedelta


tickers = pd.read_csv("tickers.csv", index_col=0)

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
        pass

for column in ["notes", "sector", "industry", "currency"]:
    tickers[column].fillna("", inplace=True)
tickers["shortName"].fillna(tickers.index.to_series(), inplace=True)
tickers["purchase dates"].fillna("2100-01-01", inplace=True)
tickers["purchase dates"] = tickers["purchase dates"].apply(
    lambda dates: [datetime.strptime(date, "%Y-%m-%d") for date in dates.split()]
)
tickers.sort_values(["sector", "industry", "tic"], inplace=True)

periods = ["1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"]

external_stylesheets = [
    {
        "href": "https://fonts.googleapis.com/css2?family=Ranchers&display=swap",
        "rel": "stylesheet",
    },
    {
        "href": "https://fonts.googleapis.com/css2?family=Lato&display=swap",
        "rel": "stylesheet",
    },
]

app = dash.Dash(__name__, title="Stonks!", external_stylesheets=external_stylesheets)

app.layout = html.Div(
    [
        html.Div(
            [
                html.Img(src="/assets/favicon-32x32.png", className="emoji"),
                html.H1("Stonks!", className="title"),
            ],
            className="header",
        ),
        html.Div(
            [
                dcc.Dropdown(
                    id="ticker-select",
                    options=[{"label": tic, "value": tic} for tic in tickers.index],
                    value=tickers.index[0],
                ),
            ],
            className="dropdown",
        ),
        html.Div(
            [
                dcc.RadioItems(
                    id="period-select",
                    options=[{"label": period, "value": period} for period in periods],
                    value="6mo",
                ),
            ],
            className="radio",
        ),
        html.Div(
            [
                dcc.Graph(id="graph"),
            ],
            className="graph",
        ),
        html.Div(
            [
                dcc.Markdown(id="text"),
            ],
            className="text",
        ),
    ]
)


@app.callback(
    Output("graph", "figure"),
    [Input("ticker-select", "value"), Input("period-select", "value")],
)
def update_graph(tic, period):
    df = yf.Ticker(tic).history(period=period)
    purchase_dates = [
        date for date in tickers.loc[tic, "purchase dates"] if date in df.index
    ]
    hist_after_purchase = [
        date for date in df.index if date >= min(tickers.loc[tic, "purchase dates"])
    ]
    figure = {
        "data": [
            dict(
                x=df.index,
                y=df["Close"],
                name="Close",
                mode="lines",
                line=dict(color="#24546c"),
            ),
            dict(
                x=purchase_dates,
                y=df.loc[purchase_dates, "Close"],
                name="Purchase Dates",
                mode="markers",
                marker=dict(color="#fbb53b", size=10),
                hoverinfo="skip",
            ),
            dict(
                x=hist_after_purchase,
                y=df.loc[hist_after_purchase, "Close"],
                mode="lines",
                line=dict(color="#92041a"),
                hoverinfo="skip",
                showlegend=False,
            ),
        ],
        "layout": dict(
            title=(
                f"<b>{tickers.loc[tic, 'shortName']}</b><br>"
                f"<span style='font-size: 10px;'>{tickers.at[tic, 'sector']}"
                f" - {tickers.at[tic, 'industry']}</span>"
            ),
            yaxis=dict(title=f"Closing Price {tickers.at[tic, 'currency']}"),
            showlegend=True,
            legend=dict(orientation="h"),
        ),
    }
    return figure


@app.callback(Output("text", "children"), [Input("ticker-select", "value")])
def update_text(tic):
    current_price = yf.Ticker(tic).history(period="1d", interval="1m").iloc[-1]["Close"]
    current_time = (
        yf.Ticker(tic)
        .history(period="1d", interval="1m")
        .iloc[-1]
        .name.strftime("%b %d %H:%M %Z")
    )

    children = f"""
        **Current Price:** ${current_price} ({current_time})

        **Market Cap:** {tickers.at[tic, "marketCap"] / 1000000000: ,.3f} $B

        **Dividend Yield:** {tickers.at[tic, "dividendYield"]: .2%}

        {tickers.at[tic, "notes"]}
    """
    return children


if __name__ == "__main__":
    app.run_server(debug=False)
import os
from datetime import datetime, timedelta

import dash
import dash_auth
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import yfinance as yf
from dash.dependencies import Input, Output, State

USERNAME_PASSWORD_PAIRS = {os.environ["AUTH_USER"]: os.environ["AUTH_PASS"]}
S3_BUCKET = os.environ["S3_BUCKET"]

tickers = pd.read_pickle(S3_BUCKET + "tickers_data.pickle")

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
auth = dash_auth.BasicAuth(app, USERNAME_PASSWORD_PAIRS)
server = app.server

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
                html.Button(
                    id="prev",
                    children="Prev",
                    className="button",
                ),
            ],
            className="button-div",
        ),
        html.Div(
            [
                html.Button(
                    id="next",
                    children="Next",
                    className="button",
                ),
            ],
            className="button-div",
        ),
        html.Div(
            [
                dcc.RadioItems(
                    id="period-select",
                    options=[{"label": period, "value": period} for period in periods],
                    value="2y",
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
    df = yf.Ticker(tic).history(period=period, actions=False)
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
    current = current_price(tic)

    children = f"""
        **Current Price:** ${current[0]:,.2f} ({current[1]}) ({current[2]:+.2%})

        **Market Cap:** {tickers.at[tic, "marketCap"] / 1000000000:,.3f} $B

        **Dividend Yield:** {tickers.at[tic, "dividendYield"]:.2%}

        {tickers.at[tic, "notes"]}
    """
    return children


@app.callback(
    Output("ticker-select", "value"),
    [Input("prev", "n_clicks"), Input("next", "n_clicks")],
    [State("ticker-select", "value"), State("ticker-select", "options")],
)
def button(prev_clicks, next_clicks, tic, options):
    changed_id = [p["prop_id"] for p in dash.callback_context.triggered][0]

    tickers = [d["value"] for d in options]
    index = tickers.index(tic)

    if prev_clicks is not None or next_clicks is not None:
        if "prev" in changed_id:
            index -= 1
        elif "next" in changed_id:
            if index == len(tickers) - 1:
                index = 0
            else:
                index += 1

    return tickers[index]


def current_price(tic):
    """Get current stock price

    Parameters
    ----------
    tic : str
        stock ticker

    Returns
    -------
    (float, str, float)
        (current price, date/time of current price, fractional change vs last close)

    """
    df_day = yf.Ticker(tic).history(period="5d", actions=False)
    df_min = yf.Ticker(tic).history(period="1d", interval="1m", actions=False)

    price = df_day.iloc[-1]["Close"]
    time = df_min.iloc[-1].name.strftime("%b %d %-I:%M %p %Z")
    change = (price / df_day.iloc[-2]["Close"]) - 1

    return (price, time, change)


if __name__ == "__main__":
    app.run_server(debug=False)

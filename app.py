import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objects as go
import datetime
import psycopg2
from sqlalchemy import create_engine, text

#From file
#df = pd.read_csv("aggr.csv", parse_dates=["Entry time"])

#From database
POSTGRES_ADDRESS = 'projectmedellin.ccwkaz2hd3k8.us-east-2.rds.amazonaws.com' ## INSERT YOUR DB ADDRESS
POSTGRES_PORT = '5432'
POSTGRES_USERNAME = 'postgres' ## CHANGE THIS TO YOUR POSTGRES USERNAME
POSTGRES_PASSWORD = 'oTuyoRw6p4lYKikB7NNp' ## CHANGE THIS TO YOUR POSTGRES PASSWORD 
POSTGRES_DBNAME = 'strategy' ## CHANGE THIS TO YOUR DATABASE NAME
postgres_str = ('postgresql://{username}:{password}@{ipaddress}:{port}/{dbname}'
                .format(username=POSTGRES_USERNAME,
                 password=POSTGRES_PASSWORD,
                 ipaddress=POSTGRES_ADDRESS,
                 port=POSTGRES_PORT,
                 dbname=POSTGRES_DBNAME))
# Create the connection
cnx = create_engine(postgres_str)
df = pd.read_sql("SELECT * from trades", cnx.connect(), parse_dates=('Entry time',))


df["YearMonth"] = df["Entry time"].apply(lambda x: x.strftime("%Y %m"))


def filter_exchange(exchange):
    return df[(df["Exchange"] == exchange)]


def filter_df(exchange, leverage, start_date, end_date):
    return df[
        (df["Exchange"] == exchange)
        & (df["Margin"] == int(leverage))
        & (df["Entry time"] >= start_date)
        & (df["Entry time"] <= end_date)
    ]


def filter_date(start_date, end_date):
    return df[(df["Entry time"] >= start_date) & (df["Entry time"] <= end_date)]


def calc_btc_returns(dff):
    btc_start_value = dff.tail(1)["BTC Price"].values[0]
    btc_end_value = dff.head(1)["BTC Price"].values[0]
    btc_returns = (btc_end_value * 100 / btc_start_value) - 100
    return btc_returns


def calc_strat_returns(dff):
    start_value = dff.tail(1)["Exit balance"].values[0]
    end_value = dff.head(1)["Entry balance"].values[0]
    returns = (end_value * 100 / start_value) - 100
    return returns


app = dash.Dash(
    __name__,
    external_stylesheets=[
        "https://codepen.io/uditagarwal/pen/oNvwKNP.css",
        "https://codepen.io/uditagarwal/pen/YzKbqyV.css",
    ],
)


app.layout = html.Div(
    children=[
        # App banner title
        html.Div(
            children=[
                html.H2(
                    children="Bitcoin Leveraged Trading Backtest Analysis",
                    className="h2-title",
                ),
            ],
            className="study-browser-banner row",
        ),
        # Filters and Summary
        html.Div(
            className="row app-body",
            children=[
                html.Div(
                    className="twelve columns card",
                    children=[
                        html.Div(
                            className="padding row",
                            children=[
                                # Exchange selector
                                html.Div(
                                    className="two columns card",
                                    children=[
                                        html.H6("Select Exchange",),
                                        dcc.RadioItems(
                                            id="exchange-select",
                                            options=[
                                                {"label": label, "value": label}
                                                for label in df["Exchange"].unique()
                                            ],
                                            value="Bitmex",
                                            labelStyle={"display": "inline-block"},
                                        ),
                                    ],
                                ),
                                # Leverage selector
                                html.Div(
                                    className="two columns card",
                                    children=[
                                        html.H6("Select Leverage"),
                                        dcc.RadioItems(
                                            id="leverage-select",
                                            options=[
                                                {
                                                    "label": str(label),
                                                    "value": str(label),
                                                }
                                                for label in df["Margin"].unique()
                                            ],
                                            value="1",
                                            labelStyle={"display": "inline-block"},
                                        ),
                                    ],
                                ),
                                # Date Range selector
                                html.Div(
                                    className="three columns card",
                                    id="date-range-div",
                                    children=[
                                        html.H6("Select a Date Range"),
                                        dcc.DatePickerRange(
                                            id="date-range-select",
                                            display_format="MMM YY",
                                            start_date=df["Entry time"].min(),
                                            end_date=df["Entry time"].max(),
                                        ),
                                    ],
                                ),
                                # Strategy Returns card
                                html.Div(
                                    id="strat-returns-div",
                                    className="two columns indicator pretty_container",
                                    children=[
                                        html.P(
                                            id="strat-returns",
                                            className="indicator_value",
                                            children="Change me",
                                        ),
                                        html.P(
                                            "Strategy Returns",
                                            className="twelve columns indicator_text",
                                        ),
                                    ],
                                ),
                                # Market Returns card
                                html.Div(
                                    id="market-returns-div",
                                    className="two columns indicator pretty_container",
                                    children=[
                                        html.P(
                                            id="market-returns",
                                            className="indicator_value",
                                            children="Change me",
                                        ),
                                        html.P(
                                            "Market Returns",
                                            className="twelve columns indicator_text",
                                        ),
                                    ],
                                ),
                                # Strategy vs Market card
                                html.Div(
                                    id="strat-vs-market-div",
                                    className="two columns indicator pretty_container",
                                    children=[
                                        html.P(
                                            id="strat-vs-market",
                                            className="indicator_value",
                                            children=["Change Me"],
                                        ),
                                        html.P(
                                            "Strategy vs. Market Returns",
                                            className="twelve columns indicator_text",
                                        ),
                                    ],
                                ),
                            ],
                        )
                    ],
                ),
            ],
        ),
        # Graph Overview of Montlhy performance
        html.Div(
            className="twelve columns cards",
            children=[
                dcc.Graph(
                    id="monthly-chart",
                    figure=go.Figure(
                        data=[
                            go.Candlestick(
                                x=df["YearMonth"],
                                open=df["Entry balance"],
                                close=df["Exit balance"],
                                low=df["Entry balance"],
                                high=df["Exit balance"],
                            )
                        ],
                        layout={"title": "Overview of Monthly performance"},
                    ),
                )
            ],
        ),
        # Table and Bar chart
        html.Div(
            className="padding row",
            children=[
                html.Div(
                    className="six columns card",
                    children=[
                        dash_table.DataTable(
                            id="table",
                            columns=[
                                {"name": "Number", "id": "Number"},
                                {"name": "Trade type", "id": "Trade type"},
                                {"name": "Exposure", "id": "Exposure"},
                                {"name": "Entry balance", "id": "Entry balance"},
                                {"name": "Exit balance", "id": "Exit balance"},
                                {"name": "Pnl (incl fees)", "id": "Pnl (incl fees)"},
                            ],
                            style_cell={"width": "50 px"},
                            style_table={"maxHeight": "450px", "overflowY": "scroll"},
                            data=df.to_dict("records"),
                        )
                    ],
                ),
                # Pnl vs Trade type
                dcc.Graph(id="pnl-types", className="six columns card", figure={}),
            ],
        ),
        html.Div(
            className="padding row",
            children=[
                # Daily BTC Price
                dcc.Graph(id="daily-btc", className="six columns card", figure={}),
                # Balance overtime
                dcc.Graph(id="balance", className="six columns card", figure={}),
            ],
        ),
    ]
)

# Date range selector update
@app.callback(
    dash.dependencies.Output("date-range-div", "children"),
    [dash.dependencies.Input("exchange-select", "value")],
)
def update_date_range(exchange):
    dfd = filter_exchange(exchange)
    date_picker = dcc.DatePickerRange(
        id="date-range-select",
        display_format="MMM YY",
        start_date=dfd["Entry time"].min(),
        end_date=dfd["Entry time"].max(),
    )
    return date_picker


def calc_returns_over_month(dff):
    out = []
    for name, group in dff.groupby("YearMonth"):
        exit_balance = group.head(1)["Exit balance"].values[0]
        entry_balance = group.tail(1)["Entry balance"].values[0]
        monthly_return = (exit_balance * 100 / entry_balance) - 100
        out.append(
            {
                "month": name,
                "entry": entry_balance,
                "exit": exit_balance,
                "monthly_return": monthly_return,
            }
        )
    return out


@app.callback(
    [
        dash.dependencies.Output("monthly-chart", "figure"),
        dash.dependencies.Output("market-returns", "children"),
        dash.dependencies.Output("strat-returns", "children"),
        dash.dependencies.Output("strat-vs-market", "children"),
        dash.dependencies.Output("pnl-types", "figure"),
    ],
    (
        dash.dependencies.Input("exchange-select", "value"),
        dash.dependencies.Input("leverage-select", "value"),
        dash.dependencies.Input("date-range-select", "start_date"),
        dash.dependencies.Input("date-range-select", "end_date"),
    ),
)
def update_monthly(exchange, leverage, start_date, end_date):
    dff = filter_df(exchange, leverage, start_date, end_date)
    data = calc_returns_over_month(dff)
    btc_returns = calc_btc_returns(dff)
    strat_returns = calc_strat_returns(dff)
    strat_vs_market = strat_returns - btc_returns
    trace1 = go.Bar(x=dff["Entry time"], y=dff["Profit"], name="Profit")
    trace2 = go.Bar(x=dff["Entry time"], y=dff["Trade type"], name="Trade type")
    return (
        {
            "data": [
                go.Candlestick(
                    open=[each["entry"] for each in data],
                    close=[each["exit"] for each in data],
                    x=[each["month"] for each in data],
                    low=[each["entry"] for each in data],
                    high=[each["exit"] for each in data],
                )
            ],
            "layout": {"title": "Overview of Monthly performance"},
        },
        f"{btc_returns:0.2f}%",
        f"{strat_returns:0.2f}%",
        f"{strat_vs_market:0.2f}%",
        {"data": [trace1, trace2], "layout": go.Layout(title="PnL vs Trade type")},
    )


# update table
@app.callback(
    dash.dependencies.Output("table", "data"),
    (
        dash.dependencies.Input("exchange-select", "value"),
        dash.dependencies.Input("leverage-select", "value"),
        dash.dependencies.Input("date-range-select", "start_date"),
        dash.dependencies.Input("date-range-select", "end_date"),
    ),
)
def update_table(exchange, leverage, start_date, end_date):
    dff = filter_df(exchange, leverage, start_date, end_date)
    return dff.to_dict("records")


# BTC line chart / portfolio balalnce
@app.callback(
    [
        dash.dependencies.Output("daily-btc", "figure"),
        dash.dependencies.Output("balance", "figure"),
    ],
    (
        dash.dependencies.Input("date-range-select", "start_date"),
        dash.dependencies.Input("date-range-select", "end_date"),
    ),
)
def update_daily_btc_portfolio_balance(start_date, end_date):
    dfd = filter_date(start_date, end_date)
    trace_btc = go.Scatter(x=dfd["Entry time"], y=dfd["BTC Price"])
    trace_portfolio = go.Scatter(x=dfd["Entry time"], y=dfd["Profit"])
    return (
        {"data": [trace_btc], "layout": go.Layout(title="Daily BTC Price")},
        {
            "data": [trace_portfolio],
            "layout": go.Layout(title="Balance overtime"),
        },
    )


if __name__ == "__main__":
    app.run_server(debug=True)

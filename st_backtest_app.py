"""Streamlit dashboard for moving average backtesting."""

from __future__ import annotations

import datetime as dt

import altair as alt
import pandas as pd
import streamlit as st

from stotify.backtest import backtest_ma_cross


def _trade_table(trades):
    if not trades:
        return pd.DataFrame()
    return pd.DataFrame(
        [
            {
                "Entry Date": trade.entry_date.date(),
                "Entry Price": trade.entry_price,
                "Exit Date": trade.exit_date.date(),
                "Exit Price": trade.exit_price,
                "Return %": trade.return_pct,
                "Hold Days": trade.hold_days,
            }
            for trade in trades
        ]
    )


st.set_page_config(page_title="ST Backtest App", layout="wide")
st.title("ST Backtest App")
st.write(
    "Explore how a simple moving average crossover strategy performed in the past."
)

with st.sidebar:
    st.header("Strategy Inputs")
    ticker = st.text_input("Ticker", value="AAPL")
    start_date = st.date_input("Start date", value=dt.date(2021, 1, 1))
    end_date = st.date_input("End date", value=dt.date.today())
    fast_window = st.number_input("Fast MA window", min_value=2, value=50)
    slow_window = st.number_input("Slow MA window", min_value=3, value=200)
    exit_mode = st.radio("Exit rule", ["fixed", "cross"], index=0)
    hold_days = st.number_input(
        "Hold days (fixed exit only)", min_value=1, value=30
    )
    run_backtest = st.button("Run backtest")

if run_backtest:
    with st.spinner("Running backtest..."):
        result = backtest_ma_cross(
            ticker.strip().upper(),
            start=str(start_date),
            end=str(end_date),
            fast_window=int(fast_window),
            slow_window=int(slow_window),
            exit_mode=exit_mode,
            hold_days=int(hold_days),
        )

    if result.history.empty:
        st.warning("No historical data found for that input.")
    else:
        history = result.history.copy()
        price_label = "Price"
        fast_label = f"{fast_window}-day MA"
        slow_label = f"{slow_window}-day MA"

        chart_data = history[["Close", "fast_ma", "slow_ma"]].rename(
            columns={
                "Close": price_label,
                "fast_ma": fast_label,
                "slow_ma": slow_label,
            }
        )
        chart_data = chart_data.reset_index(names="Date")
        melted = chart_data.melt(
            id_vars="Date",
            var_name="Series",
            value_name="Value",
        )

        st.subheader("Price with Moving Averages")
        line_chart = (
            alt.Chart(melted)
            .mark_line(strokeWidth=2)
            .encode(
                x=alt.X("Date:T", title="Date"),
                y=alt.Y("Value:Q", title="Price"),
                color=alt.Color("Series:N", legend=alt.Legend(orient="bottom")),
            )
        )

        entries = [
            {"Date": trade.entry_date, "Price": trade.entry_price, "Type": "Entry"}
            for trade in result.trades
        ]
        exits = [
            {"Date": trade.exit_date, "Price": trade.exit_price, "Type": "Exit"}
            for trade in result.trades
        ]
        markers = pd.DataFrame(entries + exits)

        if not markers.empty:
            marker_chart = (
                alt.Chart(markers)
                .mark_point(filled=True, size=80)
                .encode(
                    x=alt.X("Date:T", title="Date"),
                    y=alt.Y("Price:Q", title="Price"),
                    color=alt.Color(
                        "Type:N",
                        scale=alt.Scale(domain=["Entry", "Exit"], range=["#2ca02c", "#d62728"]),
                        legend=alt.Legend(orient="bottom"),
                    ),
                    tooltip=["Type", "Date", "Price"],
                )
            )
            st.altair_chart(line_chart + marker_chart, use_container_width=True)
        else:
            st.altair_chart(line_chart, use_container_width=True)

        st.subheader("Backtest Summary")
        metrics = result.metrics
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Trades", int(metrics.get("total_trades", 0)))
        col2.metric("Win rate", f"{metrics.get('win_rate', 0):.1f}%")
        col3.metric("Avg return", f"{metrics.get('avg_return', 0):.2f}%")
        col4.metric("Total return", f"{metrics.get('total_return', 0):.2f}%")

        st.subheader("Trades")
        st.dataframe(_trade_table(result.trades), use_container_width=True)
else:
    st.info("Set your inputs in the sidebar and click 'Run backtest'.")

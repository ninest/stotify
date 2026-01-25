.PHONY: test format check streamlit ui

test:
	uv run pytest

format:
	uv run ruff format stotify tests
	uv run ruff check --fix stotify tests

check:
	uv run ruff format --check stotify tests
	uv run ruff check stotify tests

streamlit:
	uv run streamlit run st_backtest_app.py

ui: streamlit

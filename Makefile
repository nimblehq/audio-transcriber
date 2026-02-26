.PHONY: setup run clean

setup:
	python3.12 -m venv .venv
	. .venv/bin/activate && pip install -r requirements.txt
	@echo ""
	@echo "Setup complete. Now configure your API key:"
	@echo "  cp .env.example .env"
	@echo "  Then edit .env and add your HuggingFace token"

run:
	. .venv/bin/activate && python run.py

clean:
	rm -rf .venv data/meetings/*

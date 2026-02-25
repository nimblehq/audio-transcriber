.PHONY: setup run clean

setup:
	python3.12 -m venv .venv
	. .venv/bin/activate && pip install -r requirements.txt
	@echo ""
	@echo "Setup complete. Now configure your API keys:"
	@echo "  export HF_TOKEN='your_huggingface_token'"
	@echo "  export ANTHROPIC_API_KEY='your_anthropic_key'"

run:
	. .venv/bin/activate && python run.py

clean:
	rm -rf .venv data/meetings/*

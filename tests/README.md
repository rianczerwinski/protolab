# Protolab tests

Run `python -m pytest` from the repository root. `conftest.py` supplies temporary protocol projects for storage, CLI, import, and resynthesis checks. The HTTP and webhook modules require optional FastAPI support and report skips when it is absent; a CLI-only pass does not establish HTTP readiness. Pytest's cache belongs in `dev/runtime/pytest-cache/`.

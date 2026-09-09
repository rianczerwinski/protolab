# Protolab package

`cli.py` exposes the commands; `api.py` supplies the Python interface. Command modules implement correction capture, imports, checks, analysis, resynthesis, and status. `config.py`, `types.py`, and `store.py` own configuration and persisted data. [adapters/](adapters/README.md) translates external evaluation formats. `llm.py` isolates optional model execution; `serve.py` contains the HTTP/dashboard implementation.

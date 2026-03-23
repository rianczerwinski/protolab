# Protolab Roadmap

## v0.1.x — Current

Multi-file protocol support via flat assembly: glob patterns, ordered
concatenation, section markers. Single-file configs remain unchanged.

Config:
```toml
[protocol]
paths = ["instructions/*.md", "system-prompt.md"]
```

## Future

### Protocol manifest / module graph

A top-level manifest declares protocol modules, their roles (core /
extension / override), and relationships between them. Corrections and
rules carry module attribution. Resynthesis can propagate changes across
linked modules.

Motivation: as protocols grow, isolation between subjects breaks down.
A rule in `auth.md` may govern behavior described in `session.md`. The
graph model makes those relationships explicit and queryable.

Design entry point: `PROTOCOL.toml` at repo root with `[[modules]]`
entries declaring roles and inter-module links.

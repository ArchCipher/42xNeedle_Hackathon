Improvisations

Steps:
	Summarise/retrieve: FTS5 and or sqlite-lembed
	Feed to LLM and get code
	Static checks: run compilers, tree-sitter, linters
	if static checks pass
		Unit tests 
	else
		send test results to LLM (same session)
		with short prompt"given this code and this compielr error, return a corrected version and 1-2 sentence explanation"

Notes: sandbox execution and test harness (containers/time limits)

Language:
	Node.js is a JavaScript runtime for servers. Fast async I/O, large npm ecosystem, and easy JSON/HTTP handling
	Python is good for embeddings/ML tooling

	OpenClaw uses Node.js, Hermes uses Python

Tools:
	search, DB query, or API call
	OpenClaw has built in tools via skills/puggins. Hermes has 40+ built-in toools

Summarization & session history:
	Simple token/keyword search (FTS5?) + LLM summarization

Note:	FTS5 is SQLite's full-text search extension.
		External engines: Elasticsearch, Opensearch, Apache Lucene/Tantivy, Meilisearch
		Semantic search is meaning based. Something like sqlite-vec/sqlite-lembed for hybrid search
	
		Compilers like Clang use symbol/name similarity heuristics. When name lookup fails, it uses static analysis and deterministic heuristics - AST, symbol tables, scope rules, language specifi rules, fuzzy string metrics(Levenshtein /edit distance), overlaod candidates and diagnostic-specific heuristics to propose corrections.

OpenClaw Architecture
	ReAct loop(reason, act, observe)
	Memory stored in md files()
	Process that owns session, routing, tool execution and state

Self learning loop of Hermes Agent
	Experience a complex multi step task
	Extraction of reusable patterns
	Skill creation
	Refinement of skills over use
	Nudge:periodic review & update knowledge

Memory systems
	OpenClaw stores it in plain md file (SOUL.md - agent persona, MEMORY.md - persistent notes, USER.md - user profiles)
	Hermes uses layered memory stack. Persistent notes(agent curated survives across sessions), session history(FTS + LLM summarization), User modelling, Procedural memory(skills as reusable procedures- remembers methods, not just facts), separation of prompt memory and archival storage for token efficiency

Security
	OpenClaw ships iwth weak default security but a deep, privileged access to the system - risky combo!
	Hermes is safer by default
		built-in prompt injection scanning
		user auth and approval checks
		credential filtering
		context scanning for sensitive data
		container hardening with read-only root and dropped capabilities
		isolation via Docker, SSH, or serverless backends
	Neither is enterprise-grade zero-trust sandboxing. Check IronClaw or NanoClaw

TODO
	How libclang or tree-sitter works and if can be integrated into code

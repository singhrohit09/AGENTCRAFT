# AgentCraft — System Limitations & Future Roadmap

This document outlines the current boundaries, trade-offs, security assumptions, and future enhancements of **AgentCraft**.

---

## 1. Current System Limitations

### 1.1 Sandboxed Execution Scope
- `CodeRunnerTool` operates inside a managed local execution scope with safe built-ins and redirected standard I/O. While this prevents accidental file leaks and standard crashes, it does not use a hardware virtualization boundary (e.g., gVisor, Firecracker VM, or Docker).
- High-risk operations (such as compiling C extensions, kernel-level networking, or arbitrary bash sub-processes) are deliberately blocked.

### 1.2 Network Access Boundaries
- `WebFetcherTool` provides both real HTTP queries and a local simulated knowledge retrieval provider.
- By default, external HTTP calls have a 10-second timeout and do not handle complex browser rendering (JavaScript execution via headless Chromium is deferred to future releases).

### 1.3 LLM Provider Rate Limits
- When operating in `hybrid` or `openai` mode, throughput is subject to provider rate limits (tokens per minute, requests per minute).
- To mitigate this, AgentCraft includes deterministic fallback planning that guarantees full operational capability even during provider outages or rate-limit saturation.

### 1.4 State Persistence Strategy
- Current sessions are stored in memory (`AgentService.sessions`) with file-backed sandbox storage. If the backend process restarts, active in-memory sessions reset.
- Persistent database storage (PostgreSQL / SQLite) is planned for production deployments.

---

## 2. Failure Handling & Edge Case Behavior

| Failure Mode | AgentCraft Mitigation |
| :--- | :--- |
| **Directory Traversal Attack** | Enforces path normalization within `FileManagerTool`; rejects any `../` paths with an `Access denied` error and triggers path normalization recovery. |
| **Infinite Recursion in Code** | Scripts run under compile guards and execution timeouts to prevent hanging processes. |
| **Flaky External APIs** | HTTP client automatically follows redirects and handles JSON decode fallbacks cleanly without crashing the agent pipeline. |
| **Ambiguous Goals** | When a goal does not map cleanly to standard domains, the cognitive synthesizer constructs a generalized research-and-validate plan rather than aborting. |

---

## 3. AgentCraft 2.0 Roadmap

1. **Hardware-Isolated MicroVM Sandboxes**: Integrate Firecracker or containerized sandboxes for untrusted arbitrary code execution.
2. **Persistent Relational State Store**: Store session traces and benchmark histories in SQLite/PostgreSQL with vector embeddings for semantic session retrieval.
3. **Multi-Agent Collaboration**: Enable multi-agent debates and peer review where one agent plans, another executes, and a third acts as an adversarial auditor.
4. **Interactive Human-in-the-Loop Approval**: Allow operators to pause execution on high-impact steps (e.g. destructive file deletes or external payments) to await human confirmation.

# Hazel Village NPC Game Service Design

## Goal

Upgrade the current Streamlit GraphRAG MVP into a small-service-ready NPC game with isolated, durable conversations for each NPC, guest-first play, later account conversion, and a game-like "village correspondence journal" interface.

## Approved Deployment

The repository exposes two independent deployment folders so each physical server can run `git pull` and execute the Compose file in its own folder:

- `model-server/`: reverse proxy, Streamlit, FastAPI, and approval-gated vLLM.
- `database-server/`: PostgreSQL with pgvector and Neo4j.
- `k8s/`: optional two-node Kubernetes manifests using the same workload split.

### GPU server

- Public reverse proxy on HTTPS 443.
- Streamlit frontend.
- FastAPI backend.
- vLLM inference service.
- Stateless application containers and only the model files/cache required by vLLM.

### Storage server

- PostgreSQL for mutable player and service state.
- Neo4j for canonical story knowledge and GraphRAG traversal.
- Database volumes and backups.
- No public database ports.

The servers communicate over a private network. PostgreSQL, Neo4j, and vLLM are never exposed directly to the public Internet. No shared filesystem is assumed.

## Service Boundaries

FastAPI is the only production state and database boundary. Streamlit renders the UI and keeps only transient view state. It calls FastAPI for session bootstrap, conversation loading, chat turns, quest progress, saves, account conversion, and admin mutations.

PostgreSQL owns:

- Guest and account identities.
- Browser sessions and opaque token hashes.
- Save slots.
- Per-NPC conversations and ordered messages.
- Idempotent turn attempts and failure state.
- Quest progress and observed clues.
- NPC memory summaries.
- Administrative audit events.
- The complete long-form knowledge corpus and vector embeddings through pgvector.

Neo4j owns:

- NPC, Quest, Clue, Truth, Location, Event, and KnowledgeChunk nodes.
- Hierarchical and relational story knowledge.
- GraphRAG retrieval relationships and constraints.
- Admin-authored story graph additions such as ConceptStory.
- The immediately required NPC, quest, clue, truth, and global-story relationship graph used for deterministic GraphRAG traversal.

FastAPI combines graph-scoped Neo4j results with full-corpus pgvector candidates before prompt construction. PostgreSQL remains the source of full document text; Neo4j remains the source of graph relationships and reveal policy.

`rsc/data` remains the canonical story source. Player state must never be written into source files, generated pipeline output, or the canonical story import path.

## Persistent Data Model

The minimum PostgreSQL schema consists of:

- `players`: guest/account player root.
- `accounts`: verified login identity linked to a player.
- `browser_sessions`: hashed opaque session token, expiry, rotation, and revocation.
- `saves`: player-owned save slots and current selection metadata.
- `conversations`: one durable thread per save and NPC.
- `messages`: append-only ordered player and NPC messages.
- `turn_attempts`: idempotency key, pending/succeeded/failed state, and bounded failure metadata.
- `quest_progress`: current state and hint level per save and quest.
- `observed_clues`: unique clue observations per save and quest.
- `npc_memory_summaries`: compacted prompt memory per save and NPC.
- `admin_audit_events`: authenticated administrative changes.

Query-critical fields remain relational. JSONB is limited to bounded snapshots and metadata that do not require relational queries.

## Guest And Account Lifecycle

On first visit, FastAPI creates a guest player, default save, and browser session. It issues an opaque random cookie using `HttpOnly`, `Secure`, `SameSite=Lax`, and `Path=/`; PostgreSQL stores only its hash.

Account conversion runs in one PostgreSQL transaction and rotates the session token. Guest progress is preserved. If an existing account already owns a save, the guest save becomes a separate slot rather than silently overwriting progress. Verified OIDC identity is preferred. Local passwords, if later enabled, use Argon2id.

## Chat Turn Consistency

1. FastAPI validates the browser session and idempotency key.
2. A short PostgreSQL transaction stores or reuses the user message and creates an `llm_pending` turn attempt.
3. The transaction closes before external work.
4. FastAPI evaluates quest progress and reads Neo4j using the existing NPC, role, quest, hint-level, and answer-sensitive gates.
5. FastAPI builds the existing constrained NPC prompt and calls private vLLM.
6. A second short PostgreSQL transaction stores the complete assistant response, quest progress, observed clues, and memory update.
7. On Neo4j or vLLM failure, the turn is marked failed without creating an assistant message or NPC memory. The same idempotency key can safely retry.

Partial model output is not committed as a successful NPC message. PostgreSQL transactions are never held open while waiting for vLLM.

## Game UI

The visual direction is a "village correspondence journal."

### Desktop

- Left: vertical NPC roster with name, role, quest state, unread state, and route recommendation marker.
- Center: active NPC header, location/relationship context, isolated durable transcript, composed empty/error/loading states, and chat input.
- Right: quest journal with current objective, observed clues, and the currently allowed hint tier.

Selecting an NPC loads only that NPC's conversation. Quest routing can activate the target NPC and quest without losing any transcript or progress.

### Mobile and tablet

- The NPC roster becomes a compact top switcher.
- The quest journal becomes a collapsible panel.
- The active conversation and input remain the primary surface.

Technical IDs, model addresses, prompts, retrieved chunks, and runtime diagnostics are absent from the player surface. Existing diagnostics remain available only to authenticated administrators.

## Visual System

Before product UI code changes, create `src/streamlit/DESIGN.md` containing tokens, typography, spacing, surface materials, responsive rules, reusable primitives, interaction states, motion constraints, accessibility constraints, and accepted debt. All custom CSS values and repeated UI patterns must trace to this contract.

The interface must use local assets and system/local fonts only. Motion communicates selection, loading, or state change and respects reduced-motion preferences.

## Security And Operations

- Only HTTPS 443 is public.
- Database and model ports are private.
- FastAPI authorizes every player-owned resource by the current session principal.
- Unsafe methods use same-origin checks and CSRF protection where browser cookies are accepted directly.
- Model and player text render as text, never unrestricted HTML.
- Admin routes require explicit authentication and authorization.
- Database migrations use Alembic and are applied as a deploy step, not application startup side effects.
- PostgreSQL and Neo4j backups are separate and have tested restore procedures.
- Neo4j reset, database wipe, and volume deletion remain prohibited without explicit approval.

## Verification Scenarios

1. An anonymous first visit creates a guest save and restores it after reconnect.
2. A message sent to one NPC appears only in that NPC conversation after switching away, returning, and reconnecting.
3. A new NPC conversation shows a composed empty state and no messages from another NPC.
4. Quest-directed routing activates the target NPC while preserving all conversations and quest progress.
5. Repeating the same client message ID does not duplicate the user message, assistant response, clues, or quest progress.
6. A vLLM or Neo4j failure preserves the user message as retryable and does not create assistant memory.
7. Guest-to-account conversion preserves progress and never overwrites an existing account save silently.
8. Answer-sensitive knowledge remains unavailable until the existing reveal conditions pass.
9. Admin functionality remains separate and authorization-gated.
10. Browser QA covers every player state at 375, 768, and 1280 pixels, including Korean wrapping, keyboard focus, loading, error, active, route, and reduced-motion states.

## Non-Goals

- Replacing Neo4j with PostgreSQL.
- Publicly exposing databases or vLLM.
- Adding Redis, Kafka, or a shared filesystem for the initial small service.
- Changing canonical story content or weakening retrieval/reveal rules.
- Automatically resetting or rebuilding production databases.

## Kubernetes Topology

The two-node Kubernetes option is a pinned, recoverable topology rather than high availability. Nodes are labeled `hazel-role=model` and `hazel-role=database`. Stateless API/UI workloads and the GPU-limited vLLM Deployment run on the model node. PostgreSQL+pgvector and Neo4j run as StatefulSets with local persistent volumes on the database node. NetworkPolicy permits database ingress only from the API workload. vLLM remains scaled to zero until the user explicitly approves a GPU test or production start.

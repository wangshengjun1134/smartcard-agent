---
name: RuntimeContext minimal design
description: RuntimeContext only manages hardware connection, not business state
type: project
---

RuntimeContext manages only:
- `pcsc_client` (PcscClient)
- `connected` (bool)
- `current_reader` (Optional[str])
- `atr` (Optional[bytes])

**Why:** Previously RuntimeContext tracked file paths, PIN status, secure channel state, execution history, card capabilities, discovered apps, etc. This bloated the context and mixed hardware management with business state. These are all managed by individual Skills through APDU commands — they don't need to be tracked in context.

**How to apply:** 
- Skills send APDU via `context.send_apdu()` — they manage their own state
- AgentState (LangGraph) handles serializable task state
- Do NOT add business state fields to RuntimeContext

# multiagent-coordinator

Use at the start of complex tasks that can be parallelized safely.

## Parallelization protocol
1. Split work into independent streams.
2. Define input/output contract for each stream.
3. Start all independent streams together.
4. Merge at explicit synchronization points.

## Dependency management
- Mark blocking tasks first (contracts, schemas, core config).
- Run UI/content/assets in parallel with backend where possible.
- Fail fast on contract mismatch.

## Communication template
- Agent X produces: files + output schema + status.
- Agent Y consumes only validated outputs.
- Shared status updates in one canonical place.

## Safety checks
- No two agents writing same file simultaneously.
- No hidden mutable shared state.
- Error context must include step + channel + module.


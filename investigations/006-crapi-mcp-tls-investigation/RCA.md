# Root-cause analysis — MCP TLS startup failure

## Assessment

The reported MCP authentication request failed certificate verification against the identity service. This is the reported immediate failure mechanism in the retained evidence (O2–O4), not an independently verified underlying cause. A subsequent process snapshot showed no MCP server while Uvicorn remained active (O5). Termination following the startup exception is a plausible hypothesis, but no MCP exit status or complete timestamped lifecycle trace was retained.

This is not a completed RCA for the separate chatbot uninitialised state. No causal connection between that state and MCP failure has been established.

## Observed impact

- No MCP process was reported in the process snapshot; functionality provided by that process was likely unavailable, but no functional request was captured. The full duration and specific user-facing MCP operations affected were not measured.
- The chatbot HTTP server remained running. A state request returned HTTP 200 while its body reported that model initialisation was required.
- Container running status alone did not demonstrate availability of every component.

No production impact, data loss, security compromise or complete chatbot outage was established.

## Failure mechanism and contributing conditions

1. The entrypoint starts `python -m mcpserver.server &`, allowing the script to continue to Uvicorn (O6).
2. MCP attempts an outbound identity-service request during authentication/API-key retrieval. The reported traceback identifies certificate verification failure (O2).
3. The deployed HTTPX client reportedly omits the local source's `verify=False` setting (O4). Default verification is expected, although the complete effective trust configuration was not retained.
4. A separate TLS test reportedly reproduced the trust failure (O3), supporting a TLS trust problem rather than a chatbot HTTP response issue.
5. MCP is absent in the later process snapshot while Uvicorn continues running (O5). Background execution permits this partial failure; it does not itself prove the exception caused process exit.
6. Docker's restart policy is `no` (O7). A container restart policy governs container exit, not recovery of an individual failed background child while the container remains running.

## What remains uncertain

| Question | Current evidence | Needed to resolve |
| --- | --- | --- |
| Why does certificate verification fail? | Retained summary describes an untrusted self-signed identity certificate; raw chain not retained | Inspect served chain, trust store, hostname, validity and effective client settings |
| Why do local and deployed sources differ? | Reported HTTPX configuration discrepancy | Record image digest, source revision and build provenance; compare files |
| Did the TLS exception terminate MCP? | Startup exception plus later absence | Capture exit status and correlated startup/process logs |
| Does MCP failure cause model uninitialised state? | Both symptoms observed; causality unproven | Trace initialisation prerequisites and run controlled tests |
| Can existing health checks detect MCP failure? | No verified health-check configuration | Inspect deployment/image checks and test their behaviour |
| Does another mechanism recover MCP later? | One process snapshot | Inspect supervision and observe over time |

Possible missing CA trust, chain delivery problems or other certificate validation conditions require inspection; do not promote any one of these to a proven underlying cause. Source drift is a finding, not proof that the wrong image was deployed.

## Recommended remediation — not implemented

- Verify the actual certificate and endpoint, then configure a trusted CA chain and a certificate valid for that endpoint. Keep certificate verification enabled. The local `verify=False` setting is not a secure fix.
- Make deployed artifacts traceable to source revisions and image digests; rebuild deliberately after establishing the intended version.
- Give required MCP functionality an explicit lifecycle: for example, a separately managed service or supervision that observes child failure. Define retry/backoff and dependency behaviour deliberately.
- Add capability-aware readiness checks based on actual feature dependencies. Keep liveness distinct so temporary dependency problems do not automatically trigger unnecessary restarts.
- Investigate model configuration and initialisation as a separate workstream until evidence links it to MCP.

## Acceptance criteria

A fix is verified only after the same container environment validates the identity endpoint without bypassing TLS, MCP authenticates and remains available, and a required MCP operation succeeds. A controlled MCP failure should produce the intended readiness/recovery behaviour. Repeat the chatbot state and initialisation tests independently and record their results. None of these recovery criteria was verified in the available record.

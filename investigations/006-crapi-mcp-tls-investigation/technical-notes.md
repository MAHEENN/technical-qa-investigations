# Technical notes — crAPI MCP TLS investigation

## HTTP success and application state

HTTP 200 means the request received a successful HTTP response. The body can still report that the model needs initialisation. Inspect status, body and the intended user operation. This observation alone does not identify an initialisation defect or its cause.

## TLS trust

TLS certificate verification checks the peer's identity using certificates and configured trust. A self-signed certificate is not automatically trusted. A verification failure calls for inspecting the actual certificate chain, endpoint hostname, validity and client trust configuration. Do not infer all of these from one error message.

`verify=False` bypasses certificate verification. A local source setting that bypasses verification can explain different behaviour from a deployed client that verifies certificates, but it is not a secure remediation. Prefer a valid certificate chain and appropriate CA trust.

## Tracebacks

A traceback shows the call path to an exception. Here, the retained analysis traced the TLS exception to MCP authentication/API-key retrieval. That narrows the failing operation; it does not prove every downstream symptom shares the same cause. Keep the original traceback and timestamps when possible, with secrets removed.

## Processes and containers

A container can host multiple processes. `ps -ef` is a snapshot of processes visible in that namespace. The observed Uvicorn process and missing MCP process explain why HTTP service availability and MCP availability must be assessed separately.

The shell operator `&` runs a command in the background and allows the script to continue. It does not provide automatic recovery. Docker container restart policy is different from child-process supervision. Even a container restart policy such as `always` would not directly recover MCP while the container stays running.

## Local source versus deployed code

The working tree is not proof of what an existing container runs. Record source revision, image identity and build provenance, and inspect the deployed file. A discrepancy does not by itself prove a stale image, wrong branch or build-cache problem.

## Liveness, readiness and dependency checks

- Liveness asks whether the service is alive and responsive.
- Readiness asks whether it can handle the intended work.
- Dependency checks examine required supporting capabilities.

A process check is weaker than a functional operation. Define required dependencies for each feature before deciding readiness. These are design concepts; no specific crAPI health endpoint was verified in this investigation.

## Evidence discipline

Separate observations from explanations. “TLS exception reported; MCP later absent” supports a termination hypothesis, but an exit status would strengthen the claim. “Model uninitialised and MCP absent” is coexistence, not proof of causality.

This documentation uses secondary retained evidence where original screenshots/logs were unavailable. Preserve that limitation and replace summaries with redacted primary evidence when captured. Do not invent exact commands, timestamps or error excerpts.

## Review before publication

Check technical claims, links and evidence provenance, then inspect the diff for secrets. Publication should preserve the open status and evidence limitations. A completed RCA requires primary evidence and verified recovery results.

## Technical references

- [Docker inspect syntax and templates](https://docs.docker.com/reference/cli/docker/inspect/)
- [Docker container restart policies](https://docs.docker.com/engine/containers/start-containers-automatically/)
- [HTTPX certificate verification and trust configuration](https://www.python-httpx.org/advanced/ssl/)

# Evidence register — sanitised observations

## Provenance

Scope: independent investigation of a local OWASP crAPI Docker deployment, documented on 17 November 2026. Sources are retained investigation summaries and excerpts; no fresh application run was performed for this review.

Original screenshots are not included in the repository. Some results survive only as secondary interpretations of those screenshots. This is a secondary evidence register, not a substitute for raw logs. Exact traceback lines, original TLS-test command, endpoint URL, image digest and source revision are not available here. No missing output has been reconstructed as a verbatim transcript.

## O1 — State endpoint

The retained summary reports HTTP 200 with this body:

```json
{
  "initialized": "false",
  "message": "Model needs to be initialized"
}
```

`"false"` is represented as a string in the preserved excerpt. This records application state despite a successful HTTP response; it does not establish why initialisation was incomplete. Exact request URL/method and timestamp were not retained.

## O2 — MCP authentication TLS exception

The retained traceback analysis places a TLS certificate verification failure in the MCP server's outbound identity-service request during API-key retrieval. A complete raw traceback and exact exception wording are unavailable in the retained record. The retained summary describes the identity certificate as self-signed and untrusted by the client; the actual certificate chain was not retained for independent inspection.

## O3 — Independent TLS test

The retained summary reports that a separate TLS test reproduced certificate verification failure. Its exact command, execution context, endpoint and raw output are unavailable. This corroborates the reported trust failure, with limited reproducibility until the test is recaptured.

## O4 — Local/deployed source comparison

The retained summary reports that local HTTPX configuration included `verify=False`, whereas the deployed client did not specify that argument. Full source snippets, filenames, revisions and image digest were not retained. This supports a configuration/source discrepancy, but does not identify its origin. Omitting the argument normally enables HTTPX verification; effective CA/environment configuration still needs inspection. Disabling verification is not a recommended remediation.

## O5 — Process snapshot

The retained interpretation of `ps -ef` lists:

| PID | Reported process |
| --- | --- |
| 1 | `/bin/sh -c /app/entrypoint.sh` |
| 7 | `/bin/sh /app/entrypoint.sh` |
| 11 | Python 3.11 running `uvicorn chatbot.app:app` |
| 67 | `ps -ef` diagnostic command |

No `python -m mcpserver.server` process was reported. This table is a summary, not the original complete process listing. It reports absence at the inspected moment, not permanent absence or a captured exit code.

## O6 — Startup script

Preserved excerpt:

```sh
python -m mcpserver.server &
```

The retained summary reports that Uvicorn starts subsequently. The full script was not retained. `&` backgrounds MCP and lets the shell continue; it does not start Uvicorn by itself or supervise MCP.

## O7 — Docker restart policy

Recorded command:

```bash
docker inspect crapi-chatbot --format '{{json .HostConfig.RestartPolicy}}'
```

Recorded result, formatted:

```json
{
  "Name": "no",
  "MaximumRetryCount": 0
}
```

Docker was not configured to restart this container through its restart policy. This does not independently prove the absence of other supervisors. Container restart policies do not directly restart a failed background process while the container remains running.

## O8 — Health-check evidence gap

The retained summary reports running status without a chatbot health status displayed. No actual health-check definition was inspected in the available text. It is therefore premature to claim a missing or defective health check. Proposed `/health/live` or readiness endpoints discussed in the retained analysis were design examples, not verified crAPI endpoints.

## Evidence to capture next

Capture timestamped, redacted logs and process output from the same startup; exact state request details; the verification-enabled TLS test and certificate chain; image/source identifiers; effective trust configuration; configured health checks; and controlled post-fix results. Exclude passwords, API keys, access tokens, cookies, authorisation headers and sensitive configuration values. Review command output locally before adding it to this repository.

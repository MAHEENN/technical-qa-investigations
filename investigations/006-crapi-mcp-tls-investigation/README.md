# 006 — crAPI MCP TLS investigation

Status: open investigation; reported failure mechanism identified, underlying cause and recovery unverified.

## Scope

Local OWASP crAPI Docker deployment investigated on 17 November 2026. This independent open-source investigation concerns a local deployment; no production impact was established. The investigation examined a chatbot state response, an MCP authentication failure, and container process behaviour.

## Evidence and confidence

This report uses retained investigation summaries and excerpts. Original screenshots, complete traceback and source listings are not included in this repository. Findings are **reported observations**, not independently confirmed runtime results from this documentation review. See [observations](evidence/observations.md) for provenance and limits.

## Findings

| Finding | Assessment |
| --- | --- |
| Chatbot state request returned HTTP 200 with an uninitialised model message | Reported observation, O1 |
| MCP authentication/API-key retrieval encountered TLS certificate verification failure | Reported traceback finding, O2 |
| An independent TLS test reproduced a trust failure | Reported result; command and raw output unavailable, O3 |
| Local and deployed HTTP client configurations differed | Reported source comparison; exact revisions unavailable, O4 |
| Uvicorn was running while MCP was absent from a process snapshot | Reported observation, O5 |
| Entrypoint launched MCP in the background | Reported script excerpt, O6 |
| Container restart policy was `no` | Recorded configuration excerpt, O7 |

MCP termination following the reported startup TLS exception is a working hypothesis supported by its later reported absence. Its exit code was not captured. The specific certificate-chain defect and the reason for source/image drift remain unresolved. **The investigation does not establish that MCP failure caused the chatbot model to be uninitialised.** Health-check configuration and coverage were not verified.

## Reproduction and verification guide

These are follow-up commands for the local deployment, not a claim that they were rerun while writing these files. They assume the reported container name and paths still apply.

```bash
docker compose ps
docker logs --timestamps --tail 200 crapi-chatbot
docker exec crapi-chatbot ps -ef
docker exec crapi-chatbot cat /app/entrypoint.sh
docker inspect crapi-chatbot --format '{{json .HostConfig.RestartPolicy}}'
docker inspect crapi-chatbot --format '{{json .Config.Healthcheck}}'
docker inspect crapi-chatbot --format '{{json .State.Health}}'
docker inspect crapi-chatbot --format '{{.Image}}'
docker image inspect "$(docker inspect crapi-chatbot --format '{{.Image}}')" --format '{{json .RepoDigests}}'
```

Prerequisites: Docker Engine access, the Compose plugin, and an existing deployment. `docker exec` requires a running container; `ps` and `cat` must exist in its image. Health fields may be absent or null when no health check is configured. `.Image` is the local image ID; `RepoDigests` may be empty for locally built images. These commands inspect state; they do not reproduce the original fault.

Run Compose commands from the deployment's Compose directory. Logs and startup scripts can contain sensitive values: inspect locally and redact before sharing. Do not publish a full environment dump or unrestricted container inspection.

1. Repeat the original chatbot state request in browser developer tools. Its exact URL/method were not retained in the available text; record them before claiming exact reproduction. Check both HTTP status and response body.
2. Correlate MCP logs and process snapshots from the same startup attempt, with timestamps and exit status where possible.
3. Locate the HTTPX client used for the identity request inside the deployed image. Compare it with the local source and record image digest and source revision.
4. Repeat a verification-enabled TLS request from the same container environment to the same identity endpoint. Record the command, certificate issuer/chain, hostname and trust configuration, without credentials.
5. Validate remediation with MCP authentication, sustained process availability and the intended MCP operation. Test chatbot initialisation separately.

Exact reproduction is incomplete until the original endpoint, request, deployment version and TLS-test command are captured. No remediation or recovery has been verified.

## Files

- [RCA](RCA.md): failure mechanism, uncertainties and proposed remediation.
- [Observations](evidence/observations.md): sanitised evidence register.
- [Technical notes](technical-notes.md): interpretation of HTTP, TLS and process-lifecycle evidence.

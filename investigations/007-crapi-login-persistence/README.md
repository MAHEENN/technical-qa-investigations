# Investigation 007 — crAPI login and JWT persistence

A successful login to a local OWASP crAPI deployment returned HTTP 200 from `POST /identity/api/auth/login`. A separate PostgreSQL query found one matching fixture account with a non-empty stored token. The stored value's fingerprint changed after sign-out and re-login, consistent with the login flow persisting a new JWT. No defect was established.

## Evidence

| Layer | Recorded observation | What it establishes |
| --- | --- | --- |
| HTTP | `POST /identity/api/auth/login` returned HTTP 200 in the browser's Network panel. | The endpoint returned a successful HTTP status. |
| Java source | `AuthController.java` combines `@RequestMapping("/identity/api/auth")` with `@PostMapping("/login")`. `UserServiceImpl.authenticateUserLogin` uses `authenticationManager`, generates a JWT on the successful path and calls `updateUserToken`. | The reviewed source connects the route to authentication and a token update. |
| Persistence mapping | `UserRepository extends JpaRepository<User, Long>`. The `User` entity maps to `user_login` through `@Table(name = "user_login")`. | The source identifies the entity, key type and mapped table. |
| Database | A read-only query against `public.user_login` in database `crapi`, using the local PostgreSQL role `admin`, returned ID `8`, fixture email `qa.tester001@example.com` and token status `PRESENT`. | One matching row contained a non-null, non-empty `jwt_token` value. |
| Before and after | The stored JWT fingerprint changed from A to B after sign-out and re-login. A and B are labels. | The stored values differed between the two reads. |

## Architecture

```text
Browser → POST /identity/api/auth/login → AuthController
  → UserServiceImpl.authenticateUserLogin
  → authenticationManager → JWT generation → updateUserToken
  → UserRepository → User entity → PostgreSQL public.user_login.jwt_token
```

The diagram traces the successful path in the reviewed source. The HTTP status and database reads were independent observations. The database read after login shows that the updated value was visible to a separate connection.

## Verification limits

The before/after comparison does not identify the exact SQL statement, transaction boundary or commit timing. It also leaves open the possibility of a concurrent write. The investigation did not compare the JWT in the API response with the stored value, test the prior JWT after re-login, or establish a source revision to deployed-image match. The report uses recorded observations from the original investigation. The runtime checks were not rerun for this write-up. No raw JWT or fingerprint is included.

## Follow-up

Build a Playwright API integration test in TypeScript that logs in with an isolated fixture, asserts HTTP 200 and compares the returned JWT with the value read independently from PostgreSQL. Confirm the deployed response contract first. Keep credentials and tokens out of test output, traces and artifacts.

See the [technical reference](technical-reference.md) for commands, schema details, and security observations.

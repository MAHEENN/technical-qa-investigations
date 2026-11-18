# Investigation 007 — crAPI login technical reference

[Investigation report](README.md)

## Trace the source and inspect the database

Run the source commands from the crAPI checkout. Run the Docker commands from the active deployment's Compose directory. This procedure assumes a running local deployment and an existing fixture account.

```bash
git rev-parse HEAD
rg -n 'class AuthController|@RequestMapping|@PostMapping|authenticateUserLogin|authenticationManager|generateJwtToken|updateUserToken|interface UserRepository|class User\b|jwtToken' services/identity/src/main/java
```

```bash
docker compose ps
printf 'PostgreSQL container name: '
read -r pg_container
docker exec -it "$pg_container" psql -X -v ON_ERROR_STOP=1 -P pager=off -U admin -d crapi
```

Choose the running PostgreSQL container shown by Compose. The command uses the recorded local role `admin` and database `crapi`. If the connection prompts for a password, enter it interactively. The same read queries can use a role with appropriate read privileges.

In `psql`, inspect the connection and table definition.

```sql
\conninfo
\d public.user_login
```

The recorded schema included these columns.

| Column | PostgreSQL type |
| --- | --- |
| `id` | `bigint` |
| `email` | `character varying(255)` |
| `jwt_token` | `character varying(500)` |
| `password` | `character varying(255)` |
| `role` | `smallint` |

The table had a primary key on `id` and a check constraint that bounded non-null `role` values to 0–3. The Java `jwtToken` property corresponds to the PostgreSQL `jwt_token` column.

## Verify token presence and change

Set the fixture email in `psql`. The value shown uses the reserved `example.com` domain. Keep the client in autocommit mode so each query reads independently.

```sql
\set fixture_email 'qa.tester001@example.com'

SELECT id, email,
       CASE
           WHEN jwt_token IS NULL THEN 'NULL'
           WHEN jwt_token = '' THEN 'EMPTY'
           ELSE 'PRESENT'
       END AS token_status
FROM public.user_login
WHERE email = :'fixture_email';
```

Recorded result for the fixture:

| id | email | token_status |
| --- | --- | --- |
| `8` | `qa.tester001@example.com` | `PRESENT` |

After confirming a single row with `PRESENT`, capture the baseline as a client variable. The `\gset` command stores the result without printing the fingerprint.

```sql
SELECT md5(jwt_token) AS before_fingerprint
FROM public.user_login
WHERE email = :'fixture_email'
  AND jwt_token IS NOT NULL
  AND jwt_token <> ''
\gset
```

Open `http://localhost:8888`, start recording requests in the browser's Network panel, sign out and sign back in with the fixture account. Confirm HTTP 200 for `POST /identity/api/auth/login`. Use the same PostgreSQL client to check the result.

```sql
SELECT id,
       CASE
           WHEN jwt_token IS NULL THEN 'NULL'
           WHEN jwt_token = '' THEN 'EMPTY'
           WHEN md5(jwt_token) <> :'before_fingerprint' THEN 'CHANGED'
           ELSE 'UNCHANGED'
       END AS comparison
FROM public.user_login
WHERE email = :'fixture_email';

\unset before_fingerprint
```

Expect one row for the same fixture ID and compare the classification with the recorded outcome, `CHANGED`. MD5 here is a local equality aid. A different digest establishes that the input changed. An equal digest alone cannot prove byte-for-byte equality.

## Interpret the persistence evidence

- Spring composes the controller and method mappings to route the POST request. The service coordinates authentication, token generation and the persistence call.
- `JpaRepository<User, Long>` identifies the mapped entity and its Java key type. JPA manages persistence through the mapping. The login call trace and table definition leave the specific SQL statement unverified.
- A JPA flush can send pending SQL to PostgreSQL before commit. The independent read establishes visibility when sampled. Exact transaction boundaries and causal attribution require additional evidence.

## Security observations

- **Potential account enumeration.** If the deployed login path exposes different responses for an unknown account and a known account with invalid credentials, those differences could disclose account existence. This investigation covered successful login. External failure behaviour remains unverified.
- **Intentional Log4j code.** The reviewed login flow contains a configuration-dependent Log4j branch deliberately added to crAPI. Its activation and runtime behaviour were outside the scope of this investigation. [OWASP crAPI source](https://github.com/OWASP/crAPI/blob/develop/services/identity/src/main/java/com/crapi/service/Impl/UserServiceImpl.java)
- **Token handling.** The database queries above emit only status or comparison results alongside fixture metadata. A changed stored JWT does not establish revocation or expiry of the previous JWT.

## Automation acceptance criteria

1. Confirm the target build's login request and response fields. Use a dedicated account and prevent concurrent writers for that fixture during the test.
2. Use Playwright's API client to send the login and assert HTTP 200 and a non-empty JWT field. Supply credentials through the test environment.
3. Use a parameterised PostgreSQL read on a separate connection. Assert exactly one matching fixture and compare the stored value and the returned JWT in memory. Assert on the boolean result with a fixed failure message so assertion output cannot print either token.
4. Publish only safe outcomes such as HTTP status, row count and token-match status. Keep request and response bodies, database credentials and token values out of logs and artifacts.

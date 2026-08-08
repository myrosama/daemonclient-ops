# DaemonClient Audit Findings

Read-only audit completed 2026-08-06 across the API shim, deployment service,
auth, D1/Firestore, Telegram storage, web, mobile, Firebase, self-hosting, and
CI. No fixes were made as part of this audit.

Use this file as an engineering backlog. Fix the highest-priority confirmed
issues first, add regression tests before changing behavior, and do not modify
unrelated cleanup or README work.

## Critical Fixes

1. **P0: Hosted provisioning can mark broken workers as successful.** D1
   migrations are sent as multi-statement SQL and failures are ignored. A
   partially initialized database can become permanently deployed.
   References: `deployment-service/src/index.ts:293-317`,
   `deployment-service/src/cloudflare-api.ts:93-117`,
   `schema/schema.mjs:110-119`.

2. **P0: Mobile does not reliably switch to the user worker.** Mobile can keep
   the central endpoint after login, sending data to the wrong backend or
   Firestore instead of the user's D1.
   References: `immich/mobile/lib/providers/auth.provider.dart:81-84,125-131`.

3. **P1: Legacy workers still accept forgeable sessions.** `APP_IDENTIFIER`
   remains a fallback signing secret when `SESSION_SECRET` is missing.
   References: `immich-api-shim/src/selfhost-auth.ts:26-44`,
   `immich-api-shim/src/auth.ts:119-137`.

4. **P1: Ownership checks can fail open.** If the D1 ownership lookup errors,
   requests may continue; several photo methods also lack owner predicates.
   References: `immich-api-shim/src/owner-gate.ts:81-87`,
   `immich-api-shim/src/d1-adapter.ts:98-104,161-175`.

5. **P1: Sessions are too long-lived and contain refresh credentials.** Long
   lived signed sessions are stored in browser storage, especially in Drive.
   References: `immich-api-shim/src/auth.ts:15,130-137`,
   `drive/src/api.js:38-41`.

6. **P1: Web uploads can bypass encryption policy.** The web client silently
   falls back to plaintext when encryption material is unavailable, and the
   server trusts client-supplied encryption metadata.
   References: `immich/web/src/lib/utils/daemonclient-drive.ts:46-53,303-305`,
   `immich-api-shim/src/assets.ts:1146-1173,1319-1325`.

7. **P1: Delete/undo semantics can lose media.** Normal delete permanently
   removes Telegram data, while restore only restores metadata.
   References: `immich-api-shim/src/assets.ts:535-560,739-790`.

8. **P1: Single-chunk Telegram originals are leaked after deletion.**
   Single-file uploads store `telegramOriginalId`, but deletion only iterates
   `telegramChunks`.
   References: `immich-api-shim/src/assets.ts:1469-1475,767-785`.

9. **P1: Firestore partial updates can erase fields and failed writes are
   ignored.** REST PATCH calls omit update masks and response failures are not
   checked.
   References: `immich-api-shim/src/helpers.ts:285-311`.

10. **P1: Per-user workers do not receive Turnstile protection.** The
    deployment service does not bind `TURNSTILE_SECRET`, leaving password login
    exposed to credential stuffing.
    References: `immich-api-shim/src/auth.ts:78-90`,
    `deployment-service/src/index.ts:106-122`.

## Correctness Risks

11. **P1: Firestore media rows are not normalized like D1 rows.**
    `telegramChunks` can remain a JSON string and break original/media loading.
    References: `immich-api-shim/src/assets.ts:1756-1762,2228-2230`.

12. **P1: Mobile albums are not persisted through sync.** Albums can disappear
    after a sync reset or app restart.
    References: `immich/mobile/lib/infrastructure/repositories/sync_stream.repository.dart:54-58`,
    `immich-api-shim/src/sync.ts:186-274`.

13. **P1: Search responses are incomplete for mobile's strict Dart parser.**
    Missing `albums`, `total`, and required asset fields can crash parsing.
    References: `immich-api-shim/src/search.ts:38-40,99-138`,
    `immich/mobile/openapi/lib/model/search_response_dto.dart:53-55`.

14. **P1: Timeline bucket counts ignore some visibility filters.** Archive and
    locked views can show incorrect month counts or blank buckets.
    References: `immich-api-shim/src/timeline.ts:92-117,134-163`.

15. **P1: Album settings are optimistic only.** Album order/activity settings
    and several user preferences are returned as hardcoded defaults and do not
    persist.
    References: `immich-api-shim/src/albums.ts:190-211,463-467`,
    `immich-api-shim/src/user.ts:15-19`.

16. **P2: Archive downloads silently omit client-encrypted assets and do not
    enforce archive size.**
    References: `immich-api-shim/src/assets.ts:2639-2742`.

17. **P2: ZIP filenames are not sanitized.** User filenames can become unsafe
    archive paths.
    References: `immich-api-shim/src/assets.ts:2701-2712`,
    `immich-api-shim/src/zip.ts:59-73`.

18. **P2: Service-worker caches are insufficiently user/rendition scoped.**
    Media from another account or stale repaired thumbnails can survive cache
    transitions.
    References: `immich/web/src/service-worker/index.ts:125-136,390-400,532-570`.

## Release And Operations

19. **P1: Hosted shim bundle can drift from source.** The generated bundle is
    checked in, but regeneration is ignored/undocumented and CI does not verify
    parity.
    References: `deployment-service/src/shim-bundle.ts:1-4`,
    `.gitignore:70-71`.

20. **P1: CI misses important deployable components.** It excludes schema,
    auth-worker, proxy, selfhost, web, Firebase configuration, and mobile PR
    validation.
    References: `.github/workflows/ci.yml:37-50`,
    `.github/workflows/mobile-build.yml:9-15`.

21. **P1: API typechecking is missing from CI.** Documentation requires it, but
    CI only runs tests.
    References: `CONTRIBUTING.md:27-35`, `.github/workflows/ci.yml:64-71`.

22. **P1: Historical/local secrets need rotation and scanning.** Service-account
    files and other credential-bearing paths exist in repository history and
    local environments.
    References: `.gitignore:4-16`, `backend-server/service_account.json`,
    `functions/serviceAccountsKey.json`.

23. **P2: Firebase Photos shell caching can serve stale deployments.**
    `/app.html` is broadly cached, while only `/index.html` has no-cache rules.
    References: `firebase.json:142-199`.

24. **P2: Deployment observability is weak.** API/deployment/auth workers lack
    durable deployment state, readiness checks, alerts, and structured error
    reporting.
    References: `deployment-service/src/index.ts:266-268`,
    `immich-api-shim/src/index.ts:177-183`.

## High-Value Features

1. Implement real cross-user shared albums, including album/user/asset sync
   events. The current Shared filter intentionally returns empty.

2. Add resumable client-side uploads for large mobile videos instead of sending
   the entire file before server-side chunking.

3. Add a repair/reconciliation dashboard for broken D1 schemas, stale workers,
   missing Telegram objects, and failed deployments.

4. Add server-backed EXIF and filename search with complete mobile/web DTO
   contracts.

5. Add contract tests that exercise the generated mobile parser against every
   shim response.

6. Add one protected release workflow that builds all clients, regenerates the
   shim bundle, validates migrations, deploys, and health-checks every target.

7. Scope Drive IndexedDB by Firebase UID and guarantee cache cleanup on logout
   and account switching.

8. Implement password change support or remove the UI control until it exists.

## Existing Strengths

- The shim suite has 35 test files and 294 tests.
- Firebase token verification checks algorithm, signature, expiration, audience,
  and issuer.
- SQL identifier injection was addressed with a column allowlist and tests.
- Server-side upload encryption fails closed when key material is missing.
- Firestore rules restrict per-user documents.
- Telegram proxy validation has dedicated SSRF/host/redirect tests.

## Agent Instructions

1. Fix P0 items before product features.
2. Add a regression test before each behavior change.
3. Test both D1 and Firestore fallback paths where both are supported.
4. Test generated mobile DTO parsing, not only TypeScript response shapes.
5. Keep cleanup/README changes separate from functional/security commits.
6. Do not reset, revert, or stage unrelated existing worktree changes.

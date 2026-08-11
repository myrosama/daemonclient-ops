# DaemonClient — operator repository

Private. This holds the parts of DaemonClient that run **the managed service at
daemonclient.uz** and are not part of the open-source product.

The public repository is [myrosama/DaemonClient](https://github.com/myrosama/DaemonClient).
Everything a self-hoster needs lives there. Nothing here is required to run
DaemonClient yourself, and nothing here should ever be merged back.

## Why the split

Three separate reasons, and each one on its own is sufficient:

1. **It carries live credentials.** `backend-server/` authenticates as a real
   Telegram *user account* (Telethon, not a bot) in order to talk to BotFather
   on a new user's behalf. Publishing the code that uses those sessions is a
   standing invitation to study how to abuse them.
2. **A self-hoster must never run it.** The managed signup flow creates a bot
   *for* you. Self-hosting deliberately walks you through BotFather yourself,
   so the operator never touches your credentials. Shipping this alongside the
   self-host CLI would suggest a shortcut that undermines the whole premise.
3. **The planning docs describe unfixed problems.** `docs/FINDINGS.md` lists
   verified security findings, several still open, against a service with live
   users. That is not a public document until the findings are closed.

## What is here

| Path | What it is | Deployed as |
|---|---|---|
| `backend-server/` | Flask + Telethon. Creates a Telegram bot and private channel for a new managed user, then transfers both to them. Also holds the managed `/startSetup` entry point. | Render |
| `functions/` | Firebase Functions. Operator alerting only — a Telegram message on signup, on setup complete, on ownership transfer, plus a `/stats` command. No product feature depends on it. | Firebase Functions |
| `scripts/post_updates.py` | Posts the latest commit to the operator's Telegram announcements channel. Called from a pre-push hook. | local |
| `daemon-cli/` | An unreleased Python CLI (`pip install daemonclient`) for uploading and downloading from a terminal. Predates the current architecture and still hardcodes a Firebase key. Kept for reference. | not published |
| `docs/` | Operator planning, audits and security findings. | — |

## Credentials that leaked

These were committed to the **public** repository and are retrievable from its
git history. Removing the files does not unpublish them.

| Credential | Where it leaked | Severity | Action |
|---|---|---|---|
| Telegram `API_ID` + `API_HASH` | `backend-server/generate_session.py` | moderate | nothing to revoke — see below |
| Firebase Web API key | `daemon-cli/daemon.py`, and 5 files still in the public repo | low | restrict by referrer/API in the Google Cloud console |
| Cloudflare API token, R2 keys | shared in a chat transcript | **high** | rotate |

**On the Telegram pair, precisely.** They identify an *application*, not an
account. Nobody can sign in as you with them — that still needs a phone number
and a login code. What they allow is a third party presenting themselves to
Telegram as this app; abuse attributed to it can get the app restricted, which
would break managed bot creation. Telegram offers no rotation for an
`api_hash`, so there is no revoke button to press. Watch for the app being
flagged, and register a fresh one on another account if it is.

The credential that *is* account-level access is the Telethon **session
string** — full control of the user account it was minted from. Those live in
Firestore, are read at runtime, and have never been in git. That is the one to
protect.

`generate_session.py` no longer hardcodes anything; it reads `TELEGRAM_API_ID`
and `TELEGRAM_API_HASH` from the environment.

## Running backend-server

Render deploys from this repository. It needs, as environment variables:

```
TELEGRAM_API_ID          from my.telegram.org
TELEGRAM_API_HASH        from my.telegram.org
TURNSTILE_SECRET         Cloudflare Turnstile — /startSetup fails closed without it
FIREBASE_SERVICE_ACCOUNT the service account JSON
```

Secrets are not committed here either. `.env` and `service_account.json` are
gitignored, the same as in the public repository.

## Reading order for the docs

| File | What it is |
|---|---|
| `docs/AUDIT_2026-08-03.md` | the most recent full audit — what is live, what is dead |
| `docs/FINDINGS.md` | 22 verified findings; several still open |
| `docs/MASTER_PLAN.md` | the phased plan |
| `docs/SCRATCHPAD.md` | rolling status |
| `docs/HANDOFF.md` | onboarding for whoever picks this up next. Its section 1 claims a live account takeover — that was **verified false**; Firestore rules block it. |
| `docs/GATES.md` | the four-gate review process |
| `docs/CLOUDFLARE_OAUTH.md` | the managed one-click Cloudflare flow; not used by self-hosting |
| `docs/seo/PLAN.md`, `docs/seo-strategy.md` | search strategy for the public site |
| `docs/design-prompts.md` | design direction notes |

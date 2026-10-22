# Intent: Remember me at login

Author: Anders Grandjean-Thomsen

## Problem

Users are logged out and have to sign in again about once a week. Most work from their own laptop and want to stay logged in. Some work on shared machines at client sites, where a session must not stay open any longer than it does today.

Today a login yields one access token that lives 8 days (`ACCESS_TOKEN_EXPIRE_MINUTES` in `backend/app/core/config.py`) and is kept in `localStorage`, so every session behaves the same way regardless of the machine.

## Proposed outcome

The login form has a "Remember me" checkbox, off by default. Checked, the user stays logged in on that machine across browser restarts for longer than today. Unchecked, the session lasts no longer than it does today on any machine. Logout still clears the session either way.

## Affected users and systems

- All users who log in (checkbox on the login page). Users on shared machines are the ones the default protects.
- This repo only: the React login page and auth hook (`frontend/src/hooks/useAuth.ts`, `frontend/src/main.tsx`), and at most the login endpoint in the FastAPI backend.

## Constraints

- Keep it small.
- No change to how tokens work: the same JWT access token, same issuing and validation, no refresh tokens.
- No change to the database: no migration, no new tables or columns, no server-side session store.
- Unchecked "Remember me" must never produce a session that outlives today's 8-day token.
- Existing auth tests stay green; the new behaviour gets tests at the login boundary.

## Open questions

- "Stay logged in" longer than a week conflicts with "no change to how tokens work" if the token lifetime is part of that rule. Is raising the access-token lifetime for remembered sessions (a config value or a per-login expiry argument, no change to token format or validation) acceptable, or must the token stay at 8 days and "remember me" only decide whether the token survives closing the browser?
- How long should a remembered session last: 30 days, 90 days, until explicit logout?
- Should unchecked sessions end when the browser closes (a shorter session than today, which the problem statement allows but does not ask for), or keep today's exact behaviour?

# Plan: Remember me at login (from intent.md 2026-10-22)

## Solution

The login form gets a "Remember me" checkbox, off by default. Checked, login returns a 30-day token kept in `localStorage`, so the session survives browser restarts. Unchecked, login returns today's 8-day token kept in `sessionStorage`, so closing the browser ends the session. Logout clears both.

## Decisions

- Backend: `POST /login/access-token` accepts an optional form field `remember_me` (bool, default `false`) beside the `OAuth2PasswordRequestForm`. True picks the expiry from a new setting `REMEMBER_ME_EXPIRE_MINUTES` (default `60 * 24 * 30`); false keeps `ACCESS_TOKEN_EXPIRE_MINUTES`. Same JWT, same `create_access_token`, same validation, no new claims. No database change.
- Frontend: one token-storage helper (`frontend/src/lib/token.ts`) owns where the token lives: `getAccessToken()` reads `localStorage` then `sessionStorage`; `setAccessToken(token, remember)` writes to `localStorage` when remembered, else `sessionStorage`, and clears the other; `clearAccessToken()` removes both. `useAuth.ts` (`isLoggedIn`, `login`, `logout`), the client config and the 401/403 handler in `main.tsx` all go through it. No other direct `localStorage` access for the token.
- Login page: `Checkbox` from `components/ui` with label "Remember me" and `data-testid="remember-me-checkbox"`, between the password field and the button. Form schema gains `remember_me: z.boolean()` defaulting to `false`; the value is sent as `remember_me` in the login body (the generated `Body_login_login_access_token` type gains it after regeneration).
- Client regenerated with `scripts/generate-client.sh`.
- Users already logged in before release keep their `localStorage` token; it reads fine and expires on its own schedule.
- Resolved from intent: a longer expiry for remembered sessions is allowed (token format and validation unchanged); remembered sessions last 30 days; unchecked sessions end when the browser closes.

## Files that change

- Modified: `backend/app/core/config.py`, `backend/app/api/routes/login.py`, `backend/tests/api/routes/test_login.py`
- New: `frontend/src/lib/token.ts`
- Modified: `frontend/src/hooks/useAuth.ts`, `frontend/src/main.tsx`, `frontend/src/routes/login.tsx`
- Modified: `frontend/tests/auth.setup.ts`, `frontend/tests/login.spec.ts`
- Generated: `frontend/src/client/*`, `frontend/openapi.json`

## Order of work

1. Backend: add `REMEMBER_ME_EXPIRE_MINUTES`, the `remember_me` form field and the expiry choice in the login route, with tests at the login endpoint.
2. Regenerate the client.
3. Add `frontend/src/lib/token.ts`; switch `useAuth.ts` and `main.tsx` to it.
4. Add the checkbox to `frontend/src/routes/login.tsx` and pass `remember_me` through `loginMutation`.
5. E2e: tick the checkbox in `auth.setup.ts`; add storage-location tests to `login.spec.ts`.

## Testing seams

- Backend: `POST /login/access-token` through the existing `client` TestClient fixture. Decode the returned JWT with `settings.SECRET_KEY` and assert `exp` is about 30 days out with `remember_me=true` and about 8 days without it. Prior art: `backend/tests/api/routes/test_login.py`.
- Frontend: Playwright on the login page. Unchecked login leaves `sessionStorage.access_token` set and `localStorage.access_token` unset; checked login does the reverse. Prior art: `frontend/tests/login.spec.ts`, which already reads and writes `localStorage` via `page.evaluate`.

## Risks

- Playwright's saved `storageState` captures `localStorage` but not `sessionStorage`. With the unchecked default, `auth.setup.ts` must tick the checkbox or every authenticated e2e spec runs logged out. This is the one change that can break the whole suite.
- Backend pytest and Playwright are outside `VERIFY` (see `UNTESTED` in `docs/agents/project.md`). The PR review list must state they were run.
- A 30-day token cannot be revoked before expiry; the constraints rule out server-side sessions. A lost laptop stays logged in until the token expires.
- Chrome and Firefox session restore can bring `sessionStorage` back after a crash or "continue where you left off". "Ends when the browser closes" is strong, not absolute.
- A `sessionStorage` token is per tab. An unchecked user who opens the app in a second tab by typing the URL must log in again there.

## Out of scope

- Refresh tokens, token revocation, a session list, sliding expiry.
- Any change to the user table or any new table.

## Tickets
<!-- filled by /to-tickets -->
- FAS-9 https://linear.app/grandjean/issue/FAS-9/login-endpoint-honours-remember-me
- FAS-10 https://linear.app/grandjean/issue/FAS-10/remember-me-checkbox-decides-where-the-session-lives
- FAS-11 https://linear.app/grandjean/issue/FAS-11/checked-remember-me-keeps-users-logged-in-for-30-days

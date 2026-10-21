# Plan: New-user onboarding (from intent.md 2026-10-21)

## Solution

New users see a 3-step checklist on the dashboard (first item, edit profile name, invite someone) until all are done; progress is stored in the DB. Superusers get a page showing users registered in a window, how many completed within 7 days of their own registration, and the rate (default window: last 30 days).

## Decisions

- New table `onboarding`, one row per user: `user_id` (PK, FK to `user`, cascade delete), `first_item_at`, `name_edited_at`, `invite_sent_at`, `invite_count`, `completed_at`. `user` table untouched.
- Rows created only in `POST /users/signup`. Existing users, admin-created users, initial superuser: no row, no checklist, excluded from stats.
- Step capture by hooks, idempotent (first timestamp wins, steps never revert):
  - `POST /items/` calls `mark_first_item` (one call, no behaviour change to items).
  - `PATCH /users/me` calls `mark_name_edited` when `full_name` changes to a different non-empty value.
- `completed_at = max(three timestamps)` once all are set.
- Pure function `completed_within(created_at, completed_at, days=7) -> bool`; stats use it or an equivalent SQL expression.
- Invite: `POST /onboarding/invite {email}`.
  - 400 if `emails_enabled` is false or the address is the user's own; 429 after 5 sends per user (`invite_count`).
  - New `invite.html` template, link `{FRONTEND_HOST}/signup`, sent via existing `send_email`.
  - `invite_sent_at` set only after a successful send.
  - Address never persisted or logged; check that `send_email`'s result log does not include it.
  - No already-registered check (avoids leaking existence).
- `GET /onboarding/me`: step flags + `completed`; 404 when no row (frontend hides checklist).
- `GET /onboarding/stats?start&end`: superuser-only (`get_current_active_superuser`); returns `{registered, completed_within_7d, completion_rate}`; window is users registered in [start, end); rate 0 when `registered` is 0. Default window: last 30 days.
- Frontend: `OnboardingChecklist` on the dashboard with inline invite form; new superuser-gated `/onboarding` stats route with sidebar link and date-range filter; page notes that windows ending within 7 days of now understate the rate. Client regenerated with `scripts/generate-client.sh`.
- Resolved from intent: target stays 100/140; "edited name" = changed to a different non-empty value; timestamps recorded going forward, no backfill.

## Files that change

- New: `backend/app/alembic/versions/<rev>_add_onboarding.py`
- New: `backend/app/api/routes/onboarding.py`
- New: `backend/app/email-templates/invite.html`
- New: `backend/tests/api/routes/test_onboarding.py`
- New: `backend/tests/crud/test_onboarding.py`
- New: `frontend/src/components/Onboarding/OnboardingChecklist.tsx`
- New: `frontend/src/routes/_layout/onboarding.tsx`
- New: `frontend/tests/onboarding.spec.ts`
- Modified: `backend/app/models.py`, `backend/app/crud.py`, `backend/app/utils.py` (`generate_invite_email`), `backend/app/api/main.py`
- Modified: `backend/app/api/routes/users.py` (signup, PATCH me), `backend/app/api/routes/items.py` (create hook)
- Modified: `frontend/src/routes/_layout/index.tsx`, `frontend/src/components/Sidebar/AppSidebar.tsx`
- Generated: `frontend/src/client/*`, `frontend/src/routeTree.gen.ts`

## Order of work
1. Model and reversible migration; verify upgrade and downgrade.
2. Crud functions and `completed_within`, with unit tests.
3. Signup row creation; hooks in `PATCH /users/me` and `POST /items/`.
4. `GET /onboarding/me`.
5. Invite route, email template, rate cap.
6. Stats route with superuser guard.
7. Regenerate the client.
8. Checklist component on the dashboard.
9. Stats page and sidebar link.
10. Playwright spec; lint; run full suites.

## Testing seams

- HTTP routes via existing `client` and token-header fixtures, `send_email` patched (prior art: `test_users.py`, `test_login.py`): signup creates row; item create and name edit set steps; invite 400 (emails disabled, own address), 429 over cap, no address stored; stats 403 for normal user; window and 7-day boundary cases.
- Pure `completed_within` and crud completion logic in `tests/crud/`.
- One Playwright spec for checklist and stats page (prior art: `frontend/tests/items.spec.ts`).
- Existing tests stay green; `conftest` teardown deletes `Item` and `User`, FK cascade covers `onboarding`.

## Risks

- `items.py` hook touches an item route: keep to one call, no behaviour change; flag for reviewer.
- Invite can be used to send spam; 5-send cap limits it, no per-address log.
- SMTP failure after server accept is indistinguishable from success; counts may be slightly off.
- Windows ending within 7 days of now understate the rate.
- Regenerated client and `routeTree.gen.ts` produce large diffs; review separately.
- Item step counts items created via the API directly too.

## Out of scope

- Reminders or scheduled emails; analytics beyond the stats page; item feature changes.
- Backfill of existing users; invite attribution or acceptance tracking; showing invited addresses.
- Admin-created users in onboarding.

## Tickets
<!-- filled by /to-tickets -->

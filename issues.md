# End-to-end test for onboarding checklist and stats page

## What to build

A Playwright end-to-end spec that exercises the whole onboarding feature in a browser: a new user signs up, sees the checklist, completes the item, name and invite steps, and the checklist goes away; a superuser opens the Onboarding page and sees stats, and a normal user cannot reach it. Follows the style of the existing Playwright specs.

Waits for the stats page ticket, so both the checklist and the stats page exist.

## Acceptance criteria

- [ ] A new spec in the frontend Playwright tests covers: signup shows the checklist with three unchecked steps; creating an item and editing the name tick those steps; sending an invite (with emails not required to be delivered in the test, or the response mocked) ticks the last step and the checklist disappears.
- [ ] The spec covers a superuser opening the Onboarding page and seeing the three metrics, and a normal user not seeing the sidebar link.
- [ ] The spec is stable across 3 consecutive runs and does not depend on other specs' data.
- [ ] Existing Playwright specs are unchanged and still pass where they can run locally.
- [ ] The repo's verify gate (`uv run prek run --from-ref origin/master --to-ref HEAD`) exits 0.

---

Source: [https://github.com/GrandjeanIo/claude-code-bootcamp-full-stack-fastapi-template/blob/master/docs/intent/001-new-user-onboarding/plan.md](<https://github.com/GrandjeanIo/claude-code-bootcamp-full-stack-fastapi-template/blob/master/docs/intent/001-new-user-onboarding/plan.md>)

## Metadata
- URL: [https://linear.app/grandjean/issue/FAS-8/end-to-end-test-for-onboarding-checklist-and-stats-page](https://linear.app/grandjean/issue/FAS-8/end-to-end-test-for-onboarding-checklist-and-stats-page)
- Identifier: FAS-8
- Status: In Review
- Priority: No priority
- Assignee: Unassigned
- Labels: ready-for-agent, repo:fastapi-template
- Project: [001-new-user-onboarding](https://linear.app/grandjean/project/001-new-user-onboarding-d8e81126bec3/overview). New-user onboarding checklist, invite step and superuser completion stats
- Blocked by: FAS-7
- Created: 2026-10-21T18:32:54.753Z
- Updated: 2026-10-21T19:31:35.020Z

## Comments

- Anders Grandjean-thomsen:

  On the intent PR: [https://github.com/GrandjeanIo/claude-code-bootcamp-full-stack-fastapi-template/pull/3](<https://github.com/GrandjeanIo/claude-code-bootcamp-full-stack-fastapi-template/pull/3>)

------

# Superuser onboarding stats page

## What to build

A superuser sees an "Onboarding" link in the sidebar leading to a stats page showing users registered, completers within 7 days, and the completion rate for a chosen date range, defaulting to the last 30 days. A date-range filter changes the window. The page notes that windows ending within 7 days of now understate the rate, because recent users are still inside their 7 days. Normal users do not see the link and cannot open the page. The generated API client is regenerated to include the stats operation.

Waits for the stats endpoint and for the dashboard checklist ticket, which also regenerates the client.

## Acceptance criteria

- [ ] The frontend API client is regenerated with `scripts/generate-client.sh` and includes the stats operation alongside the earlier onboarding operations. The frontend builds and lints cleanly.
- [ ] A superuser sees an Onboarding sidebar link and the page shows registered, completed within 7 days, and completion rate for the last 30 days by default.
- [ ] Changing the date range updates the three numbers to match the new window.
- [ ] When the window ends within 7 days of now, the page shows the note that the rate may be understated.
- [ ] A normal user does not see the sidebar link, and opening the page directly does not show stats (redirect or access denied, as with the existing admin page).
- [ ] The repo's verify gate (`uv run prek run --from-ref origin/master --to-ref HEAD`) exits 0.

---

Source: [https://github.com/GrandjeanIo/claude-code-bootcamp-full-stack-fastapi-template/blob/master/docs/intent/001-new-user-onboarding/plan.md](<https://github.com/GrandjeanIo/claude-code-bootcamp-full-stack-fastapi-template/blob/master/docs/intent/001-new-user-onboarding/plan.md>)

## Metadata
- URL: [https://linear.app/grandjean/issue/FAS-7/superuser-onboarding-stats-page](https://linear.app/grandjean/issue/FAS-7/superuser-onboarding-stats-page)
- Identifier: FAS-7
- Status: In Review
- Priority: No priority
- Assignee: Unassigned
- Labels: ready-for-agent, repo:fastapi-template
- Project: [001-new-user-onboarding](https://linear.app/grandjean/project/001-new-user-onboarding-d8e81126bec3/overview). New-user onboarding checklist, invite step and superuser completion stats
- Blocking: FAS-8
- Blocked by: FAS-5, FAS-6
- Created: 2026-10-21T18:32:46.278Z
- Updated: 2026-10-21T19:31:33.640Z

## Comments

- Anders Grandjean-thomsen:

  On the intent PR: [https://github.com/GrandjeanIo/claude-code-bootcamp-full-stack-fastapi-template/pull/3](<https://github.com/GrandjeanIo/claude-code-bootcamp-full-stack-fastapi-template/pull/3>)

------

# Onboarding checklist on the dashboard

## What to build

A new user sees a 3-step onboarding checklist on the dashboard (make a first item, edit your profile name, invite someone by email) showing which steps are done. The invite step has an inline form where the user enters an email and sends the invitation, with success and error feedback (including the 5-invite limit and emails-not-configured cases). The checklist disappears once all three steps are done, and is not shown to users who have no onboarding record. Progress comes from the server, so it survives logout and login. The generated API client is regenerated to include the onboarding endpoints available so far.

Waits for the ticket that adds the invite endpoint.

## Acceptance criteria

- [ ] The frontend API client is regenerated with `scripts/generate-client.sh` and includes the onboarding progress and invite operations. The frontend builds and lints cleanly.
- [ ] A freshly signed-up user sees the checklist on the dashboard with all three steps unchecked.
- [ ] After creating an item, and after changing their name, those steps show as done on the dashboard.
- [ ] Submitting an email in the checklist's invite form shows success feedback and marks the invite step done. An error from the server (such as the invite limit) is shown to the user.
- [ ] After logging out and back in, the checklist shows the same progress.
- [ ] Once all three steps are done the checklist is no longer shown.
- [ ] A user with no onboarding record (for example the initial superuser) sees no checklist and no error on the dashboard.
- [ ] The repo's verify gate (`uv run prek run --from-ref origin/master --to-ref HEAD`) exits 0.

---

Source: [https://github.com/GrandjeanIo/claude-code-bootcamp-full-stack-fastapi-template/blob/master/docs/intent/001-new-user-onboarding/plan.md](<https://github.com/GrandjeanIo/claude-code-bootcamp-full-stack-fastapi-template/blob/master/docs/intent/001-new-user-onboarding/plan.md>)

## Metadata
- URL: [https://linear.app/grandjean/issue/FAS-6/onboarding-checklist-on-the-dashboard](https://linear.app/grandjean/issue/FAS-6/onboarding-checklist-on-the-dashboard)
- Identifier: FAS-6
- Status: In Review
- Priority: No priority
- Assignee: Unassigned
- Labels: ready-for-agent, repo:fastapi-template
- Project: [001-new-user-onboarding](https://linear.app/grandjean/project/001-new-user-onboarding-d8e81126bec3/overview). New-user onboarding checklist, invite step and superuser completion stats
- Blocking: FAS-7
- Blocked by: FAS-4
- Created: 2026-10-21T18:32:37.352Z
- Updated: 2026-10-21T19:31:32.194Z

## Comments

- Anders Grandjean-thomsen:

  On the intent PR: [https://github.com/GrandjeanIo/claude-code-bootcamp-full-stack-fastapi-template/pull/3](<https://github.com/GrandjeanIo/claude-code-bootcamp-full-stack-fastapi-template/pull/3>)

------

# Superuser onboarding stats via GET /onboarding/stats

## What to build

A superuser can fetch onboarding metrics for a date window: how many users registered in the window, how many of them completed all three steps within 7 days of their own registration, and the completion rate. The window is users registered in \[start, end), and defaults to the last 30 days when no dates are given. The rate is 0 when nobody registered in the window. Only users with an onboarding record count, so admin-created users, the initial superuser and pre-release users are excluded. Normal users are refused.

Waits for the ticket that adds the invite endpoint.

## Acceptance criteria

- [ ] A superuser calling `GET /onboarding/stats` with no parameters gets `registered`, `completed_within_7d` and `completion_rate` for the last 30 days.
- [ ] A normal (non-superuser) user gets 403, and an unauthenticated request is rejected.
- [ ] With `start` and `end`, a user registered exactly at `start` is counted and one registered exactly at `end` is not.
- [ ] A user who completed exactly 7 days after registering counts as completed, and one who completed just after 7 days does not.
- [ ] A user who has not completed all three steps does not count as completed.
- [ ] `completion_rate` is `completed_within_7d / registered`, and 0 when `registered` is 0.
- [ ] Users with no onboarding record are not counted in `registered`.
- [ ] New backend route tests cover these cases, existing backend tests still pass, and the repo's verify gate (`uv run prek run --from-ref origin/master --to-ref HEAD`) exits 0.

---

Source: [https://github.com/GrandjeanIo/claude-code-bootcamp-full-stack-fastapi-template/blob/master/docs/intent/001-new-user-onboarding/plan.md](<https://github.com/GrandjeanIo/claude-code-bootcamp-full-stack-fastapi-template/blob/master/docs/intent/001-new-user-onboarding/plan.md>)

## Metadata
- URL: [https://linear.app/grandjean/issue/FAS-5/superuser-onboarding-stats-via-get-onboardingstats](https://linear.app/grandjean/issue/FAS-5/superuser-onboarding-stats-via-get-onboardingstats)
- Identifier: FAS-5
- Status: In Review
- Priority: No priority
- Assignee: Unassigned
- Labels: ready-for-agent, repo:fastapi-template
- Project: [001-new-user-onboarding](https://linear.app/grandjean/project/001-new-user-onboarding-d8e81126bec3/overview). New-user onboarding checklist, invite step and superuser completion stats
- Blocking: FAS-7
- Blocked by: FAS-4
- Created: 2026-10-21T18:32:35.194Z
- Updated: 2026-10-21T19:31:30.626Z

## Comments

- Anders Grandjean-thomsen:

  On the intent PR: [https://github.com/GrandjeanIo/claude-code-bootcamp-full-stack-fastapi-template/pull/3](<https://github.com/GrandjeanIo/claude-code-bootcamp-full-stack-fastapi-template/pull/3>)

------

# Invite someone by email via POST /onboarding/invite

## What to build

A signed-up user can invite one other person by email. They submit an address, the app sends an invitation email containing a link to the registration page, and the "invite sent" step is marked done once the email has been sent successfully. The invited address is never stored or logged, including in the existing email-send log line. Each user can send at most 5 invitations. Invitations are refused when email sending is not configured or when the address is the user's own. The app does not check whether the address already belongs to a registered user, so it never reveals who is registered. If the send fails, the step is not marked and the attempt does not count toward the cap.

Waits for the ticket that exposes onboarding progress.

## Acceptance criteria

- [ ] `POST /onboarding/invite` with a valid other address sends one invitation email to it (with email sending mocked in tests), the email body contains a link to the app's `/signup` page, the response is successful, and the user's invite step is then done.
- [ ] The response is 400 and no email is sent when email sending is disabled in settings.
- [ ] The response is 400 and no email is sent when the address is the user's own, compared case-insensitively.
- [ ] After 5 successful sends, the 6th request returns 429 and sends no email.
- [ ] When sending raises an error, the invite step stays not done and the send count is unchanged.
- [ ] The invited address does not appear in any database row, and does not appear in captured log output for a successful invite.
- [ ] An already-registered address gets the same response as any other address.
- [ ] Unauthenticated requests are rejected, and users with no onboarding record get 404.
- [ ] New backend route tests cover these cases, existing backend tests still pass, and the repo's verify gate (`uv run prek run --from-ref origin/master --to-ref HEAD`) exits 0.

---

Source: [https://github.com/GrandjeanIo/claude-code-bootcamp-full-stack-fastapi-template/blob/master/docs/intent/001-new-user-onboarding/plan.md](<https://github.com/GrandjeanIo/claude-code-bootcamp-full-stack-fastapi-template/blob/master/docs/intent/001-new-user-onboarding/plan.md>)

## Metadata
- URL: [https://linear.app/grandjean/issue/FAS-4/invite-someone-by-email-via-post-onboardinginvite](https://linear.app/grandjean/issue/FAS-4/invite-someone-by-email-via-post-onboardinginvite)
- Identifier: FAS-4
- Status: In Review
- Priority: No priority
- Assignee: Unassigned
- Labels: ready-for-agent, repo:fastapi-template
- Project: [001-new-user-onboarding](https://linear.app/grandjean/project/001-new-user-onboarding-d8e81126bec3/overview). New-user onboarding checklist, invite step and superuser completion stats
- Blocking: FAS-6, FAS-5
- Blocked by: FAS-3
- Created: 2026-10-21T18:32:20.173Z
- Updated: 2026-10-21T19:31:29.040Z

## Comments

- Anders Grandjean-thomsen:

  On the intent PR: [https://github.com/GrandjeanIo/claude-code-bootcamp-full-stack-fastapi-template/pull/3](<https://github.com/GrandjeanIo/claude-code-bootcamp-full-stack-fastapi-template/pull/3>)

------

# Expose own onboarding progress via GET /onboarding/me

## What to build

A logged-in user can ask the API for their own onboarding progress: which of the three steps (first item, name edited, invite sent) are done, and whether onboarding is complete overall. A user with no onboarding record (admin-created, initial superuser, or registered before this feature) gets a "not found" response so the frontend knows to hide the checklist. The endpoint requires authentication.

Waits for the ticket that captures the first-item and name-edit steps.

## Acceptance criteria

- [ ] `GET /onboarding/me` for a freshly signed-up user returns 200 with all three step flags false and `completed` false.
- [ ] After the user creates an item and edits their name, the response shows those two steps true and the invite step false.
- [ ] Once all three steps are done, `completed` is true.
- [ ] A user with no onboarding record gets 404.
- [ ] An unauthenticated request is rejected with 401 or 403, the same as other protected routes.
- [ ] New backend route tests cover these cases, existing backend tests still pass, and the repo's verify gate (`uv run prek run --from-ref origin/master --to-ref HEAD`) exits 0.

---

Source: [https://github.com/GrandjeanIo/claude-code-bootcamp-full-stack-fastapi-template/blob/master/docs/intent/001-new-user-onboarding/plan.md](<https://github.com/GrandjeanIo/claude-code-bootcamp-full-stack-fastapi-template/blob/master/docs/intent/001-new-user-onboarding/plan.md>)

## Metadata
- URL: [https://linear.app/grandjean/issue/FAS-3/expose-own-onboarding-progress-via-get-onboardingme](https://linear.app/grandjean/issue/FAS-3/expose-own-onboarding-progress-via-get-onboardingme)
- Identifier: FAS-3
- Status: In Review
- Priority: No priority
- Assignee: Unassigned
- Labels: ready-for-agent, repo:fastapi-template
- Project: [001-new-user-onboarding](https://linear.app/grandjean/project/001-new-user-onboarding-d8e81126bec3/overview). New-user onboarding checklist, invite step and superuser completion stats
- Blocking: FAS-4
- Blocked by: FAS-2
- Created: 2026-10-21T18:32:10.131Z
- Updated: 2026-10-21T19:31:27.275Z

## Comments

- Anders Grandjean-thomsen:

  On the intent PR: [https://github.com/GrandjeanIo/claude-code-bootcamp-full-stack-fastapi-template/pull/3](<https://github.com/GrandjeanIo/claude-code-bootcamp-full-stack-fastapi-template/pull/3>)

------

# Capture first-item and name-edit steps, and completion

## What to build

A signed-up user's onboarding record updates as they use the app. Creating an item marks the "first item" step done. Changing their profile name to a different non-empty value marks the "name edited" step done. Each step records the time it was first completed; later repeats never overwrite it and steps never revert, even if the item or name is later changed or deleted. Once all three steps (first item, name edited, invite sent) are done, the record gets a completion time equal to the latest of the three step times. A helper decides whether a user completed onboarding within 7 days of registering. Users without an onboarding record are unaffected, and item creation and profile update otherwise behave exactly as before.

Waits for the ticket that creates the onboarding record at signup.

## Acceptance criteria

- [ ] After a signed-up user creates an item, their onboarding record shows the first-item step done with a timestamp. A second item does not change that timestamp.
- [ ] After a signed-up user changes their full name to a different non-empty value via `PATCH /users/me`, the name-edited step is done. Saving the same name, an empty name, or an update that does not touch the name does not mark it.
- [ ] Deleting the item or reverting the name leaves the step done.
- [ ] When all three steps are done, the completion time equals the latest step time. It is not set while any step is missing.
- [ ] The 7-day completion helper returns true at exactly 7 days after registration and false just after, and false when there is no completion time. Unit tests cover this.
- [ ] Creating an item or updating the profile for a user with no onboarding record still succeeds with the same response as before.
- [ ] Existing backend tests still pass, and the repo's verify gate (`uv run prek run --from-ref origin/master --to-ref HEAD`) exits 0.

---

Source: [https://github.com/GrandjeanIo/claude-code-bootcamp-full-stack-fastapi-template/blob/master/docs/intent/001-new-user-onboarding/plan.md](<https://github.com/GrandjeanIo/claude-code-bootcamp-full-stack-fastapi-template/blob/master/docs/intent/001-new-user-onboarding/plan.md>)

## Metadata
- URL: [https://linear.app/grandjean/issue/FAS-2/capture-first-item-and-name-edit-steps-and-completion](https://linear.app/grandjean/issue/FAS-2/capture-first-item-and-name-edit-steps-and-completion)
- Identifier: FAS-2
- Status: In Review
- Priority: No priority
- Assignee: Unassigned
- Labels: ready-for-agent, repo:fastapi-template
- Project: [001-new-user-onboarding](https://linear.app/grandjean/project/001-new-user-onboarding-d8e81126bec3/overview). New-user onboarding checklist, invite step and superuser completion stats
- Blocking: FAS-3
- Blocked by: FAS-1
- Created: 2026-10-21T18:32:00.910Z
- Updated: 2026-10-21T19:31:25.827Z

## Comments

- Anders Grandjean-thomsen:

  On the intent PR: [https://github.com/GrandjeanIo/claude-code-bootcamp-full-stack-fastapi-template/pull/3](<https://github.com/GrandjeanIo/claude-code-bootcamp-full-stack-fastapi-template/pull/3>)

------

# Create onboarding record at signup

## What to build

Every user who registers through the public signup flow gets a per-user onboarding record that tracks the three onboarding steps (first item made, profile name edited, invitation email sent) and when the user completed onboarding. The record is stored in a new database table added by a reversible migration, with one row per user that is removed when the user is deleted. Users created any other way (by an admin, the initial superuser, or registered before this change) get no record. The existing user table and user data are unchanged.

## Acceptance criteria

- [ ] The database migration upgrades and downgrades cleanly (upgrade, downgrade, upgrade again all succeed) and leaves the existing user table and its data unchanged.
- [ ] Registering through `POST /users/signup` creates exactly one onboarding record for the new user, with no step completed.
- [ ] Creating a user as an admin, and the initial superuser, create no onboarding record.
- [ ] Deleting a user also removes their onboarding record.
- [ ] New backend tests cover the cases above, and the existing backend tests still pass.
- [ ] The repo's verify gate (`uv run prek run --from-ref origin/master --to-ref HEAD`) exits 0.

---

Source: [https://github.com/GrandjeanIo/claude-code-bootcamp-full-stack-fastapi-template/blob/master/docs/intent/001-new-user-onboarding/plan.md](<https://github.com/GrandjeanIo/claude-code-bootcamp-full-stack-fastapi-template/blob/master/docs/intent/001-new-user-onboarding/plan.md>)

## Metadata
- URL: [https://linear.app/grandjean/issue/FAS-1/create-onboarding-record-at-signup](https://linear.app/grandjean/issue/FAS-1/create-onboarding-record-at-signup)
- Identifier: FAS-1
- Status: In Review
- Priority: No priority
- Assignee: Unassigned
- Labels: ready-for-agent, repo:fastapi-template
- Project: [001-new-user-onboarding](https://linear.app/grandjean/project/001-new-user-onboarding-d8e81126bec3/overview). New-user onboarding checklist, invite step and superuser completion stats
- Blocking: FAS-2
- Created: 2026-10-21T18:31:50.593Z
- Updated: 2026-10-21T19:31:24.295Z

## Comments

- Anders Grandjean-thomsen:

  On the intent PR: [https://github.com/GrandjeanIo/claude-code-bootcamp-full-stack-fastapi-template/pull/3](<https://github.com/GrandjeanIo/claude-code-bootcamp-full-stack-fastapi-template/pull/3>)
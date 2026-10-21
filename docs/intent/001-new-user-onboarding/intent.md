# Intent: New-user onboarding

Author: Anders Grandjean-Thomsen

## Problem

New users register and then do nothing. In the last cohort, 140 users registered and 40 never made an item. No page shows this; the team finds out from support.

## Proposed outcome

Of each 140 new users (about 71%), 100 complete onboarding within 7 days of registration. "Complete" means all three: made a first item, edited their profile name, and invited one other person by email. A superuser can see registered users, completers within 7 days, and the completion rate for any window (default: last 30 days).

To get there:

1. A per-user onboarding checklist with those three steps, shown after registration and on the dashboard until all are done. Progress is stored per user and survives logout.
2. An invite step: the user enters an email, the app sends an invitation email with a registration link, and the step is done when the email is sent.
3. A superuser-only admin page with the window metrics.
4. Frontend for the checklist and admin page, with the generated API client updated.

## Affected users and systems

- All new users (checklist, invite); superusers (admin page).
- This repo only: FastAPI backend, SQLModel/PostgreSQL (new migration), React frontend and generated API client, existing email utilities and SMTP config.

## Constraints

- Keep existing authentication and the superuser rule. No new roles.
- Use existing email utilities and SMTP configuration. No new external service.
- Migrations must be reversible.
- No change to existing user data. No change to the user table beyond what the feature needs.
- Tests for the backend routes and the completion calculation. Existing tests stay green.
- Do not store invited email addresses longer than needed to send the email.
- Out of scope: reminders or scheduled emails, analytics beyond the admin page, changes to item features.

## Open questions

- Baseline vs. target: 100 of 140 already made an item, so the target of 100 completers needs most of those to also edit their name and invite someone. Is 100/140 the agreed target, and is there any data on how many already edit their name or invite?
- Existing users: do users registered before release get a checklist? Do they count in the admin page's "registered in window", or only users registered after release?
- "Edited their profile name": does any save of the name count, or must it differ from the registration value (including when it was empty)?
- "Completed within 7 days": measured from registration to the time the last step is done. Each step needs a completion timestamp; is it acceptable that step times are recorded going forward only, with no backfill?
- Invite step: does one email count regardless of recipient (including the user's own address or an already-registered user)? Should sends be rate-limited, given the address is not kept? Does the registration link carry any attribution to the inviter?
- Because invited addresses are not retained, the invite step records only that an email was sent. Is that enough for the admin page, or is any further invite metric wanted?
- Does a step stay done if the item or name is later reverted or deleted?

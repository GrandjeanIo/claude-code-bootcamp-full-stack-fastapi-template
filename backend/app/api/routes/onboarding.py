from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app import crud
from app.api.deps import CurrentUser, SessionDep, get_current_active_superuser
from app.core.config import settings
from app.models import (
    Message,
    Onboarding,
    OnboardingInvite,
    OnboardingPublic,
    OnboardingStats,
)
from app.utils import generate_invite_email, send_invite_email

router = APIRouter(prefix="/onboarding", tags=["onboarding"])

MAX_INVITES = 5
STATS_DEFAULT_DAYS = 30


@router.get("/me", response_model=OnboardingPublic)
def read_onboarding_me(session: SessionDep, current_user: CurrentUser) -> Any:
    """
    Get own onboarding progress.
    """
    onboarding = session.get(Onboarding, current_user.id)
    if onboarding is None:
        raise HTTPException(status_code=404, detail="Onboarding not found")
    return OnboardingPublic(
        first_item=onboarding.first_item_at is not None,
        name_edited=onboarding.name_edited_at is not None,
        invite_sent=onboarding.invite_sent_at is not None,
        completed=onboarding.completed_at is not None,
    )


@router.post("/invite", response_model=Message)
def send_invite(
    session: SessionDep, current_user: CurrentUser, body: OnboardingInvite
) -> Any:
    """
    Invite someone by email. The address is never stored or logged.
    """
    # Held from the cap check through the increment; released by the commit,
    # or by the session closing when the request fails.
    onboarding = crud.lock_onboarding(session=session, user_id=current_user.id)
    if onboarding is None:
        raise HTTPException(status_code=404, detail="Onboarding not found")
    if not settings.emails_enabled:
        raise HTTPException(status_code=400, detail="Email sending is not enabled")
    if body.email.lower() == current_user.email.lower():
        raise HTTPException(status_code=400, detail="You cannot invite yourself")
    if onboarding.invite_count >= MAX_INVITES:
        raise HTTPException(status_code=429, detail="Invitation limit reached")
    email_data = generate_invite_email()
    sent = send_invite_email(
        email_to=body.email,
        subject=email_data.subject,
        html_content=email_data.html_content,
    )
    if not sent:
        raise HTTPException(status_code=502, detail="Invitation could not be sent")
    crud.mark_invite_sent(session=session, onboarding=onboarding)
    return Message(message="Invitation sent")


@router.get(
    "/stats",
    response_model=OnboardingStats,
    dependencies=[Depends(get_current_active_superuser)],
)
def read_onboarding_stats(
    session: SessionDep, start: datetime | None = None, end: datetime | None = None
) -> Any:
    """
    Onboarding metrics for users registered in [start, end). Defaults to the
    last 30 days.
    """
    end = end or datetime.now(UTC)
    start = start or end - timedelta(days=STATS_DEFAULT_DAYS)
    return crud.get_onboarding_stats(session=session, start=start, end=end)

from typing import Any

from fastapi import APIRouter, HTTPException

from app import crud
from app.api.deps import CurrentUser, SessionDep
from app.core.config import settings
from app.models import Message, Onboarding, OnboardingInvite, OnboardingPublic
from app.utils import generate_invite_email, send_email

router = APIRouter(prefix="/onboarding", tags=["onboarding"])

MAX_INVITES = 5


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
    onboarding = session.get(Onboarding, current_user.id)
    if onboarding is None:
        raise HTTPException(status_code=404, detail="Onboarding not found")
    if not settings.emails_enabled:
        raise HTTPException(status_code=400, detail="Email sending is not enabled")
    if body.email.lower() == current_user.email.lower():
        raise HTTPException(status_code=400, detail="You cannot invite yourself")
    if onboarding.invite_count >= MAX_INVITES:
        raise HTTPException(status_code=429, detail="Invitation limit reached")
    email_data = generate_invite_email()
    send_email(
        email_to=body.email,
        subject=email_data.subject,
        html_content=email_data.html_content,
    )
    crud.mark_invite_sent(session=session, onboarding=onboarding)
    return Message(message="Invitation sent")

from typing import Any

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, SessionDep
from app.models import Onboarding, OnboardingPublic

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


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

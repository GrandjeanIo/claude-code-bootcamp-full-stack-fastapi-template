import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlmodel import Session, col, select

from app.core.security import get_password_hash, verify_password
from app.models import (
    Item,
    ItemCreate,
    Onboarding,
    OnboardingStats,
    User,
    UserCreate,
    UserUpdate,
)


def create_user(*, session: Session, user_create: UserCreate) -> User:
    db_obj = User.model_validate(
        user_create, update={"hashed_password": get_password_hash(user_create.password)}
    )
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def update_user(*, session: Session, db_user: User, user_in: UserUpdate) -> Any:
    user_data = user_in.model_dump(exclude_unset=True)
    extra_data = {}
    if "password" in user_data:
        password = user_data["password"]
        hashed_password = get_password_hash(password)
        extra_data["hashed_password"] = hashed_password
    db_user.sqlmodel_update(user_data, update=extra_data)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


def get_user_by_email(*, session: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    session_user = session.exec(statement).first()
    return session_user


# Dummy hash to use for timing attack prevention when user is not found
# This is an Argon2 hash of a random password, used to ensure constant-time comparison
DUMMY_HASH = "$argon2id$v=19$m=65536,t=3,p=4$MjQyZWE1MzBjYjJlZTI0Yw$YTU4NGM5ZTZmYjE2NzZlZjY0ZWY3ZGRkY2U2OWFjNjk"


def authenticate(*, session: Session, email: str, password: str) -> User | None:
    db_user = get_user_by_email(session=session, email=email)
    if not db_user:
        # Prevent timing attacks by running password verification even when user doesn't exist
        # This ensures the response time is similar whether or not the email exists
        verify_password(password, DUMMY_HASH)
        return None
    verified, updated_password_hash = verify_password(password, db_user.hashed_password)
    if not verified:
        return None
    if updated_password_hash:
        db_user.hashed_password = updated_password_hash
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
    return db_user


def create_onboarding(*, session: Session, user_id: uuid.UUID) -> Onboarding:
    db_obj = Onboarding(user_id=user_id)
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def _mark_step(*, session: Session, user_id: uuid.UUID, step: str) -> None:
    # Users without a row are not onboarding.
    onboarding = session.get(Onboarding, user_id)
    if onboarding is None:
        return
    _set_step(onboarding=onboarding, step=step)
    session.add(onboarding)
    session.commit()


def _set_step(*, onboarding: Onboarding, step: str) -> None:
    # First timestamp wins.
    if getattr(onboarding, step) is not None:
        return
    setattr(onboarding, step, datetime.now(UTC))
    steps = [
        at
        for at in (
            onboarding.first_item_at,
            onboarding.name_edited_at,
            onboarding.invite_sent_at,
        )
        if at is not None
    ]
    if len(steps) == 3:
        onboarding.completed_at = max(steps)


def mark_first_item(*, session: Session, user_id: uuid.UUID) -> None:
    _mark_step(session=session, user_id=user_id, step="first_item_at")


def mark_name_edited(*, session: Session, user_id: uuid.UUID) -> None:
    _mark_step(session=session, user_id=user_id, step="name_edited_at")


def lock_onboarding(*, session: Session, user_id: uuid.UUID) -> Onboarding | None:
    """
    Read a user's onboarding row and lock it until the session's transaction
    ends, so concurrent invites check and increment the count one at a time.
    """
    statement = (
        select(Onboarding).where(Onboarding.user_id == user_id).with_for_update()
    )
    return session.exec(statement).first()


def mark_invite_sent(*, session: Session, onboarding: Onboarding) -> None:
    onboarding.invite_count += 1
    _set_step(onboarding=onboarding, step="invite_sent_at")
    session.add(onboarding)
    session.commit()


def completed_within(
    created_at: datetime, completed_at: datetime | None, days: int = 7
) -> bool:
    if completed_at is None:
        return False
    return completed_at - created_at <= timedelta(days=days)


def get_onboarding_stats(
    *, session: Session, start: datetime, end: datetime
) -> OnboardingStats:
    # Only users with an onboarding row (self-signups) count.
    statement = (
        select(User.created_at, Onboarding.completed_at)
        .join(Onboarding, col(Onboarding.user_id) == col(User.id))
        .where(col(User.created_at) >= start, col(User.created_at) < end)
    )
    rows = session.exec(statement).all()
    registered = len(rows)
    completed = sum(
        1
        for created_at, completed_at in rows
        if created_at is not None and completed_within(created_at, completed_at)
    )
    return OnboardingStats(
        registered=registered,
        completed_within_7d=completed,
        completion_rate=completed / registered if registered else 0,
    )


def create_item(*, session: Session, item_in: ItemCreate, owner_id: uuid.UUID) -> Item:
    db_item = Item.model_validate(item_in, update={"owner_id": owner_id})
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item

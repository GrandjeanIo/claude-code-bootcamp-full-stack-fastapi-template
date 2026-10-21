from datetime import UTC, datetime, timedelta

from sqlmodel import Session

from app import crud
from app.models import Onboarding, UserCreate
from tests.utils.utils import random_email, random_lower_string

REGISTERED = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
LATER = datetime(2999, 1, 1, tzinfo=UTC)


def _new_onboarding(db: Session) -> Onboarding:
    user = crud.create_user(
        session=db,
        user_create=UserCreate(email=random_email(), password=random_lower_string()),
    )
    return crud.create_onboarding(session=db, user_id=user.id)


def _reload(db: Session, onboarding: Onboarding) -> Onboarding:
    db.expire_all()
    row = db.get(Onboarding, onboarding.user_id)
    assert row
    return row


def test_not_completed_while_a_step_is_missing(db: Session) -> None:
    onboarding = _new_onboarding(db)

    crud.mark_first_item(session=db, user_id=onboarding.user_id)
    crud.mark_name_edited(session=db, user_id=onboarding.user_id)

    assert _reload(db, onboarding).completed_at is None


def test_completed_at_is_latest_step_time(db: Session) -> None:
    onboarding = _new_onboarding(db)
    onboarding.invite_sent_at = LATER
    db.add(onboarding)
    db.commit()

    crud.mark_first_item(session=db, user_id=onboarding.user_id)
    assert _reload(db, onboarding).completed_at is None
    crud.mark_name_edited(session=db, user_id=onboarding.user_id)

    assert _reload(db, onboarding).completed_at == LATER


def test_completed_at_is_last_marked_step_when_it_is_latest(db: Session) -> None:
    onboarding = _new_onboarding(db)
    onboarding.invite_sent_at = REGISTERED
    db.add(onboarding)
    db.commit()

    crud.mark_first_item(session=db, user_id=onboarding.user_id)
    crud.mark_name_edited(session=db, user_id=onboarding.user_id)

    row = _reload(db, onboarding)
    assert row.completed_at is not None
    assert row.completed_at == row.name_edited_at


def test_marking_user_without_onboarding_is_a_no_op(db: Session) -> None:
    user = crud.create_user(
        session=db,
        user_create=UserCreate(email=random_email(), password=random_lower_string()),
    )

    crud.mark_first_item(session=db, user_id=user.id)
    crud.mark_name_edited(session=db, user_id=user.id)

    assert db.get(Onboarding, user.id) is None


def test_completed_within_is_true_at_exactly_seven_days() -> None:
    completed = datetime(2026, 1, 8, 12, 0, tzinfo=UTC)
    assert crud.completed_within(REGISTERED, completed) is True


def test_completed_within_is_false_just_after_seven_days() -> None:
    completed = datetime(2026, 1, 8, 12, 0, 0, 1, tzinfo=UTC)
    assert crud.completed_within(REGISTERED, completed) is False


def test_completed_within_is_false_without_completion() -> None:
    assert crud.completed_within(REGISTERED, None) is False


def test_completed_within_honours_custom_days() -> None:
    completed = REGISTERED + timedelta(days=2)
    assert crud.completed_within(REGISTERED, completed, days=1) is False
    assert crud.completed_within(REGISTERED, completed, days=2) is True

from pathlib import Path
from typing import Any

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text
from sqlmodel import Session

from app import crud
from app.core.db import engine
from app.models import UserCreate
from tests.utils.utils import random_email, random_lower_string

BACKEND_DIR = Path(__file__).resolve().parents[1]
REVISION_BEFORE_ONBOARDING = "fe56fa70289e"


def _alembic_config() -> Config:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "app" / "alembic"))
    return config


def _user_table_snapshot() -> tuple[list[dict[str, Any]], list[tuple[Any, ...]]]:
    with engine.connect() as conn:
        columns = inspect(conn).get_columns("user")
        rows = conn.execute(text('SELECT * FROM "user" ORDER BY id')).all()
    return [
        {"name": c["name"], "type": str(c["type"]), "nullable": c["nullable"]}
        for c in columns
    ], [tuple(r) for r in rows]


def _has_onboarding_table() -> bool:
    with engine.connect() as conn:
        return inspect(conn).has_table("onboarding")


def test_onboarding_migration_round_trip_keeps_user_table(db: Session) -> None:
    user = crud.create_user(
        session=db,
        user_create=UserCreate(email=random_email(), password=random_lower_string()),
    )
    crud.create_onboarding(session=db, user_id=user.id)
    # Release the session's locks so the migration can drop and create tables.
    db.commit()
    config = _alembic_config()
    before = _user_table_snapshot()
    assert _has_onboarding_table()

    command.downgrade(config, REVISION_BEFORE_ONBOARDING)
    assert not _has_onboarding_table()
    assert _user_table_snapshot() == before

    command.upgrade(config, "head")
    assert _has_onboarding_table()
    assert _user_table_snapshot() == before

import logging
import threading
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import patch

import pytest
from emails.backend.response import SMTPResponse
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, select

from app import crud
from app.core.config import settings
from app.core.db import engine
from app.models import Onboarding, User, UserCreate
from tests.utils.utils import random_email, random_lower_string


def _onboarding_rows(db: Session, user_id: object) -> list[Onboarding]:
    db.expire_all()
    return list(db.exec(select(Onboarding).where(Onboarding.user_id == user_id)))


def test_signup_creates_onboarding_with_no_steps(
    client: TestClient, db: Session
) -> None:
    email = random_email()
    r = client.post(
        f"{settings.API_V1_STR}/users/signup",
        json={"email": email, "password": random_lower_string()},
    )
    assert r.status_code == 200

    rows = _onboarding_rows(db, r.json()["id"])
    assert len(rows) == 1
    onboarding = rows[0]
    assert onboarding.first_item_at is None
    assert onboarding.name_edited_at is None
    assert onboarding.invite_sent_at is None
    assert onboarding.invite_count == 0
    assert onboarding.completed_at is None


def test_admin_created_user_has_no_onboarding(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    r = client.post(
        f"{settings.API_V1_STR}/users/",
        headers=superuser_token_headers,
        json={"email": random_email(), "password": random_lower_string()},
    )
    assert r.status_code == 200

    assert _onboarding_rows(db, r.json()["id"]) == []


def test_initial_superuser_has_no_onboarding(db: Session) -> None:
    superuser = crud.get_user_by_email(session=db, email=settings.FIRST_SUPERUSER)
    assert superuser

    assert _onboarding_rows(db, superuser.id) == []


def _signup_and_login(
    client: TestClient, email: str | None = None
) -> tuple[str, dict[str, str]]:
    email = email or random_email()
    password = random_lower_string()
    r = client.post(
        f"{settings.API_V1_STR}/users/signup",
        json={"email": email, "password": password},
    )
    user_id = r.json()["id"]
    r = client.post(
        f"{settings.API_V1_STR}/login/access-token",
        data={"username": email, "password": password},
    )
    return user_id, {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_deleting_own_user_removes_onboarding(client: TestClient, db: Session) -> None:
    user_id, headers = _signup_and_login(client)
    assert len(_onboarding_rows(db, user_id)) == 1

    r = client.delete(f"{settings.API_V1_STR}/users/me", headers=headers)
    assert r.status_code == 200

    assert _onboarding_rows(db, user_id) == []


def test_admin_deleting_user_removes_onboarding(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    user_id, _ = _signup_and_login(client)
    assert len(_onboarding_rows(db, user_id)) == 1

    r = client.delete(
        f"{settings.API_V1_STR}/users/{user_id}", headers=superuser_token_headers
    )
    assert r.status_code == 200

    assert _onboarding_rows(db, user_id) == []


def _create_item(client: TestClient, headers: dict[str, str]) -> str:
    r = client.post(
        f"{settings.API_V1_STR}/items/",
        headers=headers,
        json={"title": random_lower_string()},
    )
    assert r.status_code == 200
    return str(r.json()["id"])


def test_creating_item_marks_first_item_once(client: TestClient, db: Session) -> None:
    user_id, headers = _signup_and_login(client)

    _create_item(client, headers)
    first_item_at = _onboarding_rows(db, user_id)[0].first_item_at
    assert first_item_at is not None

    _create_item(client, headers)
    assert _onboarding_rows(db, user_id)[0].first_item_at == first_item_at


def test_deleting_item_keeps_first_item_step(client: TestClient, db: Session) -> None:
    user_id, headers = _signup_and_login(client)
    item_id = _create_item(client, headers)
    first_item_at = _onboarding_rows(db, user_id)[0].first_item_at
    assert first_item_at is not None

    r = client.delete(f"{settings.API_V1_STR}/items/{item_id}", headers=headers)
    assert r.status_code == 200

    assert _onboarding_rows(db, user_id)[0].first_item_at == first_item_at


def test_user_without_onboarding_can_create_item_and_edit_name(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    r = client.post(
        f"{settings.API_V1_STR}/items/",
        headers=normal_user_token_headers,
        json={"title": "Foo", "description": "Bar"},
    )
    assert r.status_code == 200
    assert r.json()["title"] == "Foo"
    assert r.json()["description"] == "Bar"

    r = client.patch(
        f"{settings.API_V1_STR}/users/me",
        headers=normal_user_token_headers,
        json={"full_name": random_lower_string()[:20]},
    )
    assert r.status_code == 200
    full_name = r.json()["full_name"]
    r = client.get(f"{settings.API_V1_STR}/users/me", headers=normal_user_token_headers)
    assert r.json()["full_name"] == full_name


def _patch_me(
    client: TestClient, headers: dict[str, str], body: dict[str, str]
) -> None:
    r = client.patch(f"{settings.API_V1_STR}/users/me", headers=headers, json=body)
    assert r.status_code == 200


def test_changing_name_marks_name_edited(client: TestClient, db: Session) -> None:
    user_id, headers = _signup_and_login(client)

    _patch_me(client, headers, {"full_name": "Ada Lovelace"})

    assert _onboarding_rows(db, user_id)[0].name_edited_at is not None


def test_reverting_name_keeps_name_edited(client: TestClient, db: Session) -> None:
    user_id, headers = _signup_and_login(client)
    _patch_me(client, headers, {"full_name": "Ada Lovelace"})
    name_edited_at = _onboarding_rows(db, user_id)[0].name_edited_at
    assert name_edited_at is not None

    _patch_me(client, headers, {"full_name": "Grace Hopper"})
    _patch_me(client, headers, {"full_name": ""})

    assert _onboarding_rows(db, user_id)[0].name_edited_at == name_edited_at


def test_empty_name_does_not_mark_name_edited(client: TestClient, db: Session) -> None:
    user_id, headers = _signup_and_login(client)

    _patch_me(client, headers, {"full_name": ""})

    assert _onboarding_rows(db, user_id)[0].name_edited_at is None


def test_update_without_name_does_not_mark_name_edited(
    client: TestClient, db: Session
) -> None:
    user_id, headers = _signup_and_login(client)

    _patch_me(client, headers, {"email": random_email()})

    assert _onboarding_rows(db, user_id)[0].name_edited_at is None


def test_saving_same_name_does_not_mark_name_edited(
    client: TestClient, db: Session
) -> None:
    email = random_email()
    password = random_lower_string()
    r = client.post(
        f"{settings.API_V1_STR}/users/signup",
        json={"email": email, "password": password, "full_name": "Ada Lovelace"},
    )
    user_id = r.json()["id"]
    r = client.post(
        f"{settings.API_V1_STR}/login/access-token",
        data={"username": email, "password": password},
    )
    headers = {"Authorization": f"Bearer {r.json()['access_token']}"}

    _patch_me(client, headers, {"full_name": "Ada Lovelace"})

    assert _onboarding_rows(db, user_id)[0].name_edited_at is None


def _get_onboarding_me(client: TestClient, headers: dict[str, str]) -> Any:
    return client.get(f"{settings.API_V1_STR}/onboarding/me", headers=headers)


def test_onboarding_me_for_fresh_signup_has_no_steps_done(client: TestClient) -> None:
    _, headers = _signup_and_login(client)

    r = _get_onboarding_me(client, headers)

    assert r.status_code == 200
    assert r.json() == {
        "first_item": False,
        "name_edited": False,
        "invite_sent": False,
        "completed": False,
    }


def test_onboarding_me_shows_item_and_name_steps(client: TestClient) -> None:
    _, headers = _signup_and_login(client)
    _create_item(client, headers)
    _patch_me(client, headers, {"full_name": "Ada Lovelace"})

    r = _get_onboarding_me(client, headers)

    assert r.status_code == 200
    assert r.json() == {
        "first_item": True,
        "name_edited": True,
        "invite_sent": False,
        "completed": False,
    }


def test_onboarding_me_is_completed_when_all_steps_done(
    client: TestClient, db: Session
) -> None:
    user_id, headers = _signup_and_login(client)
    # No invite route yet: record the invite step directly.
    onboarding = _onboarding_rows(db, user_id)[0]
    onboarding.invite_sent_at = datetime.now(UTC)
    db.add(onboarding)
    db.commit()
    _create_item(client, headers)
    _patch_me(client, headers, {"full_name": "Ada Lovelace"})

    r = _get_onboarding_me(client, headers)

    assert r.status_code == 200
    assert r.json() == {
        "first_item": True,
        "name_edited": True,
        "invite_sent": True,
        "completed": True,
    }


def test_onboarding_me_without_record_is_not_found(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    r = _get_onboarding_me(client, normal_user_token_headers)

    assert r.status_code == 404
    assert r.json() == {"detail": "Onboarding not found"}


def test_onboarding_me_requires_authentication(client: TestClient) -> None:
    r = client.get(f"{settings.API_V1_STR}/onboarding/me")

    assert r.status_code in (401, 403)


def _invite(client: TestClient, headers: dict[str, str], email: str) -> Any:
    return client.post(
        f"{settings.API_V1_STR}/onboarding/invite",
        headers=headers,
        json={"email": email},
    )


def test_invite_sends_signup_link_and_marks_invite_sent(
    client: TestClient, db: Session
) -> None:
    user_id, headers = _signup_and_login(client)
    invitee = random_email()

    with patch("app.api.routes.onboarding.send_invite_email") as send_email:
        r = _invite(client, headers, invitee)

    assert r.status_code == 200
    send_email.assert_called_once()
    assert send_email.call_args.kwargs["email_to"] == invitee
    assert (
        f"{settings.FRONTEND_HOST}/signup"
        in send_email.call_args.kwargs["html_content"]
    )
    assert _get_onboarding_me(client, headers).json()["invite_sent"] is True
    assert _onboarding_rows(db, user_id)[0].invite_count == 1


def test_invite_is_refused_when_emails_disabled(client: TestClient) -> None:
    _, headers = _signup_and_login(client)

    with (
        patch("app.core.config.settings.SMTP_HOST", None),
        patch("app.api.routes.onboarding.send_invite_email") as send_email,
    ):
        r = _invite(client, headers, random_email())

    assert r.status_code == 400
    send_email.assert_not_called()


def test_invite_to_own_address_is_refused_ignoring_case(client: TestClient) -> None:
    own_email = random_email()
    _, headers = _signup_and_login(client, own_email)

    with patch("app.api.routes.onboarding.send_invite_email") as send_email:
        r = _invite(client, headers, own_email.upper())

    assert r.status_code == 400
    send_email.assert_not_called()


def test_sixth_invite_is_rate_limited(client: TestClient) -> None:
    _, headers = _signup_and_login(client)
    with patch("app.api.routes.onboarding.send_invite_email"):
        for _ in range(5):
            assert _invite(client, headers, random_email()).status_code == 200

    with patch("app.api.routes.onboarding.send_invite_email") as send_email:
        r = _invite(client, headers, random_email())

    assert r.status_code == 429
    send_email.assert_not_called()


def test_invite_waits_for_concurrent_invite_on_same_user(
    client: TestClient, db: Session
) -> None:
    user_id, headers = _signup_and_login(client)
    with patch("app.api.routes.onboarding.send_invite_email", return_value=True):
        for _ in range(4):
            assert _invite(client, headers, random_email()).status_code == 200

    # Another transaction holds the user's onboarding row, as a concurrent
    # invite would between its cap check and its increment, and spends the
    # last send.
    with Session(engine) as other:
        held = other.exec(
            select(Onboarding).where(Onboarding.user_id == user_id).with_for_update()
        ).one()
        result: dict[str, Any] = {}
        with patch(
            "app.api.routes.onboarding.send_invite_email", return_value=True
        ) as send:
            request = threading.Thread(
                target=lambda: result.update(
                    response=_invite(client, headers, random_email())
                )
            )
            request.start()
            request.join(timeout=1)
            blocked = request.is_alive()
            held.invite_count += 1
            other.add(held)
            other.commit()
            request.join(timeout=5)

    assert blocked
    assert result["response"].status_code == 429
    send.assert_not_called()
    assert _onboarding_rows(db, user_id)[0].invite_count == 5


def _smtp_response(code: int, text: str) -> SMTPResponse:
    response = SMTPResponse()
    response.set_status("data", code, text.encode())
    return response


def test_failed_send_leaves_invite_step_and_count_unchanged(
    client: TestClient, db: Session
) -> None:
    user_id, headers = _signup_and_login(client)
    invitee = random_email()

    with patch(
        "emails.message.Message.send",
        return_value=_smtp_response(550, "Mailbox unavailable"),
    ):
        r = _invite(client, headers, invitee)

    assert r.status_code == 502
    assert invitee not in r.text
    onboarding = _onboarding_rows(db, user_id)[0]
    assert onboarding.invite_sent_at is None
    assert onboarding.invite_count == 0


@pytest.mark.parametrize(
    ("smtp_code", "reply", "expected_status"),
    [
        (250, "2.0.0 Ok: queued for <{invitee}>", 200),
        (550, "<{invitee}>: Recipient address rejected", 502),
    ],
)
def test_invited_address_is_not_stored_or_logged(
    client: TestClient,
    db: Session,
    caplog: pytest.LogCaptureFixture,
    smtp_code: int,
    reply: str,
    expected_status: int,
) -> None:
    _, headers = _signup_and_login(client)
    invitee = random_email()

    # Patch below the app's email helpers so their own log lines run, with a
    # server reply that echoes the address.
    with (
        patch(
            "emails.message.Message.send",
            return_value=_smtp_response(smtp_code, reply.format(invitee=invitee)),
        ) as smtp_send,
        caplog.at_level(logging.DEBUG),
    ):
        r = _invite(client, headers, invitee)

    assert r.status_code == expected_status
    assert smtp_send.call_args.kwargs["to"] == invitee
    assert str(smtp_code) in caplog.text
    assert invitee not in caplog.text
    db.expire_all()
    for table in SQLModel.metadata.sorted_tables:
        for row in db.exec(select(table)).all():  # type: ignore[call-overload]
            assert invitee not in str(row)


def test_invite_to_registered_address_gets_same_response(
    client: TestClient,
) -> None:
    registered_email = random_email()
    _signup_and_login(client, registered_email)
    _, headers = _signup_and_login(client)

    with patch("app.api.routes.onboarding.send_invite_email") as send_email:
        to_unknown = _invite(client, headers, random_email())
        to_registered = _invite(client, headers, registered_email)

    assert to_registered.status_code == to_unknown.status_code == 200
    assert to_registered.json() == to_unknown.json()
    assert send_email.call_count == 2


def test_invite_without_onboarding_record_is_not_found(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    with patch("app.api.routes.onboarding.send_invite_email") as send_email:
        r = _invite(client, normal_user_token_headers, random_email())

    assert r.status_code == 404
    assert r.json() == {"detail": "Onboarding not found"}
    send_email.assert_not_called()


def test_invite_requires_authentication(client: TestClient) -> None:
    with patch("app.api.routes.onboarding.send_invite_email") as send_email:
        r = client.post(
            f"{settings.API_V1_STR}/onboarding/invite",
            json={"email": random_email()},
        )

    assert r.status_code in (401, 403)
    send_email.assert_not_called()


def _stats(
    client: TestClient, headers: dict[str, str], **params: str
) -> dict[str, Any]:
    r = client.get(
        f"{settings.API_V1_STR}/onboarding/stats", headers=headers, params=params
    )
    assert r.status_code == 200
    return r.json()  # type: ignore[no-any-return]


def test_stats_default_window_counts_recent_signups(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    before = _stats(client, superuser_token_headers)
    _signup_and_login(client)
    after = _stats(client, superuser_token_headers)

    assert set(after) == {"registered", "completed_within_7d", "completion_rate"}
    assert after["registered"] == before["registered"] + 1


def test_stats_refused_for_normal_user(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    r = client.get(
        f"{settings.API_V1_STR}/onboarding/stats", headers=normal_user_token_headers
    )
    assert r.status_code == 403


def test_stats_requires_authentication(client: TestClient) -> None:
    r = client.get(f"{settings.API_V1_STR}/onboarding/stats")
    assert r.status_code == 401


def _registered_at(
    client: TestClient,
    db: Session,
    created_at: datetime,
    completed_at: datetime | None = None,
) -> None:
    """Sign up a user, then backdate registration and set step times."""
    user_id, _ = _signup_and_login(client)
    onboarding = _onboarding_rows(db, user_id)[0]
    user = db.get(User, onboarding.user_id)
    assert user
    user.created_at = created_at
    db.add(user)
    onboarding.first_item_at = created_at
    onboarding.name_edited_at = created_at
    # Without completed_at the invite step is left undone.
    onboarding.invite_sent_at = completed_at
    onboarding.completed_at = completed_at
    db.add(onboarding)
    db.commit()


def _window(year: int) -> dict[str, str]:
    return {
        "start": datetime(year, 1, 1, tzinfo=UTC).isoformat(),
        "end": datetime(year, 2, 1, tzinfo=UTC).isoformat(),
    }


def test_stats_window_includes_start_and_excludes_end(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    _registered_at(client, db, datetime(2001, 1, 1, tzinfo=UTC))
    _registered_at(client, db, datetime(2001, 2, 1, tzinfo=UTC))

    stats = _stats(client, superuser_token_headers, **_window(2001))

    assert stats["registered"] == 1


def test_stats_counts_completion_up_to_exactly_seven_days(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    registered = datetime(2002, 1, 10, 12, 0, tzinfo=UTC)
    _registered_at(client, db, registered, registered + timedelta(days=7))
    _registered_at(
        client, db, registered, registered + timedelta(days=7, microseconds=1)
    )

    stats = _stats(client, superuser_token_headers, **_window(2002))

    assert stats == {
        "registered": 2,
        "completed_within_7d": 1,
        "completion_rate": 0.5,
    }


def test_stats_does_not_count_incomplete_onboarding(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    _registered_at(client, db, datetime(2003, 1, 10, tzinfo=UTC))

    stats = _stats(client, superuser_token_headers, **_window(2003))

    assert stats == {
        "registered": 1,
        "completed_within_7d": 0,
        "completion_rate": 0,
    }


def test_stats_rate_is_zero_when_nobody_registered(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    stats = _stats(client, superuser_token_headers, **_window(1990))

    assert stats == {
        "registered": 0,
        "completed_within_7d": 0,
        "completion_rate": 0,
    }


def test_stats_excludes_users_without_onboarding_record(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    user = crud.create_user(
        session=db,
        user_create=UserCreate(email=random_email(), password=random_lower_string()),
    )
    user.created_at = datetime(2004, 1, 10, tzinfo=UTC)
    db.add(user)
    db.commit()

    stats = _stats(client, superuser_token_headers, **_window(2004))

    assert stats["registered"] == 0

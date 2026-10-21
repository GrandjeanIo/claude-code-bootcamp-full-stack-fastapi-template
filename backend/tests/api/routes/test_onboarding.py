from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app import crud
from app.core.config import settings
from app.models import Onboarding
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


def _signup_and_login(client: TestClient) -> tuple[str, dict[str, str]]:
    email = random_email()
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

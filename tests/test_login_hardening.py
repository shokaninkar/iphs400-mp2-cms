"""MP2plus S2: login hardening.

1. A wrong password and an unknown email get the same answer, so the login
   form cannot be used to learn which emails have accounts.
2. Guessing is slowed: after 5 failed logins for one email within 15 minutes,
   further attempts for that email are refused (429), even with the right
   password. The limiter is keyed on the account, not the client.

The limiter's clock is frozen through `frozen_clock`; the limiter itself is
reset between tests by the autouse `reset_login_limiter` fixture in conftest.
"""
from __future__ import annotations

import re

import pytest

from app.ratelimit import login_limiter

ADMIN = {"email": "admin@example.test", "password": "test-admin-pw"}
EDITOR = {"email": "editor@example.test", "password": "test-editor-pw"}


class FrozenClock:
    def __init__(self, start: float = 1_000_000.0):
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


@pytest.fixture
def frozen_clock(monkeypatch):
    clock = FrozenClock()
    monkeypatch.setattr(login_limiter, "clock", clock)
    return clock


def _login(client, email, password):
    return client.post("/login", data={"email": email, "password": password},
                       follow_redirects=False)


def _error_text(response) -> str:
    match = re.search(r'class="[^"]*error[^"]*"[^>]*>(.*?)<', response.text, re.S)
    return match.group(1).strip() if match else response.text


def _fail_five_times(client, email=ADMIN["email"]):
    for _ in range(5):
        assert _login(client, email, "wrong-password").status_code == 200


def test_wrong_password_and_unknown_email_give_identical_responses(client):
    wrong_password = _login(client, ADMIN["email"], "not-the-password")
    unknown_email = _login(client, "nobody@example.test", "not-the-password")

    assert wrong_password.status_code == unknown_email.status_code
    assert _error_text(wrong_password) == _error_text(unknown_email)
    assert wrong_password.text == unknown_email.text


def test_sixth_attempt_is_refused_even_with_the_right_password(client, frozen_clock):
    _fail_five_times(client)

    response = _login(client, ADMIN["email"], ADMIN["password"])

    assert response.status_code == 429
    assert "too many" in response.text.lower()
    assert "cms_session" not in response.cookies


def test_login_works_again_once_15_minutes_have_passed(client, frozen_clock):
    _fail_five_times(client)
    frozen_clock.advance(14 * 60 + 59)
    assert _login(client, ADMIN["email"], ADMIN["password"]).status_code == 429

    frozen_clock.advance(1)
    response = _login(client, ADMIN["email"], ADMIN["password"])

    assert response.status_code == 303
    assert "cms_session" in response.cookies


def test_lockout_of_one_email_does_not_block_another_email(client, frozen_clock):
    _fail_five_times(client, ADMIN["email"])

    response = _login(client, EDITOR["email"], EDITOR["password"])

    assert response.status_code == 303
    assert "cms_session" in response.cookies


def test_email_case_does_not_dodge_the_limit(client, frozen_clock):
    _fail_five_times(client)

    response = _login(client, ADMIN["email"].upper(), ADMIN["password"])

    assert response.status_code == 429


def test_four_failures_then_a_correct_login_succeeds(client, frozen_clock):
    for _ in range(4):
        _login(client, ADMIN["email"], "wrong-password")

    assert _login(client, ADMIN["email"], ADMIN["password"]).status_code == 303

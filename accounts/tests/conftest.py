# accounts/tests/conftest.py
import pytest
from accounts.models import CustomUser
from budget.models import Person


@pytest.fixture
def user():
    return CustomUser.objects.create_user(
        email="testuser@example.com", password="password123"
    )


@pytest.fixture
def person(user):
    return Person.objects.create(user=user, bio="Sample bio")

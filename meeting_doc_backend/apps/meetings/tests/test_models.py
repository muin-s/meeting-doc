import pytest
from apps.meetings.models import Meeting


@pytest.mark.django_db
class TestMeetingModel:
    def test_str(self):
        obj = Meeting(name="Test")
        assert str(obj) == "Test"

    def test_create(self):
        obj = Meeting.objects.create(name="Test Meeting")
        assert obj.id is not None
        assert obj.is_active is True

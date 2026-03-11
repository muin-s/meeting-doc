import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestMeetingAPI:
    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@example.com", password="testpass123"
        )
        self.client.force_authenticate(user=self.user)

    def test_list(self):
        url = reverse("meeting-list")
        response = self.client.get(url)
        assert response.status_code == 200

    def test_create(self):
        url = reverse("meeting-list")
        data = {"name": "New Meeting"}
        response = self.client.post(url, data)
        assert response.status_code == 201
        assert response.data["name"] == "New Meeting"

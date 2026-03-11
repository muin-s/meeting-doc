from rest_framework.routers import DefaultRouter
from apps.meetings.views import (
    MeetingViewSet,
    ParticipantViewSet,
    TranscriptViewSet,
    ActionItemViewSet,
)

router = DefaultRouter()
router.register(r"meetings", MeetingViewSet, basename="meeting")
router.register(r"participants", ParticipantViewSet, basename="participant")
router.register(r"transcripts", TranscriptViewSet, basename="transcript")
router.register(r"action-items", ActionItemViewSet, basename="action-item")

urlpatterns = router.urls

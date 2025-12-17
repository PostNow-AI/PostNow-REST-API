import uuid

from rest_framework import generics, permissions, status
from rest_framework.response import Response

from .serializers import AnalyticsEventCreateSerializer


class AnalyticsEventCreateView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AnalyticsEventCreateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        # Se o client não mandou request_id, geramos aqui para correlação.
        if not serializer.validated_data.get("request_id"):
            serializer.validated_data["request_id"] = uuid.uuid4()

        event = serializer.save()

        return Response(
            {"status": "success", "event_id": str(event.id), "request_id": str(event.request_id)},
            status=status.HTTP_201_CREATED,
        )


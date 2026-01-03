from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly


class BaseReadOnlyViewSet(viewsets.ReadOnlyModelViewSet):
    """Viewset for reading ingredients and tags."""

    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = None

from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import View


class IsAuthenticatedOrReadOnlyOrCreateUser(
    permissions.IsAuthenticatedOrReadOnly
):
    """Extends permissions to allow anonymous users to register."""

    def has_permission(
            self,
            request: Request,
            view: View) -> bool:
        """Checks if the user is authenticated or if it's a sign-up request.

        Args:
            request (Request): The incoming request.
            view (View): The view handling the request.

        Returns:
            bool: True if the user is authenticated, it's a safe method,
            or it's a POST request.
        """

        return (super().has_permission(request, view)
                or request.method == 'POST')

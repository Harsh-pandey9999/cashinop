from django.core.exceptions import PermissionDenied
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import AnonymousUser
from django.utils.translation import gettext_lazy as _
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class SecurityMiddleware(MiddlewareMixin):
    """
    Middleware to enforce security policies and data isolation.
    """
    def process_request(self, request):
        # Skip for static/media files
        if request.path.startswith(('/static/', '/media/')):
            return None

        # Skip for admin login
        if request.path.startswith('/admin/login/'):
            return None

        # Enforce HTTPS
        if not request.is_secure() and not settings.DEBUG:
            raise PermissionDenied(_("HTTPS is required for this application."))

        # Add security headers
        request.META['HTTP_X_FRAME_OPTIONS'] = 'DENY'
        request.META['HTTP_X_CONTENT_TYPE_OPTIONS'] = 'nosniff'
        request.META['HTTP_X_XSS_PROTECTION'] = '1; mode=block'
        
        # Set secure cookie flags
        if not settings.DEBUG:
            request.session.set_expiry(settings.SESSION_COOKIE_AGE)
            request.session.set_cookie(
                'sessionid',
                request.session.session_key,
                secure=True,
                httponly=True,
                samesite='Lax'
            )

        return None

class DataIsolationMiddleware(MiddlewareMixin):
    """
    Middleware to enforce data isolation between users.
    """
    def process_view(self, request, view_func, view_args, view_kwargs):
        # Skip for static/media files and admin login
        if request.path.startswith(('/static/', '/media/', '/admin/login/')):
            return None

        # Skip for anonymous users
        if isinstance(request.user, AnonymousUser):
            return None

        # Skip for superusers
        if request.user.is_superuser:
            return None

        # Get the model from the view if available
        model = getattr(view_func, 'model', None)
        if not model:
            return None

        # Check if the view has data isolation disabled
        if getattr(view_func, 'disable_data_isolation', False):
            return None

        # Get the queryset
        queryset = getattr(view_func, 'queryset', None)
        if not queryset:
            return None

        # Apply data isolation filters
        try:
            if hasattr(model, 'get_owner'):
                # Filter by owner
                owner_field = model.get_owner()
                queryset = queryset.filter(**{owner_field: request.user})
            elif hasattr(model, 'created_by'):
                # Filter by creator
                queryset = queryset.filter(created_by=request.user)
            elif hasattr(model, 'author'):
                # Filter by author
                queryset = queryset.filter(author=request.user)
            elif hasattr(model, 'user'):
                # Filter by user
                queryset = queryset.filter(user=request.user)

            # Update the view's queryset
            view_func.queryset = queryset

        except Exception as e:
            logger.error(f"Data isolation error: {str(e)}")
            raise PermissionDenied(_("Access denied due to data isolation policy."))

        return None

class AuditLogMiddleware(MiddlewareMixin):
    """
    Middleware to log security-relevant events.
    """
    def process_request(self, request):
        # Skip for static/media files
        if request.path.startswith(('/static/', '/media/')):
            return None

        # Log request information
        if not isinstance(request.user, AnonymousUser):
            logger.info(
                f"Request: {request.method} {request.path} - "
                f"User: {request.user.username} - "
                f"IP: {request.META.get('REMOTE_ADDR')} - "
                f"User-Agent: {request.META.get('HTTP_USER_AGENT')}"
            )

        return None

    def process_response(self, request, response):
        # Skip for static/media files
        if request.path.startswith(('/static/', '/media/')):
            return response

        # Log response information for security-relevant status codes
        if response.status_code in (401, 403, 404, 500):
            logger.warning(
                f"Response: {response.status_code} - "
                f"Path: {request.path} - "
                f"Method: {request.method} - "
                f"User: {request.user.username if not isinstance(request.user, AnonymousUser) else 'Anonymous'} - "
                f"IP: {request.META.get('REMOTE_ADDR')}"
            )

        return response

class RoleBasedAccessMiddleware(MiddlewareMixin):
    """
    Middleware to enforce role-based access control.
    """
    def process_view(self, request, view_func, view_args, view_kwargs):
        # Skip for static/media files and admin login
        if request.path.startswith(('/static/', '/media/', '/admin/login/')):
            return None

        # Skip for anonymous users
        if isinstance(request.user, AnonymousUser):
            return None

        # Skip for superusers
        if request.user.is_superuser:
            return None

        # Get required roles from view
        required_roles = getattr(view_func, 'required_roles', None)
        if not required_roles:
            return None

        # Check if user has any of the required roles
        user_roles = set(request.user.groups.values_list('name', flat=True))
        if not any(role in user_roles for role in required_roles):
            logger.warning(
                f"Role-based access denied: User {request.user.username} "
                f"attempted to access {request.path} "
                f"but required roles {required_roles} not found in {user_roles}"
            )
            raise PermissionDenied(_("You do not have the required role to access this resource."))

        return None 
from rest_framework import permissions
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _
from .utils import get_client_ip, log_security_event
from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner
        if hasattr(obj, 'get_owner'):
            return obj.get_owner() == request.user
        elif hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        elif hasattr(obj, 'author'):
            return obj.author == request.user
        elif hasattr(obj, 'user'):
            return obj.user == request.user

        return False

class IsApprovedUser(permissions.BasePermission):
    """
    Custom permission to only allow approved users to access the view.
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if not hasattr(request.user, 'casino_profile'):
            log_security_event(
                'permission_denied',
                request.user,
                get_client_ip(request),
                {'reason': 'no_casino_profile'},
                level='warning'
            )
            return False

        if not request.user.casino_profile.is_approved:
            log_security_event(
                'permission_denied',
                request.user,
                get_client_ip(request),
                {'reason': 'not_approved'},
                level='warning'
            )
            return False

        return True

class HasRole(permissions.BasePermission):
    """
    Custom permission to only allow users with specific roles to access the view.
    """
    def __init__(self, roles):
        self.roles = roles if isinstance(roles, (list, tuple)) else [roles]

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        user_roles = set(request.user.groups.values_list('name', flat=True))
        has_role = any(role in user_roles for role in self.roles)

        if not has_role:
            log_security_event(
                'role_violation',
                request.user,
                get_client_ip(request),
                {
                    'required_roles': self.roles,
                    'user_roles': list(user_roles)
                },
                level='warning'
            )

        return has_role

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow admins to edit objects.
    """
    def has_permission(self, request, view):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to admins
        return request.user.is_staff or request.user.is_superuser

class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow owners or admins to access objects.
    """
    def has_object_permission(self, request, view, obj):
        # Admins can do anything
        if request.user.is_staff or request.user.is_superuser:
            return True

        # Check if user is the owner
        if hasattr(obj, 'get_owner'):
            return obj.get_owner() == request.user
        elif hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        elif hasattr(obj, 'author'):
            return obj.author == request.user
        elif hasattr(obj, 'user'):
            return obj.user == request.user

        return False

class HasPermission(permissions.BasePermission):
    """
    Custom permission to check for specific model permissions.
    """
    def __init__(self, permission):
        self.permission = permission

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        has_perm = request.user.has_perm(self.permission)
        
        if not has_perm:
            log_security_event(
                'permission_denied',
                request.user,
                get_client_ip(request),
                {'required_permission': self.permission},
                level='warning'
            )

        return has_perm

class IsVerifiedUser(permissions.BasePermission):
    """
    Custom permission to only allow verified users to access the view.
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if not request.user.is_active:
            log_security_event(
                'permission_denied',
                request.user,
                get_client_ip(request),
                {'reason': 'account_inactive'},
                level='warning'
            )
            return False

        if hasattr(request.user, 'casino_profile'):
            if not request.user.casino_profile.is_approved:
                log_security_event(
                    'permission_denied',
                    request.user,
                    get_client_ip(request),
                    {'reason': 'not_approved'},
                    level='warning'
                )
                return False

        return True

class IsNotLocked(permissions.BasePermission):
    """
    Custom permission to check if user is not locked out.
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if hasattr(request.user, 'casino_profile'):
            profile = request.user.casino_profile
            if profile.failed_login_attempts >= settings.CASINO_SETTINGS['MAX_LOGIN_ATTEMPTS']:
                lockout_time = profile.last_failed_login + timedelta(seconds=settings.CASINO_SETTINGS['LOGIN_TIMEOUT'])
                if timezone.now() < lockout_time:
                    log_security_event(
                        'permission_denied',
                        request.user,
                        get_client_ip(request),
                        {
                            'reason': 'account_locked',
                            'attempts': profile.failed_login_attempts,
                            'lockout_until': lockout_time.isoformat()
                        },
                        level='warning'
                    )
                    return False

        return True

def get_permission_classes(view_type):
    """
    Get the appropriate permission classes for a view type.
    """
    permission_classes = {
        'list': [IsVerifiedUser, IsNotLocked],
        'create': [IsVerifiedUser, IsNotLocked],
        'retrieve': [IsVerifiedUser, IsNotLocked, IsOwnerOrAdmin],
        'update': [IsVerifiedUser, IsNotLocked, IsOwnerOrAdmin],
        'partial_update': [IsVerifiedUser, IsNotLocked, IsOwnerOrAdmin],
        'destroy': [IsVerifiedUser, IsNotLocked, IsOwnerOrAdmin],
        'admin': [IsAdminOrReadOnly],
        'public': [permissions.AllowAny],
        'authenticated': [permissions.IsAuthenticated],
    }
    return permission_classes.get(view_type, [permissions.IsAuthenticated]) 
from django.contrib.auth.mixins import PermissionRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.utils import timezone
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

class ObjectLevelPermissionMixin(UserPassesTestMixin):
    """
    Mixin to enforce object-level permissions.
    Requires the model to have a user field or a method to determine ownership.
    """
    def get_object_owner(self, obj):
        """
        Override this method to specify how to get the owner of an object.
        Default implementation looks for a 'user' field.
        """
        if hasattr(obj, 'user'):
            return obj.user
        elif hasattr(obj, 'get_owner'):
            return obj.get_owner()
        return None

    def test_func(self):
        """
        Test if the user has permission to access the object.
        """
        obj = self.get_object()
        if not obj:
            return False

        # Superusers can access everything
        if self.request.user.is_superuser:
            return True

        # Get the object owner
        owner = self.get_object_owner(obj)
        if not owner:
            return False

        # Check if user is the owner
        if owner == self.request.user:
            return True

        # Check for specific permissions
        if hasattr(self, 'required_permissions'):
            return self.request.user.has_perms(self.required_permissions, obj)

        return False

class RoleBasedAccessMixin(PermissionRequiredMixin):
    """
    Mixin to enforce role-based access control.
    Extends Django's PermissionRequiredMixin with role-based checks.
    """
    role_required = None
    roles = {
        'admin': ['admin'],
        'manager': ['admin', 'manager'],
        'staff': ['admin', 'manager', 'staff'],
        'user': ['admin', 'manager', 'staff', 'user'],
    }

    def get_role_required(self):
        """
        Override this method to override the role_required attribute.
        Must return a string or iterable of roles.
        """
        if self.role_required is None:
            raise ImproperlyConfigured(
                f"{self.__class__.__name__} is missing the "
                f"role_required attribute. Define "
                f"{self.__class__.__name__}.role_required, or override "
                f"{self.__class__.__name__}.get_role_required()."
            )
        if isinstance(self.role_required, str):
            roles = (self.role_required,)
        else:
            roles = self.role_required
        return roles

    def has_role(self):
        """
        Check if the user has the required role.
        """
        if self.request.user.is_superuser:
            return True

        required_roles = self.get_role_required()
        user_groups = set(self.request.user.groups.values_list('name', flat=True))

        for role in required_roles:
            if role in self.roles:
                if any(group in user_groups for group in self.roles[role]):
                    return True
        return False

    def has_permission(self):
        """
        Override to check both permissions and roles.
        """
        return super().has_permission() and self.has_role()

class DataIsolationMixin:
    """
    Mixin to enforce data isolation in querysets.
    Ensures users can only access their own data.
    """
    def get_queryset(self):
        """
        Filter queryset to only show user's own data.
        Override this method to implement custom filtering logic.
        """
        queryset = super().get_queryset()
        user = self.request.user

        if user.is_superuser:
            return queryset

        # Skip isolation for public data
        if getattr(self, 'is_public_data', False):
            return queryset

        try:
            # Default filtering by user field
            if hasattr(queryset.model, 'user'):
                return queryset.filter(user=user)

            # Custom filtering for specific models
            model_name = queryset.model.__name__
            if model_name == 'GameCards':
                return queryset.filter(active=True)  # Public data
            elif model_name == 'BlogPost':
                return queryset.filter(
                    Q(author=user) | 
                    Q(published=True) & 
                    Q(published_at__lte=timezone.now())
                )
            elif model_name == 'UserCasinoVisit':
                return queryset.filter(user=user)
            elif model_name == 'CardClick':
                if hasattr(queryset.model, 'user'):
                    return queryset.filter(user=user)
                elif hasattr(queryset.model, 'session_id'):
                    return queryset.filter(session_id=self.request.session.session_key)
                return queryset
            elif model_name == 'SiteSettings':
                # Only superusers can access site settings
                if not user.is_superuser:
                    raise PermissionDenied(_("Only superusers can access site settings."))
                return queryset
            elif model_name == 'UserProfile':
                return queryset.filter(user=user)
            elif model_name == 'Transaction':
                return queryset.filter(
                    Q(user=user) | 
                    Q(related_user=user)
                )

            # Check for owner/creator fields
            owner_fields = ['owner', 'created_by', 'author', 'user', 'profile']
            for field in owner_fields:
                if hasattr(queryset.model, field):
                    return queryset.filter(**{field: user})

            # If no specific filtering is defined, deny access
            logger.warning(
                f"Data isolation: No filtering defined for model {model_name} - "
                f"User: {user.username} - "
                f"Path: {self.request.path}"
            )
            raise PermissionDenied(_("You don't have permission to access this data."))

        except Exception as e:
            logger.error(
                f"Data isolation error: {str(e)} - "
                f"Model: {queryset.model.__name__} - "
                f"User: {user.username} - "
                f"Path: {self.request.path}"
            )
            raise PermissionDenied(_("An error occurred while checking data access permissions."))

    def get_object(self):
        """
        Override get_object to ensure data isolation is enforced
        even for single object retrieval.
        """
        obj = super().get_object()
        user = self.request.user

        if user.is_superuser:
            return obj

        # Skip isolation check for public data
        if getattr(self, 'is_public_data', False):
            return obj

        try:
            # Check ownership for specific models
            model_name = obj.__class__.__name__
            if model_name == 'BlogPost':
                if not (obj.author == user or (obj.published and obj.published_at <= timezone.now())):
                    raise PermissionDenied(_("You don't have permission to access this blog post."))
            elif model_name == 'GameCards':
                if not obj.active:
                    raise PermissionDenied(_("This game card is not active."))
            elif model_name == 'Transaction':
                if not (obj.user == user or obj.related_user == user):
                    raise PermissionDenied(_("You don't have permission to access this transaction."))
            elif model_name == 'SiteSettings':
                if not user.is_superuser:
                    raise PermissionDenied(_("Only superusers can access site settings."))

            # Check for owner/creator fields
            owner_fields = ['owner', 'created_by', 'author', 'user', 'profile']
            for field in owner_fields:
                if hasattr(obj, field) and getattr(obj, field) == user:
                    return obj

            # If no specific check passed, deny access
            raise PermissionDenied(_("You don't have permission to access this object."))

        except PermissionDenied:
            raise
        except Exception as e:
            logger.error(
                f"Data isolation error in get_object: {str(e)} - "
                f"Model: {obj.__class__.__name__} - "
                f"User: {user.username} - "
                f"Path: {self.request.path}"
            )
            raise PermissionDenied(_("An error occurred while checking object access permissions."))

class AuditLogMixin:
    """
    Mixin to automatically log model changes.
    """
    def save_model(self, request, obj, form, change):
        """
        Override to log model changes.
        """
        from .models import SystemLog
        from django.contrib.contenttypes.models import ContentType

        super().save_model(request, obj, form, change)

        # Determine action type
        if change:
            action = 'UPDATE'
            message = f"Updated {obj._meta.verbose_name} '{obj}'"
        else:
            action = 'CREATE'
            message = f"Created {obj._meta.verbose_name} '{obj}'"

        # Log the action
        SystemLog.log(
            level='INFO',
            action=action,
            message=message,
            user=request.user,
            ip_address=request.META.get('REMOTE_ADDR'),
            affected_model=ContentType.objects.get_for_model(obj).model,
            affected_id=obj.pk,
            details={
                'changed_fields': list(form.changed_data) if change else None,
                'object_repr': str(obj),
            }
        )

    def delete_model(self, request, obj):
        """
        Override to log model deletion.
        """
        from .models import SystemLog
        from django.contrib.contenttypes.models import ContentType

        # Log before deletion
        SystemLog.log(
            level='WARNING',
            action='DELETE',
            message=f"Deleted {obj._meta.verbose_name} '{obj}'",
            user=request.user,
            ip_address=request.META.get('REMOTE_ADDR'),
            affected_model=ContentType.objects.get_for_model(obj).model,
            affected_id=obj.pk,
            details={'object_repr': str(obj)}
        )

        super().delete_model(request, obj) 
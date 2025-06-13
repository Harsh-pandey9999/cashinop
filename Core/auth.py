from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import logging
from .utils import get_client_ip, log_security_event
from django.core.cache import cache

logger = logging.getLogger(__name__)
User = get_user_model()

class SecurityAwareAuthenticationBackend(ModelBackend):
    """
    Custom authentication backend that implements additional security measures.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None

        # Check for IP-based rate limiting
        client_ip = get_client_ip(request)
        if self._is_ip_rate_limited(client_ip):
            log_security_event(
                'ip_rate_limited',
                None,
                client_ip,
                {'username': username},
                level='warning'
            )
            raise PermissionDenied(_('Too many login attempts from this IP. Please try again later.'))

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # Log failed login attempt with IP tracking
            self._log_failed_attempt(client_ip, username)
            log_security_event(
                'failed_login',
                None,
                client_ip,
                {
                    'username': username,
                    'reason': 'user_not_found',
                    'user_agent': request.META.get('HTTP_USER_AGENT', 'Unknown')
                },
                level='warning'
            )
            return None

        # Check if user is active
        if not user.is_active:
            log_security_event(
                'failed_login',
                user,
                client_ip,
                {
                    'reason': 'account_inactive',
                    'user_agent': request.META.get('HTTP_USER_AGENT', 'Unknown')
                },
                level='warning'
            )
            raise PermissionDenied(_('This account is inactive.'))

        # Check if user is locked out
        if hasattr(user, 'casino_profile'):
            profile = user.casino_profile
            if profile.failed_login_attempts >= settings.CASINO_SETTINGS['MAX_LOGIN_ATTEMPTS']:
                lockout_time = profile.last_failed_login + timedelta(seconds=settings.CASINO_SETTINGS['LOGIN_TIMEOUT'])
                if timezone.now() < lockout_time:
                    remaining_time = int((lockout_time - timezone.now()).total_seconds())
                    log_security_event(
                        'login_locked',
                        user,
                        client_ip,
                        {
                            'attempts': profile.failed_login_attempts,
                            'lockout_until': lockout_time.isoformat(),
                            'remaining_seconds': remaining_time,
                            'user_agent': request.META.get('HTTP_USER_AGENT', 'Unknown')
                        },
                        level='warning'
                    )
                    raise PermissionDenied(_('Account is temporarily locked. Please try again in %(seconds)d seconds.') % {'seconds': remaining_time})

        # Verify password
        if not user.check_password(password):
            # Update failed login attempts
            if hasattr(user, 'casino_profile'):
                profile = user.casino_profile
                profile.failed_login_attempts += 1
                profile.last_failed_login = timezone.now()
                profile.save()

                # Check if user should be locked out
                if profile.failed_login_attempts >= settings.CASINO_SETTINGS['MAX_LOGIN_ATTEMPTS']:
                    lockout_time = timezone.now() + timedelta(seconds=settings.CASINO_SETTINGS['LOGIN_TIMEOUT'])
                    log_security_event(
                        'account_locked',
                        user,
                        client_ip,
                        {
                            'attempts': profile.failed_login_attempts,
                            'lockout_until': lockout_time.isoformat(),
                            'user_agent': request.META.get('HTTP_USER_AGENT', 'Unknown')
                        },
                        level='warning'
                    )
                    raise PermissionDenied(_('Too many failed login attempts. Account is temporarily locked for %(seconds)d seconds.') % {'seconds': settings.CASINO_SETTINGS['LOGIN_TIMEOUT']})

            # Log failed attempt with IP tracking
            self._log_failed_attempt(client_ip, username)
            log_security_event(
                'failed_login',
                user,
                client_ip,
                {
                    'reason': 'invalid_password',
                    'attempts': profile.failed_login_attempts if hasattr(user, 'casino_profile') else None,
                    'user_agent': request.META.get('HTTP_USER_AGENT', 'Unknown')
                },
                level='warning'
            )
            return None

        # Check for suspicious login patterns
        if self._is_suspicious_login(user, client_ip, request):
            log_security_event(
                'suspicious_login',
                user,
                client_ip,
                {
                    'user_agent': request.META.get('HTTP_USER_AGENT', 'Unknown'),
                    'previous_ip': profile.last_login_ip if hasattr(user, 'casino_profile') else None
                },
                level='warning'
            )
            # Don't block the login, but log it for monitoring

        # Reset failed login attempts on successful login
        if hasattr(user, 'casino_profile'):
            profile = user.casino_profile
            profile.failed_login_attempts = 0
            profile.last_failed_login = None
            profile.last_login_ip = client_ip
            profile.last_login_at = timezone.now()
            profile.save()

        # Log successful login
        log_security_event(
            'successful_login',
            user,
            client_ip,
            {
                'user_agent': request.META.get('HTTP_USER_AGENT', 'Unknown'),
                'login_method': 'password'
            },
            level='info'
        )

        return user

    def _is_ip_rate_limited(self, client_ip):
        """
        Check if an IP address is rate limited.
        """
        cache_key = f'login_attempts_ip_{client_ip}'
        attempts = cache.get(cache_key, 0)
        
        if attempts >= settings.CASINO_SETTINGS.get('MAX_IP_LOGIN_ATTEMPTS', 10):
            return True
            
        cache.set(cache_key, attempts + 1, settings.CASINO_SETTINGS.get('IP_LOGIN_TIMEOUT', 300))
        return False

    def _log_failed_attempt(self, client_ip, username):
        """
        Log a failed login attempt for an IP address.
        """
        cache_key = f'login_attempts_ip_{client_ip}'
        attempts = cache.get(cache_key, 0) + 1
        cache.set(cache_key, attempts, settings.CASINO_SETTINGS.get('IP_LOGIN_TIMEOUT', 300))

    def _is_suspicious_login(self, user, client_ip, request):
        """
        Check for suspicious login patterns.
        """
        if not hasattr(user, 'casino_profile'):
            return False

        profile = user.casino_profile
        if not profile.last_login_ip:
            return False

        # Check if login is from a different country (if geoip is available)
        try:
            from django.contrib.gis.geoip2 import GeoIP2
            g = GeoIP2()
            current_country = g.country(client_ip)['country_code']
            last_country = g.country(profile.last_login_ip)['country_code']
            if current_country != last_country:
                return True
        except:
            pass

        # Check if login is from a different user agent
        current_ua = request.META.get('HTTP_USER_AGENT', '')
        if profile.last_user_agent and current_ua != profile.last_user_agent:
            return True

        # Check if login is from a different IP range
        if profile.last_login_ip:
            current_ip_parts = client_ip.split('.')
            last_ip_parts = profile.last_login_ip.split('.')
            if len(current_ip_parts) == 4 and len(last_ip_parts) == 4:
                # Check if first two octets are different
                if current_ip_parts[0] != last_ip_parts[0] or current_ip_parts[1] != last_ip_parts[1]:
                    return True

        return False

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

class RoleBasedAuthenticationBackend(SecurityAwareAuthenticationBackend):
    """
    Authentication backend that enforces role-based access control.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        user = super().authenticate(request, username, password, **kwargs)
        
        if user is not None:
            # Check if user has required roles
            required_roles = getattr(request, 'required_roles', None)
            if required_roles:
                user_roles = set(user.groups.values_list('name', flat=True))
                if not any(role in user_roles for role in required_roles):
                    log_security_event(
                        'role_violation',
                        user,
                        get_client_ip(request),
                        {
                            'required_roles': required_roles,
                            'user_roles': list(user_roles)
                        },
                        level='warning'
                    )
                    raise PermissionDenied(_('You do not have the required role to access this resource.'))

        return user

class DataIsolationAuthenticationBackend(SecurityAwareAuthenticationBackend):
    """
    Authentication backend that enforces data isolation.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        user = super().authenticate(request, username, password, **kwargs)
        
        if user is not None:
            # Check if user is approved
            if hasattr(user, 'casino_profile') and not user.casino_profile.is_approved:
                log_security_event(
                    'unapproved_access',
                    user,
                    get_client_ip(request),
                    {'reason': 'account_not_approved'},
                    level='warning'
                )
                raise PermissionDenied(_('Your account is pending approval.'))

        return user

def get_backends():
    """
    Get the list of authentication backends to use.
    """
    return [
        'Core.auth.RoleBasedAuthenticationBackend',
        'Core.auth.DataIsolationAuthenticationBackend',
        'Core.auth.SecurityAwareAuthenticationBackend',
        'django.contrib.auth.backends.ModelBackend',
    ] 
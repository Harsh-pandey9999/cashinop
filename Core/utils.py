from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from rest_framework import status
from rest_framework.exceptions import APIException, NotAuthenticated, PermissionDenied as DRFPermissionDenied
from rest_framework.response import Response
from rest_framework.views import exception_handler
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SecurityException(APIException):
    """
    Base class for security-related exceptions.
    """
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = _('Security violation detected.')
    default_code = 'security_violation'

class RateLimitExceeded(SecurityException):
    """
    Exception raised when rate limit is exceeded.
    """
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_detail = _('Rate limit exceeded. Please try again later.')
    default_code = 'rate_limit_exceeded'

class InvalidToken(SecurityException):
    """
    Exception raised when token is invalid or expired.
    """
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = _('Invalid or expired token.')
    default_code = 'invalid_token'

class DataIsolationViolation(SecurityException):
    """
    Exception raised when data isolation is violated.
    """
    default_detail = _('Access denied due to data isolation policy.')
    default_code = 'data_isolation_violation'

class RoleViolation(SecurityException):
    """
    Exception raised when role-based access is violated.
    """
    default_detail = _('You do not have the required role to access this resource.')
    default_code = 'role_violation'

def custom_exception_handler(exc, context):
    """
    Custom exception handler for the API.
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)

    if response is None:
        if isinstance(exc, Http404):
            exc = APIException(detail=_('Not found.'), code='not_found')
            response = exception_handler(exc, context)
        elif isinstance(exc, PermissionDenied):
            exc = DRFPermissionDenied(detail=_('Permission denied.'), code='permission_denied')
            response = exception_handler(exc, context)
        elif isinstance(exc, ValidationError):
            exc = APIException(detail=str(exc), code='validation_error')
            response = exception_handler(exc, context)
        elif isinstance(exc, Exception):
            # Log unexpected exceptions
            logger.exception(
                f"Unexpected exception: {exc.__class__.__name__} - "
                f"Detail: {str(exc)} - "
                f"User: {context['request'].user.username if context['request'].user.is_authenticated else 'Anonymous'} - "
                f"Path: {context['request'].path}"
            )
            exc = APIException(detail=_('An unexpected error occurred.'), code='unexpected_error')
            response = exception_handler(exc, context)

    if response is not None:
        # Add timestamp to response
        response.data['timestamp'] = datetime.now().isoformat()
        
        # Log security-related exceptions with more context
        if isinstance(exc, SecurityException):
            logger.warning(
                f"Security exception: {exc.__class__.__name__} - "
                f"Detail: {exc.detail} - "
                f"Code: {exc.default_code} - "
                f"User: {context['request'].user.username if context['request'].user.is_authenticated else 'Anonymous'} - "
                f"Path: {context['request'].path} - "
                f"Method: {context['request'].method} - "
                f"IP: {get_client_ip(context['request'])} - "
                f"User-Agent: {context['request'].META.get('HTTP_USER_AGENT', 'Unknown')}"
            )

        # Add custom error code to response
        if hasattr(exc, 'default_code'):
            response.data['code'] = exc.default_code
        elif hasattr(exc, 'code'):
            response.data['code'] = exc.code
        else:
            response.data['code'] = 'error'

        # Add request ID to response if available
        if hasattr(context['request'], 'request_id'):
            response.data['request_id'] = context['request'].request_id

        # Enhanced sanitization for production
        if not settings.DEBUG:
            if isinstance(response.data, dict):
                if 'detail' in response.data:
                    # Keep only the error code for security-related exceptions
                    if isinstance(exc, SecurityException):
                        response.data['detail'] = _('A security error occurred. Please try again later.')
                    # Sanitize other error messages
                    elif not isinstance(exc, (NotAuthenticated, DRFPermissionDenied)):
                        response.data['detail'] = _('An error occurred. Please try again later.')
                    # Remove any sensitive information
                    for key in list(response.data.keys()):
                        if key.lower() in ['password', 'token', 'secret', 'key', 'authorization']:
                            del response.data[key]

    return response

def get_client_ip(request):
    """
    Get the client IP address from the request.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def validate_password_strength(password):
    """
    Validate password strength according to security requirements.
    """
    from django.conf import settings
    from django.core.exceptions import ValidationError
    import re

    if len(password) < settings.CASINO_SETTINGS['MIN_PASSWORD_LENGTH']:
        raise ValidationError(
            _('Password must be at least %(min_length)d characters long.'),
            params={'min_length': settings.CASINO_SETTINGS['MIN_PASSWORD_LENGTH']},
        )

    complexity = settings.CASINO_SETTINGS['PASSWORD_COMPLEXITY']
    
    if complexity['UPPER'] and not re.search(r'[A-Z]', password):
        raise ValidationError(_('Password must contain at least one uppercase letter.'))
    
    if complexity['LOWER'] and not re.search(r'[a-z]', password):
        raise ValidationError(_('Password must contain at least one lowercase letter.'))
    
    if complexity['DIGITS'] and not re.search(r'\d', password):
        raise ValidationError(_('Password must contain at least one digit.'))
    
    if complexity['SPECIAL'] and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        raise ValidationError(_('Password must contain at least one special character.'))

    return True

def sanitize_filename(filename):
    """
    Sanitize filename to prevent directory traversal and other security issues.
    """
    import os
    from django.utils.text import get_valid_filename
    
    # Get the base filename without path
    filename = os.path.basename(filename)
    
    # Remove any null bytes
    filename = filename.replace('\0', '')
    
    # Get a valid filename
    filename = get_valid_filename(filename)
    
    # Add a timestamp to prevent filename collisions
    name, ext = os.path.splitext(filename)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{name}_{timestamp}{ext}"

def validate_file_type(file_obj, allowed_types):
    """
    Validate file type using both extension and content type.
    """
    import magic
    import os
    
    # Get file extension
    ext = os.path.splitext(file_obj.name)[1].lower()
    
    # Check file extension
    if not any(file_obj.name.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif']):
        raise ValidationError(_('Invalid file type. Allowed types: JPG, JPEG, PNG, GIF'))
    
    # Check file content type
    content_type = magic.from_buffer(file_obj.read(1024), mime=True)
    file_obj.seek(0)  # Reset file pointer
    
    if content_type not in allowed_types:
        raise ValidationError(_('Invalid file content type.'))
    
    return True

def validate_file_size(file_obj, max_size):
    """
    Validate file size.
    """
    if file_obj.size > max_size:
        raise ValidationError(
            _('File size must be no more than %(max_size)d bytes.'),
            params={'max_size': max_size},
        )
    return True

def generate_secure_token(length=32):
    """
    Generate a secure random token.
    """
    import secrets
    return secrets.token_urlsafe(length)

def hash_sensitive_data(data):
    """
    Hash sensitive data for logging.
    """
    import hashlib
    return hashlib.sha256(str(data).encode()).hexdigest()

def mask_sensitive_data(data, mask_char='*'):
    """
    Mask sensitive data for logging.
    """
    if not data:
        return data
    
    if isinstance(data, str):
        if '@' in data:  # Email
            username, domain = data.split('@')
            return f"{username[:2]}{mask_char * (len(username)-2)}@{domain}"
        elif len(data) > 4:  # Credit card, phone, etc.
            return f"{data[:2]}{mask_char * (len(data)-4)}{data[-2:]}"
        else:
            return mask_char * len(data)
    
    return str(data)

def log_security_event(event_type, user, ip_address, details=None, level='info'):
    """
    Log security-related events.
    """
    log_data = {
        'event_type': event_type,
        'user': user.username if user.is_authenticated else 'Anonymous',
        'ip_address': ip_address,
        'timestamp': datetime.now().isoformat(),
        'details': details or {},
    }
    
    # Mask sensitive data in details
    if details:
        for key, value in details.items():
            if any(sensitive in key.lower() for sensitive in ['password', 'token', 'key', 'secret']):
                log_data['details'][key] = mask_sensitive_data(value)
    
    # Log the event
    log_message = f"Security Event: {event_type} - User: {log_data['user']} - IP: {log_data['ip_address']}"
    if details:
        log_message += f" - Details: {log_data['details']}"
    
    if level == 'warning':
        logger.warning(log_message)
    elif level == 'error':
        logger.error(log_message)
    else:
        logger.info(log_message)
    
    return log_data 
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.http import JsonResponse
from .models import Contact
import json

def get_client_ip(request):
    """Get the client's IP address from the request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

@csrf_exempt
@require_http_methods(["POST"])
def submit_contact_form(request):
    """Handle contact form submission."""
    try:
        # Parse JSON data from request body
        data = json.loads(request.body)
        
        # Get form data
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        subject = data.get('subject', '').strip()
        message = data.get('message', '').strip()
        
        # Basic validation
        if not all([name, email, subject, message]):
            return JsonResponse(
                {'success': False, 'message': 'All fields are required.'}, 
                status=400
            )
            
        if '@' not in email or '.' not in email:
            return JsonResponse(
                {'success': False, 'message': 'Please enter a valid email address.'}, 
                status=400
            )
        
        # Get client IP
        ip_address = get_client_ip(request)
        
        # Create and save contact submission
        contact = Contact(
            name=name,
            email=email,
            subject=subject,
            message=message,
            ip_address=ip_address
        )
        contact.save()
        
        # Here you can add email notification if needed
        # send_contact_notification(contact)
        
        return JsonResponse({
            'success': True, 
            'message': 'Thank you for your message. We will get back to you soon!'
        })
        
    except json.JSONDecodeError:
        return JsonResponse(
            {'success': False, 'message': 'Invalid JSON data.'}, 
            status=400
        )
    except Exception as e:
        if settings.DEBUG:
            return JsonResponse(
                {'success': False, 'message': f'An error occurred: {str(e)}'}, 
                status=500
            )
        return JsonResponse(
            {'success': False, 'message': 'An error occurred while processing your request.'}, 
            status=500
        )

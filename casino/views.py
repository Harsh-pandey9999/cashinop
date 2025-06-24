from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.shortcuts import render, redirect

@login_required
@user_passes_test(is_admin)
def admin_logs(request):
    logs = SystemLog.objects.all()
    
    # Filtering
    level = request.GET.get('level')
    action = request.GET.get('action')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if level:
        logs = logs.filter(level=level)
    if action:
        logs = logs.filter(action=action)
    if date_from:
        logs = logs.filter(timestamp__gte=date_from)
    if date_to:
        logs = logs.filter(timestamp__lte=date_to)
    
    # Pagination
    paginator = Paginator(logs, 50)
    page = request.GET.get('page')
    logs = paginator.get_page(page)
    
    context = {
        'logs': logs,
        'log_levels': SystemLog.LOG_LEVELS,
        'action_types': SystemLog.ACTION_TYPES,
        'current_filters': {
            'level': level,
            'action': action,
            'date_from': date_from,
            'date_to': date_to,
        }
    }
    
    return render(request, 'admin_logs.html', context)

@login_required
@user_passes_test(is_admin)
def clear_logs(request):
    if request.method == 'POST':
        days = int(request.POST.get('days', 30))
        cutoff_date = timezone.now() - timezone.timedelta(days=days)
        SystemLog.objects.filter(timestamp__lt=cutoff_date).delete()
        
        SystemLog.log(
            level='INFO',
            action='SYSTEM',
            message=f'Cleared logs older than {days} days',
            user=request.user,
            ip_address=get_client_ip(request)
        )
        
        messages.success(request, f'Successfully cleared logs older than {days} days')
        return redirect('admin_logs')
    
    return render(request, 'clear_logs.html')

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

# Middleware for automatic logging
class LoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Only log admin actions
        if request.path.startswith('/admin/') and request.user.is_authenticated and is_admin(request.user):
            if request.method in ['POST', 'PUT', 'DELETE']:
                action = 'UPDATE'
                if request.method == 'POST':
                    action = 'CREATE'
                elif request.method == 'DELETE':
                    action = 'DELETE'
                
                SystemLog.log(
                    level='INFO',
                    action=action,
                    message=f'{request.method} request to {request.path}',
                    user=request.user,
                    ip_address=get_client_ip(request),
                    details={
                        'method': request.method,
                        'path': request.path,
                        'data': request.POST.dict() if request.method == 'POST' else None
                    }
                )
        
        return response 
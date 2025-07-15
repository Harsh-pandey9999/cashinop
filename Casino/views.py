from django.contrib.auth import logout
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_protect

@csrf_protect
def admin_logout(request):
    if request.method == 'POST':
        logout(request)
        return redirect(reverse('admin:index'))
    return redirect(reverse('admin:logout'))

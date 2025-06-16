from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User, auth
from django.core.cache import cache
from django.http import HttpResponse, Http404, HttpResponseServerError
from django.contrib import messages
from Core.models import CardClick, GameCards
import datetime
from django.contrib.auth.decorators import login_required
from .models import CasinoUser, Contact, About, SiteSettings, SystemLog, BlogPost
from django.shortcuts import render, redirect, get_object_or_404
from .forms import PostForm,AboutForm,BlogPostForm
from django import forms
from django.contrib.auth.decorators import login_required

from django.forms.models import model_to_dict

from django.core.exceptions import PermissionDenied


from django.db.models.functions import TruncMonth
from django.db.models import Count
from datetime import datetime, timedelta
from django.utils.timezone import now

from django.conf import settings
from django.template import loader
from django.views.decorators.csrf import requires_csrf_token

from django.core.paginator import Paginator
from django.utils import timezone

from django.contrib.auth.decorators import user_passes_test

from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import redirect_to_login
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .permissions import get_permission_classes, IsOwnerOrAdmin, IsVerifiedUser, IsNotLocked
from .utils import get_client_ip, log_security_event
import logging
import uuid

logger = logging.getLogger(__name__)

def superuser_or_staff_required(view_func):
    @login_required(login_url="/admin/login/")
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_superuser or request.user.is_staff:
            return view_func(request, *args, **kwargs)
        raise PermissionDenied
    return _wrapped_view


def is_admin(user):
    return user.is_authenticated and user.is_staff


def index(request):
    # Get all active game cards
    cards = GameCards.objects.filter(active=True)
    
    # Get site settings
    site_settings = SiteSettings.objects.first()
    
    # Get about sections
    about_sections = About.objects.all()
    
    # Get contact information
    contact_info = Contact.objects.first()
    contact_data = None
    if contact_info:
        contact_data = {
            "mail": contact_info.email,
            "ph": contact_info.phone,
            "address": contact_info.address
        }
    
    # Prepare context with all necessary data
    context = {
        "cards": cards,
        "site_settings": site_settings,
        "abouts": about_sections,
        "contact": contact_data,
    }
    
    # Add site_logo for backward compatibility
    if site_settings and site_settings.site_logo:
        context["site_logo"] = site_settings.site_logo.url
    
    return render(request, "index.html", context)

def signup(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        first_name = request.POST["first_name"]
        last_name = request.POST["last_name"]
        password = request.POST["password"]
        password2 = request.POST["password2"]
        
        # Validate all required fields
        if not (username and email and first_name and last_name and password and password2):
            messages.error(request, "All fields are required")
            return redirect("signup")
            
        if password == password2:
            if User.objects.filter(email=email).exists():
                messages.error(request, "Email Already Used")
                return redirect("signup")
            elif User.objects.filter(username=username).exists():
                messages.error(request, "Username Already Used")
                return redirect("signup")
            else:
                # Create the User first
                user = User.objects.create_user(
                    username=username, 
                    email=email, 
                    password=password,
                    first_name=first_name,
                    last_name=last_name
                )
                
                # The CasinoUser will be created automatically by the signal
                # No need to create it manually
                
                messages.success(request, "Account Created Successfully and Pending Admin approval")
                return redirect("signin")
        else:
            messages.error(request, "Passwords do not match")
            return redirect("signup")

    return render(request, "signup.html")


def signin(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        
        try:
            cas = CasinoUser.objects.get(username=username)
            user = auth.authenticate(request, username=username, password=password)
            
            if user is not None:
                if cas.is_approved:
                    auth.login(request, user)
                    
                    # Redirect based on user role
                    if user.is_staff or user.is_superuser:
                        return redirect('admin_dashboard')
                    else:
                        return redirect('user_dashboard')
                else:
                    messages.error(request, "Your account is pending approval.")
                    return redirect("signin")
            else:
                messages.info(request, "Invalid Credentials")
                return redirect("signin")
        except CasinoUser.DoesNotExist:
            messages.info(request, "User does not exist")
            return redirect("signin")
    else:
        # Check if user is already logged in
        if request.user.is_authenticated:
            if request.user.is_staff or request.user.is_superuser:
                return redirect('admin_dashboard')
            else:
                return redirect('user_dashboard')
        return render(request, "signin.html")



@login_required(login_url="/signin/")
def logout(request):
    auth.logout(request)
    return redirect("signin")




@superuser_or_staff_required
def admin_logout(request):
    auth.logout(request)
    return redirect("index")

# locked with admin login 
# also new user approval


@superuser_or_staff_required
def admin_0_dashboard(request):
    # Get user registration counts grouped by month (last 6 months)
    six_months_ago = now() - timedelta(days=180)
    users_per_month = (
        User.objects.filter(date_joined__gte=six_months_ago)
        .annotate(month=TruncMonth('date_joined'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )

    # Prepare data for chart - labels and counts for last 6 months
    labels = []
    user_counts = []
    current_month = now().replace(day=1)
    for i in range(6):
        month = current_month - timedelta(days=30 * (5 - i))
        label = month.strftime('%b %Y')
        labels.append(label)
        # Find count for this month
        count = 0
        for entry in users_per_month:
            if entry['month'].strftime('%b %Y') == label:
                count = entry['count']
                break
        user_counts.append(count)

    # Total users
    total_users = User.objects.count()

    # Visitor counts - simulate last 7 days data
    # Ideally, you have a model that tracks visitors daily; here we'll fake it
    visitor_labels = []
    visitor_counts = []
    for i in range(7):
        day = now().date() - timedelta(days=6 - i)
        visitor_labels.append(day.strftime('%a %d'))
        # Simulate visitor counts
        visitor_counts.append(100 + i * 15)  # replace with real data

    # Total visitors count (sum last 7 days)
    total_visitors = sum(visitor_counts)

    context = {
        'total_users': total_users,
        'user_chart_labels': labels,
        'user_chart_data': user_counts,
        'total_visitors': total_visitors,
        'visitor_chart_labels': visitor_labels,
        'visitor_chart_data': visitor_counts,
    }
    return render(request, 'dashboard.html', context)

@superuser_or_staff_required
def admin_dashboard(request):
    # Basic statistics
    total_users = User.objects.count()
    pending_users = CasinoUser.objects.filter(is_approved=False).count()
    total_posts = GameCards.objects.count()
    active_posts = GameCards.objects.filter(active=True).count()
    
    # Get site settings
    site_settings = SiteSettings.objects.first()
    if not site_settings:
        site_settings = SiteSettings.objects.create()
    
    # Get Django version
    import django
    django_version = django.get_version()
    
    # Get CSRF trusted origins from settings
    csrf_trusted_origins = getattr(settings, 'CSRF_TRUSTED_ORIGINS', [])
    
    # Analytics data (dummy data - in a real app, this would come from the database)
    # Visitor analytics for the chart
    visitor_labels = []
    visitor_counts = []
    for i in range(7):
        day = now().date() - timedelta(days=6 - i)
        visitor_labels.append(day.strftime('%a %d'))
        visitor_counts.append(100 + i * 15)
    
    # Recent admin activities (dummy data - in a real app, this would come from the database)
    recent_activities = [
        {
            'user': request.user.username,
            'action': 'Logged in',
            'timestamp': now() - timedelta(minutes=5),
            'status': 'success'
        },
        {
            'user': 'System',
            'action': 'Updated site settings',
            'timestamp': now() - timedelta(hours=2),
            'status': 'info'
        },
        {
            'user': 'Admin',
            'action': 'Added new casino card',
            'timestamp': now() - timedelta(days=1),
            'status': 'success'
        },
        {
            'user': 'User123',
            'action': 'Requested approval',
            'timestamp': now() - timedelta(days=2),
            'status': 'warning'
        }
    ]
    
    # Card click statistics (dummy data - in a real app, this would come from the database)
    total_clicks = 642
    total_views = 2458
    unique_visitors = 1842
    avg_duration = '2m 45s'
    bounce_rate = '32.8%'
    
    context = {
        # Basic statistics
        'total_users': total_users,
        'pending_users': pending_users,
        'total_posts': total_posts,
        'active_posts': active_posts,
        
        # Site settings
        'site_settings': site_settings,
        'django_version': django_version,
        'csrf_trusted_origins': '\n'.join(csrf_trusted_origins),
        
        # Analytics data
        'visitor_labels': visitor_labels,
        'visitor_counts': visitor_counts,
        'recent_activities': recent_activities,
        'total_clicks': total_clicks,
        'total_views': total_views,
        'unique_visitors': unique_visitors,
        'avg_duration': avg_duration,
        'bounce_rate': bounce_rate,
    }
    
    return render(request, 'dashboard.html', context)

@superuser_or_staff_required
def admin_dashboard_new(request):
    # Basic statistics
    total_users = User.objects.count()
    pending_users = CasinoUser.objects.filter(is_approved=False).count()
    total_posts = GameCards.objects.count()
    active_posts = GameCards.objects.filter(active=True).count()
    
    # Get site settings
    site_settings = SiteSettings.objects.first()
    if not site_settings:
        site_settings = SiteSettings.objects.create()
    
    # Get Django version
    import django
    django_version = django.get_version()
    
    # Get CSRF trusted origins from settings
    csrf_trusted_origins = getattr(settings, 'CSRF_TRUSTED_ORIGINS', [])
    
    # Analytics data (dummy data - in a real app, this would come from the database)
    # Visitor analytics for the chart
    visitor_labels = []
    visitor_counts = []
    for i in range(7):
        day = now().date() - timedelta(days=6 - i)
        visitor_labels.append(day.strftime('%a %d'))
        visitor_counts.append(100 + i * 15)
    
    # Recent admin activities (dummy data - in a real app, this would come from the database)
    recent_activities = [
        {
            'user': request.user.username,
            'action': 'Logged in',
            'timestamp': now() - timedelta(minutes=5),
            'status': 'success'
        },
        {
            'user': 'System',
            'action': 'Updated site settings',
            'timestamp': now() - timedelta(hours=2),
            'status': 'info'
        },
        {
            'user': 'Admin',
            'action': 'Added new casino card',
            'timestamp': now() - timedelta(days=1),
            'status': 'success'
        },
        {
            'user': 'User123',
            'action': 'Requested approval',
            'timestamp': now() - timedelta(days=2),
            'status': 'warning'
        }
    ]
    
    # Card click statistics (dummy data - in a real app, this would come from the database)
    total_clicks = 642
    total_views = 2458
    unique_visitors = 1842
    avg_duration = '2m 45s'
    bounce_rate = '32.8%'
    
    context = {
        # Basic statistics
        'total_users': total_users,
        'pending_users': pending_users,
        'total_posts': total_posts,
        'active_posts': active_posts,
        
        # Site settings
        'site_settings': site_settings,
        'django_version': django_version,
        'csrf_trusted_origins': '\n'.join(csrf_trusted_origins),
        
        # Analytics data
        'visitor_labels': visitor_labels,
        'visitor_counts': visitor_counts,
        'recent_activities': recent_activities,
        'total_clicks': total_clicks,
        'total_views': total_views,
        'unique_visitors': unique_visitors,
        'avg_duration': avg_duration,
        'bounce_rate': bounce_rate,
    }
    
    return render(request, 'admin_dashboard_new.html', context)

@superuser_or_staff_required
def approve_users(request):
    users = CasinoUser.objects.filter(is_approved=False)
    return render(request, 'approve_users.html', {'users': users})

@superuser_or_staff_required
def posts(request):
    posts = GameCards.objects.all().order_by('created_at')
    print(posts)
    return render(request, 'posts.html', {'posts': posts})

@superuser_or_staff_required
def toggle_post_visibility(request, post_id):
    post = get_object_or_404(GameCards, id=post_id)
    post.active = not post.active
    post.save()
    return redirect('posts')

@superuser_or_staff_required
def add_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('posts')
    else:
        form = PostForm()
    return render(request, 'add_post.html', {'form': form})


#@user_passes_test(lambda u: u.is_superuser)

@superuser_or_staff_required
def approve_user(request, username):
    print(username)
    if request.method == 'POST':
        user = get_object_or_404(CasinoUser, username=username)
        user.is_approved = True  # Assuming pending users are inactive
        user.save()
    return redirect('/dashboard/approve-users/')  #

@superuser_or_staff_required
def user_info(request, username):
    """Returns User Details for approval time """
    #print(username)
    
    user = get_object_or_404(CasinoUser, username=username)
    profile_data = model_to_dict(user)
    user_data = {f"user_{k}": v for k, v in profile_data.items()}
    #print(profile_data)
    return render(request, 'user_approve_info.html', {'user': user_data,'username':user.username})

@superuser_or_staff_required
def delete_post(request, pk):
    post = get_object_or_404(GameCards, pk=pk)
    
    if request.method == 'POST':
        post.delete()
        messages.success(request, 'Post deleted successfully.')
        return redirect('posts')  # Replace with your posts listing view name

    return render(request, 'confirm_delete.html', {'post': post})

@superuser_or_staff_required
def edit_post(request, pk):
    post = get_object_or_404(GameCards, pk=pk)
    form = PostForm(request.POST or None, request.FILES or None, instance=post)

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, 'Post updated successfully.')
            return redirect('posts')  # Adjust this to your actual post list view name

    return render(request, 'edit_post.html', {'form': form, 'post': post})

@superuser_or_staff_required
def contact_update(request):
    # Try to get the single contact instance or None
    contact = Contact.objects.first()

    if request.method == 'POST':
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')

        if contact:
            # Update existing contact
            contact.email = email
            contact.phone = phone
            contact.address = address
            contact.save()
            messages.success(request, "Contact information updated successfully.")
        else:
            # Create new contact
            Contact.objects.create(email=email, phone=phone, address=address)
            messages.success(request, "Contact information created successfully.")

        return redirect('contact_update')  # Adjust URL name as needed

    context = {
        'contact': contact
    }
    return render(request, 'contact_update.html', context)




@login_required
def site_settings_update(request):
    if not request.user.is_superuser:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('home')
    
    site_settings = SiteSettings.objects.first()
    if not site_settings:
        site_settings = SiteSettings.objects.create()
    
    if request.method == 'POST':
        try:
            # General Settings
            site_settings.site_name = request.POST.get('site_name', '')
            site_settings.description = request.POST.get('description', '')
            site_settings.footer_text = request.POST.get('footer_text', '')
            site_settings.copyright_text = request.POST.get('copyright_text', '')
            
            # Logo and Favicon
            if 'logo' in request.FILES:
                site_settings.logo = request.FILES['logo']
            if 'favicon' in request.FILES:
                site_settings.favicon = request.FILES['favicon']
            
            # Colors
            site_settings.primary_color = request.POST.get('primary_color', '#ffd700')
            site_settings.secondary_color = request.POST.get('secondary_color', '#121212')
            
            # Social Media Links
            site_settings.facebook_url = request.POST.get('facebook_url', '')
            site_settings.twitter_url = request.POST.get('twitter_url', '')
            site_settings.instagram_url = request.POST.get('instagram_url', '')
            site_settings.linkedin_url = request.POST.get('linkedin_url', '')
            site_settings.youtube_url = request.POST.get('youtube_url', '')
            site_settings.telegram_url = request.POST.get('telegram_url', '')
            
            # Display Settings
            site_settings.show_footer = request.POST.get('show_footer') == 'on'
            site_settings.show_email_in_header = request.POST.get('show_email_in_header') == 'on'
            site_settings.show_phone_in_header = request.POST.get('show_phone_in_header') == 'on'
            site_settings.show_address_in_footer = request.POST.get('show_address_in_footer') == 'on'
            site_settings.enable_dark_mode = request.POST.get('enable_dark_mode') == 'on'
            
            # System Settings
            site_settings.maintenance_mode = request.POST.get('maintenance_mode') == 'on'
            site_settings.allow_registration = request.POST.get('allow_registration') == 'on'
            site_settings.auto_approve_users = request.POST.get('auto_approve_users') == 'on'
            site_settings.maintenance_message = request.POST.get('maintenance_message', '')
            
            site_settings.save()
            messages.success(request, "Site settings updated successfully!")
            
        except Exception as e:
            messages.error(request, f"Error updating site settings: {str(e)}")
    
    return render(request, 'site_settings_update.html', {'site_settings': site_settings})



@superuser_or_staff_required
def manage_users(request):
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'manage_users.html', {'users': users})

@superuser_or_staff_required
def edit_user(request, user_id):
    user = get_object_or_404(User, id=user_id)

    class UserEditForm(forms.ModelForm):
        class Meta:
            model = User
            fields = ['username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff']

    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "User updated successfully.")
            return redirect('manage_users')
    else:
        form = UserEditForm(instance=user)

    return render(request, 'edit_user.html', {'form': form, 'user_obj': user})

@superuser_or_staff_required
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        user.delete()
        messages.success(request, "User deleted.")
        return redirect('manage_users')
    return render(request, 'confirm_user_delete.html', {'user_obj': user})


@superuser_or_staff_required
def delete_about(request, pk):
    post = get_object_or_404(About, pk=pk)
    
    if request.method == 'GET':
        post.delete()
        messages.success(request, 'About deleted successfully.')
        return redirect('about')  # Replace with your posts listing view name
    return redirect("about")


@superuser_or_staff_required
def add_about(request):
    if request.method == 'POST':
        form = AboutForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('about')
    else:
        form = AboutForm()
    return render(request, 'add_about.html', {'form': form})


@superuser_or_staff_required
def edit_about(request, pk):
    post = get_object_or_404(About, pk=pk)
    form = AboutForm(request.POST or None, instance=post)

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, 'About updated successfully.')
            return redirect('about')  # Adjust this to your actual post list view name

    return render(request, 'about_update.html', {'form': form, 'post': post})


@superuser_or_staff_required
def about(request):
    abouts = About.objects.all().order_by('updated_at')
    for i in abouts:
        print(i.title)
    return render(request, 'about.html', {'abouts': abouts})

@login_required(login_url='/signin/')
def redirect_to_card_link(request, card_id):
    # Get the card or return 404
    card = get_object_or_404(GameCards, id=card_id, active=True)
    
    # Log the click
    CardClick.objects.create(
        card=card,
        user=request.user if request.user.is_authenticated else None,
        ip_address=get_client_ip(request)
    )
    
    # Redirect to the card's link
    return redirect(card.redirect_link)





def contact_page(request):
    """
    Public contact page view
    """
    # Get contact information
    contact_info = Contact.objects.first()
    
    # Get site settings
    site_settings = SiteSettings.objects.first()
    
    context = {
        "contact": contact_info,
        "site_settings": site_settings,
    }
    
    return render(request, "contact_page.html", context)


def about_page(request):
    """
    Public about page view
    """
    # Get about sections
    about_sections = About.objects.all()
    # Get site settings
    site_settings = SiteSettings.objects.first()
    context = {
        "abouts": about_sections,
        "site_settings": site_settings,
    }
    return render(request, "about.html", context)

def account_locked(request):
    """
    View to handle locked-out users
    """
    cooloff_time = getattr(settings, 'AXES_COOLOFF_TIME', 1)  # Default to 1 hour if not set
    context = {
        'axes_cooloff_time': cooloff_time,
    }
    return render(request, 'account_locked.html', context)

@requires_csrf_token
def handler404(request, exception=None):
    """
    Custom 404 error handler
    """
    log_security_event(
        'not_found',
        request.user if request.user.is_authenticated else None,
        get_client_ip(request),
        {
            'method': request.method,
            'path': request.path
        },
        level='warning'
    )
    template = loader.get_template('errors/404.html')
    context = {
        'request_path': request.path,
        'site_settings': SiteSettings.objects.first(),
    }
    return HttpResponse(template.render(context, request), status=404)

@requires_csrf_token
def handler500(request, exception=None):
    """
    Custom 500 error handler
    """
    log_security_event(
        'error',
        request.user if request.user.is_authenticated else None,
        get_client_ip(request),
        {
            'method': request.method,
            'path': request.path
        },
        level='error'
    )
    template = loader.get_template('errors/500.html')
    context = {
        'site_settings': SiteSettings.objects.first(),
    }
    return HttpResponseServerError(template.render(context, request))

@requires_csrf_token
def handler403(request, exception=None):
    """
    Custom 403 error handler
    """
    log_security_event(
        'permission_denied',
        request.user if request.user.is_authenticated else None,
        get_client_ip(request),
        {
            'method': request.method,
            'path': request.path,
            'reason': str(exception)
        },
        level='warning'
    )
    template = loader.get_template('errors/403.html')
    context = {
        'site_settings': SiteSettings.objects.first(),
    }
    return HttpResponse(template.render(context, request), status=403)

@requires_csrf_token
def handler400(request, exception=None):
    """
    Custom 400 error handler
    """
    log_security_event(
        'bad_request',
        request.user if request.user.is_authenticated else None,
        get_client_ip(request),
        {
            'method': request.method,
            'path': request.path,
            'reason': str(exception)
        },
        level='warning'
    )
    template = loader.get_template('errors/400.html')
    context = {
        'site_settings': SiteSettings.objects.first(),
    }
    return HttpResponse(template.render(context, request), status=400)

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

@login_required
def blog_list(request):
    posts = BlogPost.objects.filter(published=True).order_by('-published_at')
    print(f"Found {posts.count()} published posts")
    paginator = Paginator(posts, 9)  # Show 9 posts per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    print(f"Page {page_obj.number} of {page_obj.paginator.num_pages}")
    return render(request, 'blog_list.html', {'page_obj': page_obj})

@login_required
def blog_detail(request, slug):
    post = get_object_or_404(BlogPost, slug=slug, published=True)
    return render(request, 'blog_detail.html', {'post': post})

@login_required
@superuser_or_staff_required
def blog_create(request):
    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            messages.success(request, 'Blog post created successfully.')
            return redirect('blog_detail', slug=post.slug)
    else:
        form = BlogPostForm()
    return render(request, 'blog_form.html', {'form': form, 'action': 'Create'})

@login_required
@superuser_or_staff_required
def blog_edit(request, slug):
    post = get_object_or_404(BlogPost, slug=slug)
    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            post = form.save()
            messages.success(request, 'Blog post updated successfully.')
            return redirect('blog_detail', slug=post.slug)
    else:
        form = BlogPostForm(instance=post)
    return render(request, 'blog_form.html', {'form': form, 'post': post, 'action': 'Edit'})

@login_required
@superuser_or_staff_required
def blog_delete(request, slug):
    post = get_object_or_404(BlogPost, slug=slug)
    if request.method == 'POST':
        post.delete()
        messages.success(request, 'Blog post deleted successfully.')
        return redirect('blog_list')
    return render(request, 'blog_confirm_delete.html', {'post': post})

class SecurityViewMixin:
    """
    Mixin to add security features to views.
    """
    def dispatch(self, request, *args, **kwargs):
        # Add request ID for tracking
        request.request_id = str(uuid.uuid4())
        
        # Log request
        if request.user.is_authenticated:
            log_security_event(
                'view_access',
                request.user,
                get_client_ip(request),
                {
                    'method': request.method,
                    'path': request.path,
                    'request_id': request.request_id
                },
                level='info'
            )
        
        try:
            response = super().dispatch(request, *args, **kwargs)
            
            # Add security headers
            response['X-Content-Type-Options'] = 'nosniff'
            response['X-Frame-Options'] = 'DENY'
            response['X-XSS-Protection'] = '1; mode=block'
            response['Referrer-Policy'] = 'same-origin'
            response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
            
            return response
            
        except PermissionDenied as e:
            log_security_event(
                'permission_denied',
                request.user if request.user.is_authenticated else None,
                get_client_ip(request),
                {
                    'method': request.method,
                    'path': request.path,
                    'reason': str(e),
                    'request_id': request.request_id
                },
                level='warning'
            )
            return HttpResponseForbidden(_('Permission denied.'))
            
        except Http404 as e:
            log_security_event(
                'not_found',
                request.user if request.user.is_authenticated else None,
                get_client_ip(request),
                {
                    'method': request.method,
                    'path': request.path,
                    'request_id': request.request_id
                },
                level='warning'
            )
            raise
            
        except Exception as e:
            logger.exception("Unhandled exception in view")
            log_security_event(
                'error',
                request.user if request.user.is_authenticated else None,
                get_client_ip(request),
                {
                    'method': request.method,
                    'path': request.path,
                    'error': str(e),
                    'request_id': request.request_id
                },
                level='error'
            )
            return HttpResponseServerError(_('An error occurred. Please try again later.'))

class SecureView(SecurityViewMixin, View):
    """
    Base view class with security features.
    """
    permission_required = None
    login_url = '/login/'
    
    def get_permission_required(self):
        """
        Override this method to override the permission_required attribute.
        """
        return self.permission_required
    
    def has_permission(self):
        """
        Override this method to customize permission checks.
        """
        if not self.request.user.is_authenticated:
            return False
            
        if not self.request.user.is_active:
            return False
            
        if hasattr(self.request.user, 'casino_profile'):
            if not self.request.user.casino_profile.is_approved:
                return False
                
        permission_required = self.get_permission_required()
        if permission_required:
            return self.request.user.has_perm(permission_required)
            
        return True
    
    def handle_no_permission(self):
        """
        Override this method to customize the response when permission is denied.
        """
        if not self.request.user.is_authenticated:
            return redirect_to_login(self.request.get_full_path(), self.login_url)
            
        log_security_event(
            'permission_denied',
            self.request.user,
            get_client_ip(self.request),
            {
                'method': self.request.method,
                'path': self.request.path,
                'permission': self.get_permission_required()
            },
            level='warning'
        )
        return HttpResponseForbidden(_('Permission denied.'))
    
    def dispatch(self, request, *args, **kwargs):
        if not self.has_permission():
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)

class SecureLoginRequiredMixin(LoginRequiredMixin, SecurityViewMixin):
    """
    Mixin to require login and add security features.
    """
    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect_to_login(self.request.get_full_path(), self.login_url)
            
        if not self.request.user.is_active:
            log_security_event(
                'permission_denied',
                self.request.user,
                get_client_ip(self.request),
                {'reason': 'account_inactive'},
                level='warning'
            )
            return HttpResponseForbidden(_('Your account is inactive.'))
            
        if hasattr(self.request.user, 'casino_profile'):
            if not self.request.user.casino_profile.is_approved:
                log_security_event(
                    'permission_denied',
                    self.request.user,
                    get_client_ip(self.request),
                    {'reason': 'not_approved'},
                    level='warning'
                )
                return HttpResponseForbidden(_('Your account is pending approval.'))
                
        return super().handle_no_permission()

class SecureUserPassesTestMixin(UserPassesTestMixin, SecurityViewMixin):
    """
    Mixin to require user to pass a test and add security features.
    """
    def handle_no_permission(self):
        log_security_event(
            'permission_denied',
            self.request.user,
            get_client_ip(self.request),
            {'reason': 'test_failed'},
            level='warning'
        )
        return HttpResponseForbidden(_('Permission denied.'))

class SecureViewSet(viewsets.ModelViewSet):
    """
    Base viewset with security features.
    """
    permission_classes = [IsAuthenticated, IsVerifiedUser, IsNotLocked, IsOwnerOrAdmin]
    
    def get_permissions(self):
        """
        Get the appropriate permission classes for the current action.
        """
        permission_classes = get_permission_classes(self.action)
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """
        Filter queryset based on user permissions.
        """
        queryset = super().get_queryset()
        
        # Superusers can see everything
        if self.request.user.is_superuser:
            return queryset
            
        # Staff users can see everything in their scope
        if self.request.user.is_staff:
            return queryset
            
        # Regular users can only see their own data
        if hasattr(queryset.model, 'get_owner'):
            owner_field = queryset.model.get_owner()
            return queryset.filter(**{owner_field: self.request.user})
        elif hasattr(queryset.model, 'created_by'):
            return queryset.filter(created_by=self.request.user)
        elif hasattr(queryset.model, 'author'):
            return queryset.filter(author=self.request.user)
        elif hasattr(queryset.model, 'user'):
            return queryset.filter(user=self.request.user)
            
        return queryset.none()
    
    def perform_create(self, serializer):
        """
        Set the owner when creating an object.
        """
        if hasattr(serializer.Meta.model, 'created_by'):
            serializer.save(created_by=self.request.user)
        elif hasattr(serializer.Meta.model, 'author'):
            serializer.save(author=self.request.user)
        elif hasattr(serializer.Meta.model, 'user'):
            serializer.save(user=self.request.user)
        else:
            serializer.save()
    
    def handle_exception(self, exc):
        """
        Handle exceptions with proper logging.
        """
        if isinstance(exc, PermissionDenied):
            log_security_event(
                'permission_denied',
                self.request.user,
                get_client_ip(self.request),
                {
                    'method': self.request.method,
                    'path': self.request.path,
                    'action': self.action
                },
                level='warning'
            )
        elif isinstance(exc, Http404):
            log_security_event(
                'not_found',
                self.request.user,
                get_client_ip(self.request),
                {
                    'method': self.request.method,
                    'path': self.request.path,
                    'action': self.action
                },
                level='warning'
            )
        else:
            logger.exception("Unhandled exception in viewset")
            log_security_event(
                'error',
                self.request.user,
                get_client_ip(self.request),
                {
                    'method': self.request.method,
                    'path': self.request.path,
                    'action': self.action,
                    'error': str(exc)
                },
                level='error'
            )
            
        return super().handle_exception(exc)

def ratelimit_view(request, exception):
    """
    Custom rate limit handler.
    """
    log_security_event(
        'rate_limit_exceeded',
        request.user if request.user.is_authenticated else None,
        get_client_ip(request),
        {
            'method': request.method,
            'path': request.path
        },
        level='warning'
    )
    return render(request, '429.html', status=429)

def terms_page(request):
    """
    Public terms of service page view
    """
    context = {
        "current_date": timezone.now(),
        "site_settings": SiteSettings.objects.first(),
    }
    return render(request, "terms.html", context)

def privacy_page(request):
    """
    Public privacy policy page view
    """
    context = {
        "current_date": timezone.now(),
        "site_settings": SiteSettings.objects.first(),
    }
    return render(request, "privacy.html", context)

@login_required
def user_dashboard(request):
    # Get user's casino user profile
    try:
        casino_user = CasinoUser.objects.get(user=request.user)
    except CasinoUser.DoesNotExist:
        casino_user = None
    
    # Get user's click history
    click_history = CardClick.objects.filter(user=request.user).order_by('-click_date', '-click_time')[:10]
    
    # Get total clicks
    total_clicks = CardClick.objects.filter(user=request.user).count()
    
    # Get recent blog posts
    recent_posts = BlogPost.objects.filter(published=True).order_by('-published_at')[:3]
    
    context = {
        'casino_user': casino_user,
        'click_history': click_history,
        'total_clicks': total_clicks,
        'recent_posts': recent_posts,
    }
    return render(request, 'user_dashboard.html', context)

@login_required
def user_profile(request):
    try:
        casino_user = CasinoUser.objects.get(user=request.user)
    except CasinoUser.DoesNotExist:
        casino_user = None
    
    if request.method == 'POST':
        # Handle profile update
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        
        if first_name and last_name and email:
            request.user.first_name = first_name
            request.user.last_name = last_name
            request.user.email = email
            request.user.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('user_profile')
    
    context = {
        'casino_user': casino_user,
    }
    return render(request, 'user_profile.html', context)

@login_required
def user_clicks(request):
    # Get user's click history with pagination
    clicks = CardClick.objects.filter(user=request.user).order_by('-click_date', '-click_time')
    paginator = Paginator(clicks, 20)  # Show 20 clicks per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get click statistics
    total_clicks = clicks.count()
    today_clicks = clicks.filter(click_date=now().date()).count()
    this_week_clicks = clicks.filter(click_date__gte=now().date() - timedelta(days=7)).count()
    
    context = {
        'page_obj': page_obj,
        'total_clicks': total_clicks,
        'today_clicks': today_clicks,
        'this_week_clicks': this_week_clicks,
    }
    return render(request, 'user_clicks.html', context)

def custom_csrf_failure(request, reason=""):
    return render(request, 'csrf_failure.html', {
        'title': 'CSRF Verification Failed',
        'reason': reason
    })
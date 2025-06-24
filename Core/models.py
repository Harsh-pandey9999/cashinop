from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid
from django.utils.text import slugify
from django.urls import reverse
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import Group, Permission
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from django.conf import settings
from django.core.exceptions import ValidationError

User = get_user_model()



class CasinoUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='casino_profile')
    username = models.TextField(unique=True,blank=False)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    failed_login_attempts = models.IntegerField(default=0)
    last_failed_login = models.DateTimeField(null=True, blank=True)

    class Meta:
        permissions = [
            ('can_approve_user', 'Can approve casino users'),
            ('can_view_user_details', 'Can view user details'),
            ('can_manage_user', 'Can manage casino users'),
        ]

    def __str__(self) :
        return self.user.username 

    def get_owner(self):
        return self.user

    def save(self, *args, **kwargs):
        if not self.pk:  # New instance
            # Create user group if it doesn't exist
            user_group, _ = Group.objects.get_or_create(name='casino_user')
            self.user.groups.add(user_group)
        super().save(*args, **kwargs)

@receiver(post_save, sender=User)
def create_casino_user(sender, instance, created, **kwargs):
    if created:
        # Generate a unique username by appending a number if needed
        base_username = instance.username
        username = base_username
        counter = 1
        
        # Check if username already exists and make it unique if needed
        while CasinoUser.objects.filter(username=username).exists():
            username = f"{base_username}_{counter}"
            counter += 1
            
        # Create the CasinoUser with the unique username
        CasinoUser.objects.create(user=instance, username=username)

class GameCards(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=False, db_index=True)
    image = models.ImageField(upload_to='cards_images', blank=False)
    title = models.CharField(max_length=20, blank=False, db_index=True)
    description = models.CharField(max_length=200, blank=True)
    redirect_link = models.URLField(max_length=200, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_cards', db_index=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='approved_cards', db_index=True)
    approved_at = models.DateTimeField(null=True, blank=True, db_index=True)
    slug = models.SlugField(max_length=50, unique=True, blank=True)

    class Meta:
        permissions = [
            ('can_approve_card', 'Can approve game cards'),
            ('can_manage_cards', 'Can manage game cards'),
            ('can_view_card_stats', 'Can view card statistics'),
        ]
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['active', 'approved_at']),
            models.Index(fields=['created_by', 'created_at']),
            models.Index(fields=['approved_by', 'approved_at']),
        ]
        verbose_name = "Game Card"
        verbose_name_plural = "Game Cards"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        if self.active and not self.approved_at:
            self.approved_at = timezone.now()
        super().save(*args, **kwargs)
        cache.delete(f'gamecard_{self.id}')
        cache.delete('gamecards_active_list')

    def get_absolute_url(self):
        return reverse('gamecard_detail', kwargs={'slug': self.slug})

    @classmethod
    def get_active_cards(cls):
        cache_key = 'gamecards_active_list'
        cards = cache.get(cache_key)
        if cards is None:
            cards = list(cls.objects.filter(active=True).select_related(
                'created_by', 'approved_by'
            ).order_by('-created_at'))
            cache.set(cache_key, cards, timeout=3600)
        return cards

# contact model 

class Contact(models.Model):
    email = models.EmailField(max_length=254, db_index=True)
    phone = models.CharField(max_length=20, db_index=True)
    address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_contacts', db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name = "Contact"
        verbose_name_plural = "Contact Info"
        permissions = [
            ('can_manage_contact', 'Can manage contact information'),
        ]
        indexes = [
            models.Index(fields=['is_active', 'created_at']),
        ]

    def __str__(self):
        return f"Contact Info - {self.email}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        cache.delete('contact_info')

    @classmethod
    def get_active_contact(cls):
        cache_key = 'contact_info'
        contact = cache.get(cache_key)
        if contact is None:
            contact = cls.objects.filter(is_active=True).first()
            if contact:
                cache.set(cache_key, contact, timeout=3600)
        return contact

# about model 

class About(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200, default="About Us", db_index=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_about_sections', db_index=True)
    is_published = models.BooleanField(default=False, db_index=True)
    published_at = models.DateTimeField(null=True, blank=True, db_index=True)
    slug = models.SlugField(max_length=200, unique=True, blank=True)

    class Meta:
        verbose_name = "About Section"
        verbose_name_plural = "About Sections"
        permissions = [
            ('can_publish_about', 'Can publish about sections'),
            ('can_manage_about', 'Can manage about sections'),
        ]
        indexes = [
            models.Index(fields=['is_published', 'published_at']),
            models.Index(fields=['created_by', 'created_at']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        if self.is_published and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)
        cache.delete(f'about_{self.id}')
        cache.delete('about_published_list')

    def get_absolute_url(self):
        return reverse('about_detail', kwargs={'slug': self.slug})

    @classmethod
    def get_published_about(cls):
        cache_key = 'about_published_list'
        about_sections = cache.get(cache_key)
        if about_sections is None:
            about_sections = list(cls.objects.filter(
                is_published=True
            ).select_related('created_by').order_by('-published_at'))
            cache.set(cache_key, about_sections, timeout=3600)
        return about_sections

# Site_setting model


class SiteSettings(models.Model):
    site_name = models.CharField(max_length=100, default="Casino Site")
    description = models.TextField(blank=True)
    footer_text = models.TextField(blank=True)
    copyright_text = models.CharField(max_length=200, default="© 2024 Casino Site. All rights reserved.")
    
    # Social Media Links
    facebook_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    youtube_url = models.URLField(blank=True)
    telegram_url = models.URLField(blank=True)
    
    # Contact Information
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    contact_address = models.TextField(blank=True)
    
    # SEO Settings
    meta_keywords = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(blank=True)
    google_analytics_id = models.CharField(max_length=50, blank=True)
    
    # Media Files
    site_logo = models.ImageField(upload_to='site/', null=True, blank=True, help_text="Recommended size: 200x50 pixels")
    favicon = models.ImageField(upload_to='site/', null=True, blank=True, help_text="Recommended size: 32x32 pixels")
    
    # Additional Settings
    maintenance_mode = models.BooleanField(default=False)
    allow_registration = models.BooleanField(default=True)
    require_email_verification = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Site Settings"
        verbose_name_plural = "Site Settings"
    
    def __str__(self):
        return self.site_name
    
    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        if not self.pk and SiteSettings.objects.exists():
            raise ValidationError('There can be only one SiteSettings instance')
        super().save(*args, **kwargs)
    
    @classmethod
    def get_settings(cls):
        settings, created = cls.objects.get_or_create(pk=1)
        return settings

class PageVisit(models.Model):
    page_url = models.CharField(max_length=255, db_index=True)
    visit_date = models.DateField(auto_now_add=True, db_index=True)
    visit_time = models.TimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True, db_index=True)
    user_agent = models.TextField(blank=True, null=True)
    referrer = models.URLField(blank=True, null=True)
    is_unique = models.BooleanField(default=True, db_index=True)
    session_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    
    class Meta:
        verbose_name = "Page Visit"
        verbose_name_plural = "Page Visits"
        permissions = [
            ('can_view_analytics', 'Can view page analytics'),
            ('can_export_analytics', 'Can export page analytics'),
        ]
        indexes = [
            models.Index(fields=['visit_date', 'page_url']),
            models.Index(fields=['ip_address', 'visit_date']),
            models.Index(fields=['session_id', 'visit_date']),
        ]
    
    def __str__(self):
        return f"{self.page_url} - {self.visit_date}"

    @classmethod
    def get_visit_stats(cls, days=30):
        cache_key = f'visit_stats_{days}'
        stats = cache.get(cache_key)
        if stats is None:
            stats = cls.objects.filter(
                visit_date__gte=timezone.now().date() - timezone.timedelta(days=days)
            ).values('visit_date').annotate(
                total_visits=models.Count('id'),
                unique_visits=models.Count('id', filter=models.Q(is_unique=True))
            ).order_by('visit_date')
            cache.set(cache_key, list(stats), timeout=3600)
        return stats

class CardClick(models.Model):
    card = models.ForeignKey(GameCards, on_delete=models.CASCADE, related_name='clicks', db_index=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='card_clicks', db_index=True)
    click_date = models.DateField(auto_now_add=True, db_index=True)
    click_time = models.TimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True, db_index=True)
    user_agent = models.TextField(blank=True, null=True)
    referrer = models.URLField(blank=True, null=True)
    session_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    
    class Meta:
        verbose_name = "Card Click"
        verbose_name_plural = "Card Clicks"
        permissions = [
            ('can_view_clicks', 'Can view card clicks'),
            ('can_export_clicks', 'Can export card clicks'),
        ]
        indexes = [
            models.Index(fields=['click_date', 'card']),
            models.Index(fields=['user', 'click_date']),
            models.Index(fields=['ip_address', 'click_date']),
            models.Index(fields=['session_id', 'click_date']),
        ]
    
    def __str__(self):
        return f"{self.card.title} - {self.click_date}"

    @classmethod
    def get_click_stats(cls, card_id=None, days=30):
        cache_key = f'click_stats_{card_id}_{days}'
        stats = cache.get(cache_key)
        if stats is None:
            queryset = cls.objects.filter(
                click_date__gte=timezone.now().date() - timezone.timedelta(days=days)
            )
            if card_id:
                queryset = queryset.filter(card_id=card_id)
            stats = queryset.values('click_date').annotate(
                total_clicks=models.Count('id'),
                unique_clicks=models.Count('session_id', distinct=True)
            ).order_by('click_date')
            cache.set(cache_key, list(stats), timeout=3600)
        return stats

class AdminActivity(models.Model):
    ACTIVITY_TYPES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('approve', 'Approve'),
        ('other', 'Other'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES, db_index=True)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(blank=True, null=True, db_index=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    related_model = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    object_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    
    class Meta:
        verbose_name = "Admin Activity"
        verbose_name_plural = "Admin Activities"
        permissions = [
            ('can_view_activity', 'Can view admin activity'),
            ('can_export_activity', 'Can export admin activity'),
        ]
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'activity_type', 'timestamp']),
            models.Index(fields=['related_model', 'object_id']),
            models.Index(fields=['ip_address', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.activity_type} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

    @classmethod
    def get_recent_activity(cls, limit=50):
        cache_key = f'recent_admin_activity_{limit}'
        activities = cache.get(cache_key)
        if activities is None:
            activities = list(cls.objects.select_related('user').order_by('-timestamp')[:limit])
            cache.set(cache_key, activities, timeout=300)
        return activities

class SystemNotification(models.Model):
    NOTIFICATION_TYPES = [
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('success', 'Success'),
    ]
    
    title = models.CharField(max_length=100, db_index=True)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='info', db_index=True)
    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    expires_at = models.DateTimeField(blank=True, null=True, db_index=True)
    for_all_admins = models.BooleanField(default=True, db_index=True)
    target_admin = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, db_index=True)
    
    class Meta:
        verbose_name = "System Notification"
        verbose_name_plural = "System Notifications"
        permissions = [
            ('can_manage_notifications', 'Can manage system notifications'),
            ('can_view_notifications', 'Can view system notifications'),
        ]
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['notification_type', 'is_read']),
            models.Index(fields=['for_all_admins', 'created_at']),
            models.Index(fields=['target_admin', 'is_read']),
            models.Index(fields=['expires_at', 'is_read']),
        ]

    def __str__(self):
        return self.title
    
    @property
    def is_expired(self):
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        cache.delete('notifications_all')
        if self.target_admin:
            cache.delete(f'notifications_user_{self.target_admin.id}')

    @classmethod
    def get_active_notifications(cls, user=None):
        if user:
            cache_key = f'notifications_user_{user.id}'
        else:
            cache_key = 'notifications_all'
        
        notifications = cache.get(cache_key)
        if notifications is None:
            queryset = cls.objects.filter(
                is_read=False,
                expires_at__gt=timezone.now()
            )
            if user:
                queryset = queryset.filter(
                    models.Q(for_all_admins=True) | models.Q(target_admin=user)
                )
            notifications = list(queryset.order_by('-created_at'))
            cache.set(cache_key, notifications, timeout=300)
        return notifications

class SystemLog(models.Model):
    LOG_LEVELS = (
        ('INFO', 'Information'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('SUCCESS', 'Success'),
    )

    ACTION_TYPES = (
        ('LOGIN', 'User Login'),
        ('LOGOUT', 'User Logout'),
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('APPROVE', 'Approve'),
        ('REJECT', 'Reject'),
        ('SETTINGS', 'Settings Change'),
        ('SYSTEM', 'System Event'),
    )

    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    level = models.CharField(max_length=10, choices=LOG_LEVELS, default='INFO', db_index=True)
    action = models.CharField(max_length=10, choices=ACTION_TYPES, db_index=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True, db_index=True)
    message = models.TextField()
    details = models.JSONField(null=True, blank=True)
    affected_model = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    affected_id = models.CharField(max_length=100, null=True, blank=True, db_index=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'System Log'
        verbose_name_plural = 'System Logs'
        permissions = [
            ('can_view_logs', 'Can view system logs'),
            ('can_export_logs', 'Can export system logs'),
            ('can_manage_logs', 'Can manage system logs'),
        ]
        indexes = [
            models.Index(fields=['level', 'action', 'timestamp']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['affected_model', 'affected_id']),
            models.Index(fields=['ip_address', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.get_level_display()} - {self.get_action_display()} - {self.message[:50]}"

    @classmethod
    def log(cls, level, action, message, user=None, ip_address=None, details=None, affected_model=None, affected_id=None):
        log_entry = cls.objects.create(
            level=level,
            action=action,
            message=message,
            user=user,
            ip_address=ip_address,
            details=details,
            affected_model=affected_model,
            affected_id=str(affected_id) if affected_id else None
        )
        cache.delete('system_logs_recent')
        return log_entry

    @classmethod
    def get_recent_logs(cls, limit=100):
        cache_key = 'system_logs_recent'
        logs = cache.get(cache_key)
        if logs is None:
            logs = list(cls.objects.select_related('user').order_by('-timestamp')[:limit])
            cache.set(cache_key, logs, timeout=300)
        return logs

class BlogPost(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(max_length=200, unique=True, db_index=True)
    content = models.TextField()
    featured_image = models.ImageField(upload_to='blog_images/', null=True, blank=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blog_posts', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    published = models.BooleanField(default=False, db_index=True)
    published_at = models.DateTimeField(null=True, blank=True, db_index=True)
    last_modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='modified_posts', db_index=True)
    is_featured = models.BooleanField(default=False, db_index=True)
    meta_description = models.CharField(max_length=160, blank=True)
    meta_keywords = models.CharField(max_length=200, blank=True)
    view_count = models.PositiveIntegerField(default=0, db_index=True)

    class Meta:
        verbose_name = "Blog Post"
        verbose_name_plural = "Blog Posts"
        permissions = [
            ('can_publish_post', 'Can publish blog posts'),
            ('can_feature_post', 'Can feature blog posts'),
            ('can_manage_posts', 'Can manage blog posts'),
        ]
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['published', 'published_at']),
            models.Index(fields=['author', 'created_at']),
            models.Index(fields=['is_featured', 'published']),
            models.Index(fields=['view_count', 'published']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        if self.published and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)
        cache.delete(f'blogpost_{self.id}')
        cache.delete('blogposts_published_list')
        cache.delete('blogposts_featured_list')

    def get_absolute_url(self):
        return reverse('blog_detail', kwargs={'slug': self.slug})

    def increment_view_count(self):
        cache_key = f'blogpost_views_{self.id}'
        current_views = cache.get(cache_key, self.view_count)
        new_views = current_views + 1
        cache.set(cache_key, new_views, timeout=3600)
        
        if new_views % 5 == 0:
            self.view_count = new_views
            self.save(update_fields=['view_count'])

    @classmethod
    def get_published_posts(cls, limit=None):
        cache_key = f'blogposts_published_list_{limit}'
        posts = cache.get(cache_key)
        if posts is None:
            queryset = cls.objects.filter(published=True).select_related(
                'author', 'last_modified_by'
            ).order_by('-published_at')
            if limit:
                queryset = queryset[:limit]
            posts = list(queryset)
            cache.set(cache_key, posts, timeout=3600)
        return posts

    @classmethod
    def get_featured_posts(cls, limit=5):
        cache_key = f'blogposts_featured_list_{limit}'
        posts = cache.get(cache_key)
        if posts is None:
            posts = list(cls.objects.filter(
                published=True, is_featured=True
            ).select_related('author').order_by('-published_at')[:limit])
            cache.set(cache_key, posts, timeout=3600)
        return posts

@receiver([post_save, post_delete], sender=GameCards)
def clear_gamecard_cache(sender, instance, **kwargs):
    cache.delete(f'gamecard_{instance.id}')
    cache.delete('gamecards_active_list')

@receiver([post_save, post_delete], sender=BlogPost)
def clear_blogpost_cache(sender, instance, **kwargs):
    cache.delete(f'blogpost_{instance.id}')
    cache.delete('blogposts_published_list')
    cache.delete('blogposts_featured_list')

@receiver([post_save, post_delete], sender=SystemNotification)
def clear_notification_cache(sender, instance, **kwargs):
    cache.delete('notifications_all')
    if instance.target_admin:
        cache.delete(f'notifications_user_{instance.target_admin.id}')

@receiver([post_save, post_delete], sender=SystemLog)
def clear_systemlog_cache(sender, instance, **kwargs):
    cache.delete('system_logs_recent')

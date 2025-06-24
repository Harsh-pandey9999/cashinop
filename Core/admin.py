from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from import_export.admin import ImportExportModelAdmin
from rangefilter.filters import DateRangeFilter

from .models import (
    CasinoUser, 
    GameCards, 
    Contact, 
    About, 
    SiteSettings,
    PageVisit, 
    CardClick, 
    AdminActivity, 
    SystemNotification,
    SystemLog,
    BlogPost
)
from .forms import BlogPostForm

# Extend User Admin
class CasinoUserInline(admin.StackedInline):
    model = CasinoUser
    can_delete = False
    verbose_name_plural = 'Casino User Profile'

class UserAdmin(BaseUserAdmin):
    inlines = (CasinoUserInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'date_joined', 'get_approval_status')
    list_filter = ('is_staff', 'is_active', 'date_joined', ('date_joined', DateRangeFilter))
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    actions = ['approve_users', 'deactivate_users', 'activate_users']
    
    def get_approval_status(self, obj):
        try:
            casino_user = CasinoUser.objects.get(user=obj)
            if casino_user.is_approved:
                return format_html('<span style="color: green;">Approved</span>')
            return format_html('<span style="color: red;">Pending</span>')
        except CasinoUser.DoesNotExist:
            return format_html('<span style="color: gray;">No Profile</span>')
    get_approval_status.short_description = 'Approval Status'
    
    def approve_users(self, request, queryset):
        for user in queryset:
            try:
                casino_user = CasinoUser.objects.get(user=user)
                casino_user.is_approved = True
                casino_user.save()
                
                # Log admin activity
                AdminActivity.objects.create(
                    user=request.user,
                    activity_type='approve',
                    description=f'Approved user: {user.username}',
                    related_model='User',
                    object_id=str(user.id)
                )
            except CasinoUser.DoesNotExist:
                pass
        self.message_user(request, f"{queryset.count()} users were successfully approved.")
    approve_users.short_description = "Approve selected users"
    
    def deactivate_users(self, request, queryset):
        queryset.update(is_active=False)
        for user in queryset:
            AdminActivity.objects.create(
                user=request.user,
                activity_type='update',
                description=f'Deactivated user: {user.username}',
                related_model='User',
                object_id=str(user.id)
            )
        self.message_user(request, f"{queryset.count()} users were successfully deactivated.")
    deactivate_users.short_description = "Deactivate selected users"
    
    def activate_users(self, request, queryset):
        queryset.update(is_active=True)
        for user in queryset:
            AdminActivity.objects.create(
                user=request.user,
                activity_type='update',
                description=f'Activated user: {user.username}',
                related_model='User',
                object_id=str(user.id)
            )
        self.message_user(request, f"{queryset.count()} users were successfully activated.")
    activate_users.short_description = "Activate selected users"

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

@admin.register(CasinoUser)
class CasinoUserAdmin(admin.ModelAdmin):
    list_display = ('user__username', 'user__email', 'user__first_name', 'user__last_name', 'is_approved', 'user__is_active', 'user__date_joined')
    list_filter = ('is_approved', 'user__is_active', 'user__date_joined')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    ordering = ('-user__date_joined',)
    actions = ['approve_users', 'deactivate_users']
    
    def user__username(self, obj):
        return obj.user.username
    user__username.short_description = 'Username'
    user__username.admin_order_field = 'user__username'

    def user__email(self, obj):
        return obj.user.email
    user__email.short_description = 'Email'
    user__email.admin_order_field = 'user__email'

    def user__first_name(self, obj):
        return obj.user.first_name
    user__first_name.short_description = 'First Name'
    user__first_name.admin_order_field = 'user__first_name'

    def user__last_name(self, obj):
        return obj.user.last_name
    user__last_name.short_description = 'Last Name'
    user__last_name.admin_order_field = 'user__last_name'

    def user__is_active(self, obj):
        return obj.user.is_active
    user__is_active.short_description = 'Active'
    user__is_active.boolean = True
    user__is_active.admin_order_field = 'user__is_active'

    def user__date_joined(self, obj):
        return obj.user.date_joined
    user__date_joined.short_description = 'Date Joined'
    user__date_joined.admin_order_field = 'user__date_joined'

    def approve_users(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f"{updated} users have been approved.")
    approve_users.short_description = "Approve selected users"

    def deactivate_users(self, request, queryset):
        updated = queryset.update(user__is_active=False)
        self.message_user(request, f"{updated} users have been deactivated.")
    deactivate_users.short_description = "Deactivate selected users"

@admin.register(GameCards)
class GameCardsAdmin(ImportExportModelAdmin):
    list_display = ('title', 'active', 'created_at', 'get_image_preview', 'get_click_count')
    list_filter = ('active', 'created_at')
    search_fields = ('title', 'description')
    readonly_fields = ('id', 'created_at', 'get_image_preview', 'get_click_count')
    actions = ['activate_cards', 'deactivate_cards']
    
    def get_image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover;" />', obj.image.url)
        return "-"
    get_image_preview.short_description = 'Image Preview'
    
    def get_click_count(self, obj):
        count = CardClick.objects.filter(card=obj).count()
        return count
    get_click_count.short_description = 'Clicks'
    
    def activate_cards(self, request, queryset):
        queryset.update(active=True)
        for obj in queryset:
            AdminActivity.objects.create(
                user=request.user,
                activity_type='update',
                description=f'Activated card: {obj.title}',
                related_model='GameCards',
                object_id=str(obj.id)
            )
        self.message_user(request, f"{queryset.count()} cards were successfully activated.")
    activate_cards.short_description = "Activate selected cards"
    
    def deactivate_cards(self, request, queryset):
        queryset.update(active=False)
        for obj in queryset:
            AdminActivity.objects.create(
                user=request.user,
                activity_type='update',
                description=f'Deactivated card: {obj.title}',
                related_model='GameCards',
                object_id=str(obj.id)
            )
        self.message_user(request, f"{queryset.count()} cards were successfully deactivated.")
    deactivate_cards.short_description = "Deactivate selected cards"

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('email', 'phone', 'is_active', 'created_at', 'updated_at', 'created_by')
    search_fields = ('email', 'phone', 'address')
    list_filter = ('is_active', 'created_at')
    readonly_fields = ('created_at', 'updated_at', 'created_by')
    fieldsets = (
        (None, {
            'fields': ('email', 'phone', 'address', 'is_active')
        }),
        ('Advanced options', {
            'classes': ('collapse',),
            'fields': ('created_by', 'created_at', 'updated_at'),
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:  # New instance
            obj.created_by = request.user
        obj.save()
        
    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('Core.can_manage_contact')
        
    def has_add_permission(self, request):
        return request.user.has_perm('Core.can_manage_contact')
        
    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('Core.can_manage_contact')
        
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing an existing object
            return self.readonly_fields + ('created_by',)
        return self.readonly_fields

@admin.register(About)
class AboutAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_published', 'created_at', 'updated_at', 'created_by', 'published_at', 'slug')
    search_fields = ('title', 'content')
    list_filter = ('is_published', 'created_at')
    readonly_fields = ('created_at', 'updated_at', 'slug', 'created_by')
    fieldsets = (
        (None, {
            'fields': ('title', 'content', 'is_published')
        }),
        ('Advanced options', {
            'classes': ('collapse',),
            'fields': ('slug', 'created_by', 'published_at', 'created_at', 'updated_at'),
        }),
    )
    ordering = ('-created_at',)
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:  # New instance
            obj.created_by = request.user
        if 'is_published' in form.changed_data and obj.is_published and not obj.published_at:
            obj.published_at = timezone.now()
        obj.save()
        
    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('Core.can_manage_about')
        
    def has_add_permission(self, request):
        return request.user.has_perm('Core.can_manage_about')
        
    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('Core.can_manage_about')
        
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing an existing object
            return self.readonly_fields + ('created_by',)
        return self.readonly_fields

@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Basic Information', {
            'fields': ('site_name', 'description', 'footer_text', 'copyright_text')
        }),
        ('Media Files', {
            'fields': ('site_logo', 'favicon'),
            'classes': ('wide',),
            'description': 'Upload your site logo and favicon here. Logo should be 200x50 pixels, favicon should be 32x32 pixels.'
        }),
        ('Contact Information', {
            'fields': ('contact_email', 'contact_phone', 'contact_address')
        }),
        ('Social Media Links', {
            'fields': ('facebook_url', 'twitter_url', 'instagram_url', 'linkedin_url', 'youtube_url', 'telegram_url')
        }),
        ('SEO Settings', {
            'fields': ('meta_keywords', 'meta_description', 'google_analytics_id')
        }),
        ('Additional Settings', {
            'fields': ('maintenance_mode', 'allow_registration', 'require_email_verification')
        }),
    )
    
    def has_add_permission(self, request):
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)
    
    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(PageVisit)
class PageVisitAdmin(admin.ModelAdmin):
    list_display = ('page_url', 'visit_date', 'visit_time', 'ip_address', 'user_agent', 'referrer', 'is_unique', 'session_id')
    search_fields = ('page_url', 'ip_address', 'user_agent')
    list_filter = ('visit_date', 'is_unique')
    readonly_fields = ('visit_date', 'visit_time')
    ordering = ('-visit_date',)
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False

@admin.register(CardClick)
class CardClickAdmin(admin.ModelAdmin):
    list_display = ('card', 'click_date', 'click_time', 'ip_address')
    list_filter = ('click_date', ('click_date', DateRangeFilter), 'card')
    search_fields = ('card__title', 'ip_address')
    readonly_fields = ('card', 'click_date', 'click_time', 'ip_address', 'user_agent', 'referrer')

@admin.register(AdminActivity)
class AdminActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'activity_type', 'description', 'timestamp', 'ip_address')
    list_filter = ('activity_type', 'timestamp', ('timestamp', DateRangeFilter), 'user')
    search_fields = ('user__username', 'description', 'related_model')
    readonly_fields = ('user', 'activity_type', 'description', 'timestamp', 'ip_address', 'related_model', 'object_id')

@admin.register(SystemNotification)
class SystemNotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'notification_type', 'is_read', 'created_at', 'expires_at')
    list_filter = ('notification_type', 'is_read', 'created_at', ('created_at', DateRangeFilter))
    search_fields = ('title', 'message')
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)
        self.message_user(request, f"{queryset.count()} notifications were marked as read.")
    mark_as_read.short_description = "Mark selected notifications as read"
    
    def mark_as_unread(self, request, queryset):
        queryset.update(is_read=False)
        self.message_user(request, f"{queryset.count()} notifications were marked as unread.")
    mark_as_unread.short_description = "Mark selected notifications as unread"

@admin.register(SystemLog)
class SystemLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'level', 'action', 'user', 'ip_address', 'message', 'affected_model', 'affected_id')
    search_fields = ('message', 'ip_address', 'level', 'action', 'user__username')
    list_filter = ('level', 'action', 'timestamp')
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False

@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    form = BlogPostForm
    list_display = ('title', 'author', 'created_at', 'updated_at', 'published', 'published_at', 'is_featured', 'view_count')
    search_fields = ('title', 'content', 'author__username')
    list_filter = ('published', 'created_at', 'is_featured')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'view_count')
    fieldsets = (
        ('Post Details', {
            'fields': ('title', 'slug', 'content', 'featured_image')
        }),
        ('Publication', {
            'fields': ('published', 'published_at', 'is_featured')
        }),
        ('SEO', {
            'classes': ('collapse',),
            'fields': ('meta_description', 'meta_keywords')
        }),
        ('Metadata', {
            'classes': ('collapse',),
            'fields': ('author', 'last_modified_by', 'created_at', 'updated_at', 'view_count')
        }),
    )
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['author'].initial = request.user
        return form
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:  # New post
            obj.author = request.user
        obj.last_modified_by = request.user
        super().save_model(request, obj, form, change)
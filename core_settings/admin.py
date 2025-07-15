from django.contrib import admin
from django.utils.html import format_html, mark_safe
from django.urls import reverse
from .models import SiteSettings, Contact

@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ('site_name',)
    
    def has_add_permission(self, request):
        # Only allow one instance
        return not SiteSettings.objects.exists()


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'status_badge', 'created_at', 'view_action')
    list_filter = ('status', 'created_at')
    search_fields = ('name', 'email', 'subject', 'message')
    date_hierarchy = 'created_at'
    list_per_page = 20
    readonly_fields = ('created_at', 'updated_at', 'ip_address')
    fieldsets = (
        ('Contact Information', {
            'fields': ('name', 'email', 'subject', 'message')
        }),
        ('Status', {
            'fields': ('status', 'ip_address')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def status_badge(self, obj):
        status_colors = {
            'new': 'blue',
            'in_progress': 'orange',
            'resolved': 'green',
            'spam': 'red',
        }
        return format_html(
            '<span style="color: white; background-color: {}; padding: 3px 8px; border-radius: 4px; font-size: 12px;">{}</span>',
            status_colors.get(obj.status, 'gray'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'status'

    def view_action(self, obj):
        url = reverse('admin:core_settings_contact_change', args=[obj.id])
        return mark_safe(f'<a class="button" href="{url}">View</a>&nbsp;')
    view_action.short_description = 'Actions'

    def has_add_permission(self, request):
        # Prevent adding contacts through admin
        return False

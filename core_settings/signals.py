from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .models import SiteSettings

@receiver(post_migrate)
def create_default_site_settings(sender, **kwargs):
    if not SiteSettings.objects.exists():
        SiteSettings.objects.create(site_name='Casino Admin')

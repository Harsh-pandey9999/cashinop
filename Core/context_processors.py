from .models import SiteSettings

def site_settings(request):
    """
    Context processor that makes site settings available in all templates.
    """
    return {
        'site_settings': SiteSettings.objects.first()
    }

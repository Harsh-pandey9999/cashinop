def site_settings(request):
    from .models import SiteSettings
    try:
        settings = SiteSettings.objects.first()
        if not settings:
            settings = SiteSettings.objects.create(site_name='Casino Admin')
    except:
        settings = None
    
    return {
        'site_settings': settings
    }

from django.contrib import admin
from django.contrib.admin import AdminSite

class CustomAdminSite(AdminSite):
    login_template = 'admin/login.html'

# Create an instance of our custom admin site
custom_admin_site = CustomAdminSite()

# Register all the models that were previously registered with the default admin site
for model, model_admin in admin.site._registry.items():
    custom_admin_site.register(model, model_admin.__class__)

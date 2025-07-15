from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

class SiteSettings(models.Model):
    site_name = models.CharField(max_length=100, default='Casino Admin')
    site_logo = models.ImageField(upload_to='site_logo/', blank=True, null=True)
    favicon = models.ImageField(upload_to='favicon/', blank=True, null=True)
    
    class Meta:
        verbose_name = _('Site Setting')
        verbose_name_plural = _('Site Settings')
    
    def __str__(self):
        return self.site_name
    
    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        if self.__class__.objects.count() > 1 and not self.pk:
            self.pk = 1
        super().save(*args, **kwargs)


class Contact(models.Model):
    STATUS_CHOICES = [
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('spam', 'Spam'),
    ]
    
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new',
        db_index=True
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Contact Form Submission'
        verbose_name_plural = 'Contact Form Submissions'
    
    def __str__(self):
        return f"{self.name} - {self.subject} ({self.get_status_display()})"

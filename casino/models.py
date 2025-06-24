from django.utils import timezone


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

    timestamp = models.DateTimeField(auto_now_add=True)
    level = models.CharField(max_length=10, choices=LOG_LEVELS, default='INFO')
    action = models.CharField(max_length=10, choices=ACTION_TYPES)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    message = models.TextField()
    details = models.JSONField(null=True, blank=True)
    affected_model = models.CharField(max_length=100, null=True, blank=True)
    affected_id = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'System Log'
        verbose_name_plural = 'System Logs'

    def __str__(self):
        return f"{self.get_level_display()} - {self.get_action_display()} - {self.message[:50]}"

    @classmethod
    def log(cls, level, action, message, user=None, ip_address=None, details=None, affected_model=None, affected_id=None):
        return cls.objects.create(
            level=level,
            action=action,
            message=message,
            user=user,
            ip_address=ip_address,
            details=details,
            affected_model=affected_model,
            affected_id=affected_id
        ) 
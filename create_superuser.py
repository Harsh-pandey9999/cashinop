import os
import django

def create_superuser():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Casino.settings')
    django.setup()
    
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    
    # Delete existing superuser if it exists
    User.objects.filter(username='admin').delete()
    
    # Create new superuser
    User.objects.create_superuser(
        username='admin',
        email='admin@gmail.com',
        password='root1234'
    )
    print("Superuser created successfully!")

if __name__ == '__main__':
    create_superuser()

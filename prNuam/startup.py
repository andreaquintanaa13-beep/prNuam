import os
import django
from django.contrib.auth import get_user_model

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prNuam.settings')
django.setup()

def create_superuser():
    User = get_user_model()
    
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser(
            username='admin',
            email='admin@prnuam.com',
            password='Admin123456!'
        )
        print('✅ Superusuario creado: admin / Admin123456!')
    else:
        print('✅ Superusuario ya existe')

# Ejecutar solo si es el proceso principal
if __name__ == '__main__':
    create_superuser()

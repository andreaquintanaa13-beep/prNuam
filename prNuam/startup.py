import os
from django.contrib.auth import get_user_model
from django.db.utils import OperationalError, ProgrammingError

def create_superuser():
    try:
        User = get_user_model()
        
        # Verificar si ya existe un superusuario
        if not User.objects.filter(is_superuser=True).exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@prnuam.com', 
                password='Admin123'  # ⚠️ CAMBIA ESTA CONTRASEÑA
            )
            print('✅ Superusuario creado: admin / Admin123456!')
        else:
            print('✅ Ya existe un superusuario')
            
    except (OperationalError, ProgrammingError) as e:
        print(f'⚠️ Error creando superusuario (puede ser normal en primer deploy): {e}')

# Ejecutar automáticamente en Render
if 'RENDER' in os.environ:
    create_superuser()
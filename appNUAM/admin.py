from django.contrib import admin
from .models import (
    Usuario, Factor, Permiso, UsuarioPermiso,
    Auditoria, Corredor, Calificacion,
    CalificacionFactor, Reporte, Archivocarga
)

admin.site.register(Usuario)
admin.site.register(Factor)
admin.site.register(Permiso)
admin.site.register(UsuarioPermiso)
admin.site.register(Auditoria)
admin.site.register(Corredor)
admin.site.register(Calificacion)
admin.site.register(CalificacionFactor)
admin.site.register(Reporte)
admin.site.register(Archivocarga)

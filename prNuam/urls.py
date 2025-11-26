from django.contrib import admin
from django.urls import path
from appNUAM import views
urlpatterns = [
    path('admin/', admin.site.urls),
    #-- iniciar sesion --
    path('', views.login, name='login'),
    path('registrarse/', views.registrarse, name="registrarse"),
    path("logout/", views.logout, name="logout"),
    #-- paneles --
    path('panel-admin/', views.perfil_administrador, name="perfil_administrador"),
    path('panel-usuario/', views.perfil_usuario, name="perfil_usuario"),
    #-- calificaciones
    path('calificaciones/', views.calificaciones_tributarias, name='calificaciones_tributarias'),
    path('agregar-calificacion/', views.agregar_calificacion, name='agregar_calificacion'),
    path('carga-masiva/', views.carga_masiva, name='carga_masiva'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('editar-calificacion/<int:id>/', views.editar_calificacion, name="editar_calificacion"),
    path('eliminar-calificacion/<int:id>/', views.eliminar_calificacion, name="eliminar_calificacion"),
    #path('dashboard-corredor/', views.dashboard_corredor, name='dashboard_corredor'),

    #-- administrador
    path('admin/usuarios/eliminar/<int:id>/', views.eliminar_usuario, name="eliminar_usuario"),
    path("editar-usuario/<int:id>/", views.editar_usuario, name="editar_usuario"),
    path("editar-usuario/<int:id>/", views.editar_usuario, name="editar_usuario"),
    path("eliminar-usuario/<int:id>/", views.eliminar_usuario, name="eliminar_usuario"),
    path('aprobar-usuario/<int:id>/', views.aprobar_usuario, name="aprobar_usuario"),



    #-- permisos
    path("permisos/", views.permisos, name="permisos"),
    path("permisos/editar/<int:id_permiso>/", views.editar_permiso, name="editar_permiso"),
    path("permisos/crear/", views.crear_permiso, name="crear_permiso"),

    #-- extras
    path('montos/', views.mantenedor_montos, name='mantenedor_montos'),
    path('factores/', views.mantenedor_factores, name='mantenedor_factores'),
    path('no-inscritas/', views.calificaciones_no_inscritas, name='calificaciones_no_inscritas'),
    path('carga-masiva/', views.carga_masiva, name='carga_masiva'),
    path('carga-externa/', views.carga_externa, name='carga_externa'),
    path('mis-calificaciones/', views.ver_mis_calificaciones, name='ver_mis_calificaciones'),

]


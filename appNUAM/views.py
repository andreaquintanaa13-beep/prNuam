from django.utils import timezone
from django.db.models import Q
import pandas as pd
import openpyxl
from django.contrib import messages
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from .decorators import administrador_required, corredor_required
from .models import Archivocarga, Permiso, Usuario, Corredor, Calificacion, Auditoria, Factor
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.models import User


# -- calificaciones
def calificaciones_tributarias(request):
    return render(request, 'template_calificaciones/template_calificaciones.html')

def agregar_calificacion(request):

    if "usuario_id" not in request.session:
        return redirect("login")

    usuario_id = request.session["usuario_id"]

    # Buscar corredor asociado
    try:
        corredor = Corredor.objects.get(fk_usuario_id=usuario_id)
    except Corredor.DoesNotExist:
        return redirect("perfil_administrador")

    # Si envían formulario
    if request.method == "POST":
        mercado = request.POST.get("mercado")
        descripcion = request.POST.get("descripcion")
        fecha = request.POST.get("fecha")
        ano = request.POST.get("ano")
        factor_actualizado = request.POST.get("factor_actualizado")

        # Crear registro SOLO con los campos existentes en el modelo
        Calificacion.objects.create(
            fecha=fecha,
            mercado=mercado,
            ano=ano,
            descripcion=descripcion,
            factor_actualizado=factor_actualizado,
            fk_id_corredor=corredor,
        )

        # Registrar auditoría
        registrar_auditoria(
            usuario_admin_id=usuario_id,
            accion="Crear calificación",
            resultado=f"Calificación agregada: {descripcion}"
        )

        return redirect("perfil_usuario")

    return render(request, 'template_calificaciones/template_agregarCalificacion.html')

def carga_masiva(request):
    mensaje = None

    if "usuario_id" not in request.session:
        return redirect("login")

    usuario = Usuario.objects.get(id_usuario=request.session["usuario_id"])

    if request.method == "POST":
        archivo = request.FILES.get("archivo")

        if not archivo:
            mensaje = "Debe seleccionar un archivo."
            return render(request, "carga_masiva.html", {"mensaje": mensaje})

        try:
            df = pd.read_excel(archivo)

            # Detectar qué tipo de archivo es por las columnas
            if "nombre_factor" in df.columns:
                tipo_archivo = "factor"
            elif "mercado" in df.columns:
                tipo_archivo = "calificacion"
            else:
                mensaje = "El archivo no contiene columnas válidas."
                return render(request, "carga_masiva.html", {"mensaje": mensaje})

            agregados = 0
            actualizados = 0

            if tipo_archivo == "factor":
                for _, fila in df.iterrows():
                    obj, creado = Factor.objects.update_or_create(
                        nombre_factor=fila["nombre_factor"],
                        defaults={
                            "valor_factor": fila["valor_factor"],
                            "fecha_inicio": fila["fecha_inicio"],
                            "fecha_fin": fila["fecha_fin"],
                        }
                    )
                    if creado:
                        agregados += 1
                    else:
                        actualizados += 1

            elif tipo_archivo == "calificacion":

                # Obtener el corredor relacionado al usuario
                corredor = Corredor.objects.get(fk_usuario=usuario)

                for _, fila in df.iterrows():
                    obj, creado = Calificacion.objects.update_or_create(
                        ano=fila["ano"],
                        mercado=fila["mercado"],
                        fk_id_corredor=corredor,
                        defaults={
                            "fecha": fila["fecha"],
                            "descripcion": fila.get("descripcion", "")
                        }
                    )
                    if creado:
                        agregados += 1
                    else:
                        actualizados += 1

            # Registrar archivo cargado
            Archivocarga.objects.create(
                tipo_archivo=tipo_archivo,
                fecha_carga=timezone.now(),
                estado="Procesado",
                archivo_url=archivo.name,
                fk_id_usuario=usuario
            )

            # Auditoría
            Auditoria.objects.create(
                accion="Carga Masiva",
                fecha_hora=timezone.now(),
                resultado=f"{agregados} agregados, {actualizados} actualizados",
                fk_usuario=usuario
            )

            mensaje = f"Carga OK. Agregados: {agregados}, Actualizados: {actualizados}"

        except Exception as e:
            mensaje = f"Error procesando archivo: {str(e)}"

    return render(request, "template_calificaciones/template_cargaCalificacion.html", {"mensaje": mensaje})


def editar_calificacion(request, id):
    if "usuario_id" not in request.session:
        return redirect("login")

    usuario_id = request.session["usuario_id"]

    try:
        corredor = Corredor.objects.get(fk_usuario_id=usuario_id)
    except Corredor.DoesNotExist:
        return redirect("perfil_administrador")

    try:
        calificacion = Calificacion.objects.get(id_calificacion=id, fk_id_corredor=corredor)
    except Calificacion.DoesNotExist:
        return redirect("perfil_usuario")

    if request.method == "POST":

        calificacion.descripcion = request.POST.get("descripcion")
        calificacion.ano = request.POST.get("ano")

        # --- FECHA ---
        fecha_input = request.POST.get("fecha")
        if fecha_input:
            calificacion.fecha = fecha_input

        factor = request.POST.get("factor_actualizado")
        calificacion.factor_actualizado = factor if factor != "" else None

        calificacion.save()

        registrar_auditoria(
            usuario_admin_id=usuario_id,
            accion="Editar calificación",
            resultado=f"Modificada {calificacion.descripcion}"
        )

        return redirect("perfil_usuario")

    return render(request, "template_calificaciones/template_editarCalificacion.html", {
        "c": calificacion
    })

def eliminar_calificacion(request, id):
    Calificacion.objects.filter(id_calificacion=id).delete()
    return redirect("perfil_usuario")

def listar_calificaciones(request):
    query = request.GET.get("q", "")
    filtro_ano = request.GET.get("ano", "")
    filtro_mercado = request.GET.get("mercado", "")

    calificaciones = Calificacion.objects.all()

    if query:
        calificaciones = calificaciones.filter(
            Q(descripcion__icontains=query) |
            Q(mercado__icontains=query) |
            Q(ano__icontains=query)
        )

    if filtro_ano:
        calificaciones = calificaciones.filter(ano=filtro_ano)

    if filtro_mercado:
        calificaciones = calificaciones.filter(mercado__icontains=filtro_mercado)

    context = {
        "calificaciones": calificaciones,
        "query": query,
        "filtro_ano": filtro_ano,
        "filtro_mercado": filtro_mercado,
    }

    return render(request, "calificaciones/listar_calificaciones.html", context)

# -- registro
def registrarse(request):
    if request.method == "POST":
        nombre = request.POST.get("nombre")
        correo = request.POST.get("correo")
        password = request.POST.get("password")

        # Crear usuario con estado pendiente
        Usuario.objects.create(
            nombre=nombre,
            correo=correo,
            contrasena=password,
            rol="corredor",
            estado="pendiente"
        )

        return render(request, "template_login/template_registro.html", {
            "mensaje": "Tu registro fue enviado. Un administrador debe aprobar tu cuenta."
        })

    return render(request, "template_login/template_registro.html")


def login(request):
    if request.method == "POST":
        correo = request.POST.get("usuario")
        contrasena = request.POST.get("password")

        # ✅ USAR AUTENTICACIÓN DJANGO - NO tu modelo personalizado
        user = authenticate(request, username=correo, password=contrasena)
        
        if user is not None:
            # Verificar si el usuario está activo
            if not user.is_active:
                return render(request, 'template_login/template_login.html', {
                    "error": "Tu cuenta está pendiente o desactivada."
                })
            
            # Iniciar sesión con Django
            auth_login(request, user)
            
            # Guardar sesión personalizada (si necesitas mantener tu lógica)
            request.session["usuario_id"] = user.id
            request.session["usuario_nombre"] = user.username
            request.session["usuario_rol"] = "corredor"  # O obtén del perfil
            
            return redirect("dashboard")
        else:
            return render(request, 'template_login/template_login.html', {
                "error": "Usuario o contraseña incorrectos"
            })

    return render(request, 'template_login/template_login.html')

# --- usuario
def perfil_usuario(request):
    if "usuario_id" not in request.session:
        return redirect("login")

    usuario_id = request.session["usuario_id"]
    corredor = Corredor.objects.get(fk_usuario_id=usuario_id)

    calificaciones = Calificacion.objects.filter(fk_id_corredor=corredor.id_corredor)

    # --- FILTROS ---
    mercado = request.GET.get("mercado")
    ano = request.GET.get("ano")
    buscar = request.GET.get("buscar")

    if mercado and mercado != "":
        calificaciones = calificaciones.filter(mercado__icontains=mercado)

    if ano and ano != "":
        calificaciones = calificaciones.filter(ano=ano)

    if buscar and buscar != "":
        calificaciones = calificaciones.filter(
            descripcion__icontains=buscar
        )

    return render(request, "template_calificaciones/template_calificaciones.html", {
        "calificaciones": calificaciones,
        "nombre_usuario": request.session["usuario_nombre"],
    })

@administrador_required
def aprobar_usuario(request, id):
    usuario = Usuario.objects.get(id_usuario=id)
    usuario.estado = "activo"
    usuario.save()

    Corredor.objects.get_or_create(fk_usuario=usuario)

    registrar_auditoria(
        request.session["usuario_id"],
        "Aprobar usuario",
        f"Usuario {usuario.nombre} aprobado"
    )

    return redirect("perfil_administrador")

def obtener_o_crear_corredor(usuario):
    from datetime import date

    try:
        return Corredor.objects.get(fk_usuario=usuario)
    except Corredor.DoesNotExist:
        # Crear corredor automáticamente
        return Corredor.objects.create(
            nombre=usuario.nombre,
            rut="00000000-0",  # Puedes ajustarlo luego
            telefono="Sin registrar",
            correo=usuario.correo,
            fecha_registro=date.today(),
            fk_usuario=usuario
        )

# --- panel administrador ---
@administrador_required
def perfil_administrador(request):
    usuarios = Usuario.objects.all()
    auditorias = Auditoria.objects.order_by("-fecha_hora")[:20]

    return render(request, 'template_administracion/template_administracion.html', {
        "usuarios": usuarios,
        "auditorias": auditorias,
    })


@administrador_required
def eliminar_usuario(request, id):
    usuario = Usuario.objects.get(id_usuario=id)

    if request.method == "POST":
        registrar_auditoria(
            request.session["usuario_id"],
            "Eliminar usuario",
            f"Se eliminó {usuario.nombre}"
        )
        usuario.delete()
        return redirect("perfil_administrador")

    return render(request, "template_administracion/eliminar_usuario.html", {
        "usuario": usuario
    })



@administrador_required
def editar_usuario(request, id):
    usuario = Usuario.objects.get(id_usuario=id)

    if request.method == "POST":
        usuario.rol = request.POST.get("rol")
        usuario.estado = request.POST.get("estado")
        usuario.save()

        registrar_auditoria(
            request.session["usuario_id"],
            "Editar usuario",
            f"Se editó {usuario.nombre}"
        )

        return redirect("perfil_administrador")

    return render(request, "template_administracion/editar_usuario.html", {
        "usuario": usuario
    })



@administrador_required
def aprobar_usuario(request, id):
    usuario = Usuario.objects.get(id_usuario=id)
    usuario.estado = "activo"
    usuario.save()

    registrar_auditoria(
        request.session["usuario_id"],
        "Aprobar usuario",
        f"Usuario {usuario.nombre} aprobado"
    )

    return redirect("perfil_administrador")


def dashboard(request):
    if request.session.get("usuario_rol") == "administrador":
        return render(request, "template_dashboard/template_dashboard_admin.html")

    if request.session.get("usuario_rol") == "corredor":
        return render(request, "template_calificaciones/template_dashboard_corredor.html")

    return redirect("login")


# -- Cargas
def listar_cargas(request):

    query = request.GET.get("q", "")
    filtro_estado = request.GET.get("estado", "")

    cargas = Archivocarga.objects.select_related("fk_id_usuario").all()

    if query:
        cargas = cargas.filter(
            Q(tipo_archivo__icontains=query) |
            Q(archivo_url__icontains=query) |
            Q(fk_id_usuario__nombre__icontains=query)
        )

    if filtro_estado:
        cargas = cargas.filter(estado__iexact=filtro_estado)

    context = {
        "cargas": cargas,
        "query": query,
        "filtro_estado": filtro_estado,
    }

    return render(request, "template_calificaciones/listar_cargas.html", context)

def logout(request):
    request.session.flush()
    return redirect("login")

#-- auditoria 
def registrar_auditoria(usuario_admin_id, accion, resultado):
    Auditoria.objects.create(
        accion=str(accion)[:20],
        fecha_hora=timezone.now(),
        resultado=str(resultado)[:50],
        fk_usuario_id=usuario_admin_id
    )

# -- permisos
def permisos(request):
    permisos = Permiso.objects.all()

    return render(request, "template_administracion/permisos.html", {
        "permisos": permisos
    })

@administrador_required
def editar_permiso(request, id_permiso):
    permiso = get_object_or_404(Permiso, pk=id_permiso)

    if request.method == "POST":
        permiso.nombre_permiso = request.POST.get("nombre_permiso")
        permiso.descripcion = request.POST.get("descripcion")
        permiso.save()

        # Registrar auditoría
        Auditoria.objects.create(
            accion="Editar permiso",
            resultado=f"Se modificó el permiso: {permiso.nombre_permiso}",
            fecha_hora=timezone.now(),
            fk_usuario_id=request.session["usuario_id"]
        )

        return redirect("permisos")

    return render(request, "template_administracion/editar_permiso.html", {
        "permiso": permiso
    })

@administrador_required
def crear_permiso(request):
    if request.method == "POST":
        nombre = request.POST.get("nombre_permiso")
        descripcion = request.POST.get("descripcion")

        permiso = Permiso.objects.create(
            nombre_permiso=nombre,
            descripcion=descripcion
        )

        registrar_auditoria(
            request.session["usuario_id"],
             "Editar permiso",
            f"Se modificó el permiso: {permiso.nombre_permiso}"
)


        return redirect("permisos")

    return render(request, "template_administracion/crear_permiso.html")

# ---------------------------------------------------------
# PANEL PRINCIPAL DEL CORREDOR
# ---------------------------------------------------------

@corredor_required
def panel_corredor(request):

    return render(request, "template_dashboard/template_panel_corredor.html", {
        "nombre": request.session.get("usuario_nombre")
    })


# ---------------------------------------------------------
# MANTENEDOR DE MONTOS
# ---------------------------------------------------------
@corredor_required
def mantenedor_montos(request):
    return render(request, "template_corredor/mantenedor_montos.html")


# ---------------------------------------------------------
# MANTENEDOR DE FACTORES
# ---------------------------------------------------------
@corredor_required
def mantenedor_factores(request):
    return render(request, "template_corredor/mantenedor_factores.html")


# ---------------------------------------------------------
# CALIFICACIONES NO INSCRITAS
# ---------------------------------------------------------
@corredor_required
def calificaciones_no_inscritas(request):

    usuario_id = request.session["usuario_id"]
    corredor = Corredor.objects.get(fk_usuario_id=usuario_id)

    # Calificaciones que NO pertenecen al corredor
    otras_calificaciones = Calificacion.objects.exclude(
        fk_id_corredor=corredor.id_corredor
    )

    return render(request, "template_corredor/calificaciones_no_inscritas.html", {
        "calificaciones": otras_calificaciones
    })


# ---------------------------------------------------------
# CARGA EXTERNA
# ---------------------------------------------------------
@corredor_required
def carga_externa(request):
    return render(request, "template_corredor/carga_externa.html")


# ---------------------------------------------------------
# VER MIS CALIFICACIONES
# ---------------------------------------------------------
@corredor_required
def ver_mis_calificaciones(request):

    usuario_id = request.session["usuario_id"]
    corredor = Corredor.objects.get(fk_usuario_id=usuario_id)

    mis_calificaciones = Calificacion.objects.filter(
        fk_id_corredor=corredor.id_corredor
    )

    return render(request, "template_corredor/mis_calificaciones.html", {
        "calificaciones": mis_calificaciones
    })

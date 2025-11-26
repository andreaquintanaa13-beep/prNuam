from django.shortcuts import redirect

def administrador_required(view_func):
    def wrapper(request, *args, **kwargs):

        rol = request.session.get("usuario_rol", "").strip().lower()

        if "usuario_id" not in request.session:
            return redirect("login")

        if rol != "administrador":
            return redirect("perfil_usuario")

        return view_func(request, *args, **kwargs)
    return wrapper


def corredor_required(view_func):
    def wrapper(request, *args, **kwargs):

        rol = request.session.get("usuario_rol", "").strip().lower()

        if "usuario_id" not in request.session:
            return redirect("login")

        if rol != "corredor":
            return redirect("perfil_administrador")

        return view_func(request, *args, **kwargs)
    return wrapper

def login_required_custom(view_func):
    def wrapper(request, *args, **kwargs):
        rol = request.session.get("usuario_rol")
        if rol in ["administrador", "corredor"]:
            return view_func(request, *args, **kwargs)
        return redirect("login")
    return wrapper

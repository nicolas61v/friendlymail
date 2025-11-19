"""
Authentication views - User registration, login, logout
"""
import logging
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from ..forms import UserRegistrationForm, UserLoginForm

logger = logging.getLogger('gmail_app')


def home(request):
    """Vista principal - redirige según estado de autenticación"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login')


def user_register(request):
    """Vista de registro de usuarios"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Iniciar sesión automáticamente después del registro
            login(request, user)
            messages.success(
                request,
                f'¡Bienvenido {user.username}! Tu cuenta ha sido creada exitosamente.'
            )
            logger.info(f"Nuevo usuario registrado: {user.username} ({user.email})")
            return redirect('dashboard')
        else:
            # Los errores del formulario se mostrarán automáticamente en el template
            logger.warning(f"Intento de registro fallido: {form.errors}")
    else:
        form = UserRegistrationForm()

    return render(request, 'gmail_app/register.html', {'form': form})


def user_login(request):
    """Vista de inicio de sesión"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserLoginForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)

            if user is not None:
                login(request, user)
                messages.success(request, f'¡Bienvenido de vuelta, {user.username}!')
                logger.info(f"Usuario {user.username} inició sesión")

                # Redirigir a la página solicitada o al dashboard
                next_page = request.GET.get('next', 'dashboard')
                return redirect(next_page)
            else:
                messages.error(request, 'Usuario o contraseña incorrectos.')
                logger.warning(f"Intento de login fallido para usuario: {username}")
        else:
            # Los errores del formulario se mostrarán automáticamente
            logger.warning(f"Formulario de login inválido: {form.errors}")
    else:
        form = UserLoginForm()

    return render(request, 'gmail_app/login.html', {'form': form})


@login_required
def user_logout(request):
    """Vista de cierre de sesión"""
    username = request.user.username
    logout(request)
    messages.success(request, f'Has cerrado sesión exitosamente. ¡Hasta pronto, {username}!')
    logger.info(f"Usuario {username} cerró sesión")
    return redirect('login')

from django.shortcuts import render, redirect
from .forms import RegistrationForm

# Variables globales
nombre_global = None
correo_global = None

def home_view(request):
    global nombre_global, correo_global

    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            nombre_global = form.cleaned_data['nombre']
            correo_global = form.cleaned_data['correo']
            return redirect('success')
    else:
        form = RegistrationForm()

    return render(request, 'registrations/home.html', {'form': form})

def success_view(request):
    global nombre_global, correo_global
    return render(request, 'registrations/success.html', {
        'nombre': nombre_global,
        'correo': correo_global
    })

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
import re


class UserRegistrationForm(UserCreationForm):
    """
    Formulario de registro de usuario con validaciones personalizadas
    """
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'ejemplo@correo.com',
            'autocomplete': 'email'
        }),
        label='Correo electrónico'
    )

    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'nombre_usuario',
            'autocomplete': 'username'
        }),
        label='Nombre de usuario',
        help_text='Solo letras, números y los caracteres @/./+/-/_ permitidos.'
    )

    first_name = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Juan',
            'autocomplete': 'given-name'
        }),
        label='Nombre (opcional)'
    )

    last_name = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Pérez',
            'autocomplete': 'family-name'
        }),
        label='Apellido (opcional)'
    )

    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '••••••••',
            'autocomplete': 'new-password'
        }),
        label='Contraseña',
        help_text='Mínimo 8 caracteres. No puede ser completamente numérica.'
    )

    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '••••••••',
            'autocomplete': 'new-password'
        }),
        label='Confirmar contraseña',
        help_text='Ingresa la misma contraseña para verificación.'
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']

    def clean_email(self):
        """
        Valida que el email no esté ya registrado
        """
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('Este correo electrónico ya está registrado.')
        return email.lower()

    def clean_username(self):
        """
        Valida el nombre de usuario
        """
        username = self.cleaned_data.get('username')

        # Validar longitud mínima
        if len(username) < 3:
            raise ValidationError('El nombre de usuario debe tener al menos 3 caracteres.')

        # Validar caracteres permitidos
        if not re.match(r'^[\w.@+-]+$', username):
            raise ValidationError('El nombre de usuario solo puede contener letras, números y los caracteres @/./+/-/_')

        # Verificar que no exista
        if User.objects.filter(username=username).exists():
            raise ValidationError('Este nombre de usuario ya está en uso.')

        return username

    def clean_password1(self):
        """
        Valida la contraseña
        """
        password = self.cleaned_data.get('password1')

        # Validar longitud mínima
        if len(password) < 8:
            raise ValidationError('La contraseña debe tener al menos 8 caracteres.')

        # Validar que no sea completamente numérica
        if password.isdigit():
            raise ValidationError('La contraseña no puede ser completamente numérica.')

        return password

    def save(self, commit=True):
        """
        Guarda el usuario con el email en minúsculas
        """
        user = super().save(commit=False)
        user.email = self.cleaned_data['email'].lower()

        if commit:
            user.save()

        return user


class UserLoginForm(AuthenticationForm):
    """
    Formulario de inicio de sesión personalizado
    """
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'nombre_usuario o correo@ejemplo.com',
            'autocomplete': 'username'
        }),
        label='Usuario o correo electrónico'
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '••••••••',
            'autocomplete': 'current-password'
        }),
        label='Contraseña'
    )

    error_messages = {
        'invalid_login': 'Usuario o contraseña incorrectos. Por favor, intenta de nuevo.',
        'inactive': 'Esta cuenta está inactiva.',
    }

    def clean_username(self):
        """
        Permite login con email o username
        """
        username_or_email = self.cleaned_data.get('username')

        # Si parece un email, buscar el usuario por email
        if '@' in username_or_email:
            try:
                user = User.objects.get(email=username_or_email.lower())
                return user.username
            except User.DoesNotExist:
                # Si no encuentra el email, dejar que Django maneje el error
                pass

        return username_or_email

from django import forms

class RegistrationForm(forms.Form):
    nombre = forms.CharField(label="Nombre", max_length=100)
    correo = forms.EmailField(label="Correo")

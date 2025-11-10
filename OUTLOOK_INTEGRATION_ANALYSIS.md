# Análisis de Integración con Outlook - FriendlyMail

## Resumen Ejecutivo

Este documento analiza la viabilidad y requerimientos para integrar Microsoft Outlook/Office 365 en FriendlyMail, permitiendo mostrar correos de múltiples cuentas (Gmail + Outlook) en un dashboard unificado ordenado cronológicamente.

**Conclusión:** La integración es completamente viable y sigue un patrón similar a Gmail usando OAuth2 y Microsoft Graph API.

---

## 1. Análisis de la Situación Actual

### 1.1 Arquitectura Actual de Gmail

**Modelos de Datos:**
- `GmailAccount`: Almacena credenciales OAuth2 de Google (1:1 con User)
- `Email`: Almacena emails sincronizados con `received_date` para ordenamiento

**Problema Actual:**
```python
# gmail_app/views.py línea 102
emails = Email.objects.filter(gmail_account=gmail_account)[:20]
```

Este código solo obtiene emails de Gmail. La relación es:
```
User → GmailAccount → Email
```

**Ordenamiento Actual:**
```python
# gmail_app/models.py línea 32-33
class Meta:
    ordering = ['-received_date']  # Más reciente primero
```

Esto ya está bien implementado (orden descendente = más reciente primero).

### 1.2 Limitaciones Actuales

1. **Relación 1:1 rígida:** Un usuario solo puede conectar UNA cuenta de Gmail
2. **Modelo Email acoplado:** El campo `gmail_account` solo permite Gmail
3. **Vista dashboard limitada:** Solo muestra emails de Gmail
4. **Sin unificación:** No hay forma de mezclar correos de múltiples proveedores

---

## 2. Análisis de Viabilidad - Integración Outlook

### 2.1 Comparación Gmail vs Outlook

| Aspecto | Gmail API | Microsoft Graph API |
|---------|-----------|---------------------|
| **Protocolo Auth** | OAuth 2.0 | OAuth 2.0 |
| **Tipo de Token** | Access + Refresh Token | Access + Refresh Token |
| **Permisos (Scopes)** | `gmail.readonly`, `gmail.send` | `Mail.Read`, `Mail.Send` |
| **API REST** | Google Gmail API | Microsoft Graph API |
| **Librería Python** | `google-api-python-client` | `msal` (Microsoft Auth Library) |
| **Endpoint de Auth** | accounts.google.com/o/oauth2/auth | login.microsoftonline.com |
| **Endpoint de API** | gmail.googleapis.com | graph.microsoft.com |
| **Registro de App** | Google Cloud Console | Azure AD Portal |

**Conclusión:** Ambos usan flujos OAuth2 similares, por lo que la arquitectura puede ser paralela.

### 2.2 Viabilidad Técnica: ✅ ALTA

**Razones:**
1. OAuth2 es estándar en ambos
2. Ambos proveen APIs REST bien documentadas
3. Existen librerías Python maduras para ambos
4. Los datos de correos son similares (subject, from, to, body, date)
5. La aplicación ya tiene experiencia con OAuth2 (Gmail)

---

## 3. Arquitectura Propuesta - Multi-Proveedor

### 3.1 Diseño de Base de Datos

**Opción 1: Modelo Unificado con Polimorfismo (RECOMENDADO)**

```python
# Nuevo modelo abstracto
class EmailAccount(models.Model):
    """Clase base para todas las cuentas de email"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_accounts')
    email = models.EmailField()
    provider = models.CharField(max_length=20, choices=[
        ('gmail', 'Gmail'),
        ('outlook', 'Outlook')
    ])
    access_token = models.TextField()
    refresh_token = models.TextField(null=True, blank=True)
    token_expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [['user', 'email', 'provider']]

# Reemplazar GmailAccount con EmailAccount
# O mantener compatibilidad con migración
```

**Modelo Email Actualizado:**
```python
class Email(models.Model):
    email_account = models.ForeignKey(EmailAccount, on_delete=models.CASCADE, related_name='emails')
    # gmail_account → email_account (migración)

    provider_id = models.CharField(max_length=255)  # ID único del proveedor
    thread_id = models.CharField(max_length=255)
    subject = models.CharField(max_length=500, blank=True)
    sender = models.CharField(max_length=255)
    recipient = models.CharField(max_length=255)
    body_plain = models.TextField(blank=True)
    body_html = models.TextField(blank=True)
    received_date = models.DateTimeField()  # Clave para ordenamiento unificado
    is_read = models.BooleanField(default=False)
    is_important = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-received_date']  # MANTENER ESTE ORDEN
        unique_together = [['email_account', 'provider_id']]
```

### 3.2 Servicios Separados

```
gmail_app/
├── services/
│   ├── __init__.py
│   ├── base_email_service.py    # Clase abstracta base
│   ├── gmail_service.py          # Implementación Gmail (existente)
│   └── outlook_service.py        # Implementación Outlook (NUEVO)
```

**Interfaz Base:**
```python
class BaseEmailService(ABC):
    @abstractmethod
    def get_authorization_url(self, request):
        pass

    @abstractmethod
    def handle_oauth_callback(self, request):
        pass

    @abstractmethod
    def get_credentials(self):
        pass

    @abstractmethod
    def sync_emails(self, max_results=20):
        pass

    @abstractmethod
    def send_email(self, to, subject, body):
        pass
```

### 3.3 Vista Dashboard Unificada

```python
@login_required
def dashboard(request):
    # Obtener TODAS las cuentas de email del usuario
    email_accounts = EmailAccount.objects.filter(user=request.user, is_active=True)

    # Obtener emails de TODAS las cuentas, ya ordenados por received_date
    emails = Email.objects.filter(
        email_account__in=email_accounts
    ).select_related('email_account')[:50]  # Aumentar límite

    # Emails ya vienen ordenados por Meta.ordering = ['-received_date']
    # No necesitas hacer más ordenamiento

    context = {
        'email_accounts': email_accounts,
        'emails': emails,
        'has_accounts': email_accounts.exists(),
        'gmail_accounts': email_accounts.filter(provider='gmail'),
        'outlook_accounts': email_accounts.filter(provider='outlook'),
    }
    return render(request, 'gmail_app/dashboard.html', context)
```

---

## 4. Configuración de Microsoft Azure AD

### 4.1 Registro de Aplicación en Azure Portal

**Pasos detallados:**

1. **Ir a Azure Portal:**
   - URL: https://portal.azure.com
   - Iniciar sesión con cuenta Microsoft/Office 365

2. **Navegar a Azure Active Directory:**
   - Menú lateral → "Azure Active Directory"
   - Seleccionar "App registrations"

3. **Crear Nueva Aplicación:**
   - Click en "New registration"
   - **Name:** FriendlyMail
   - **Supported account types:**
     - Selecciona "Accounts in any organizational directory and personal Microsoft accounts"
     - Esto permite Gmail, Outlook, Office 365, etc.

4. **Configurar Redirect URI:**
   - **Type:** Web
   - **Redirect URI:**
     - Desarrollo: `http://localhost:8000/outlook/callback/`
     - Producción: `https://tu-dominio.com/outlook/callback/`

5. **Copiar Credenciales Importantes:**
   - Ir a "Overview" de tu app
   - **Copiar:**
     - `Application (client) ID` → Será tu `OUTLOOK_CLIENT_ID`
     - `Directory (tenant) ID` → Será tu `OUTLOOK_TENANT_ID`

6. **Crear Client Secret:**
   - Ir a "Certificates & secrets"
   - Click "New client secret"
   - **Description:** "FriendlyMail Production"
   - **Expires:** 24 months (recomendado)
   - Click "Add"
   - **COPIAR INMEDIATAMENTE el Value** → Será tu `OUTLOOK_CLIENT_SECRET`
     - ⚠️ Solo se muestra una vez, guárdalo en lugar seguro

7. **Configurar Permisos API:**
   - Ir a "API permissions"
   - Click "Add a permission"
   - Seleccionar "Microsoft Graph"
   - Seleccionar "Delegated permissions"
   - **Agregar estos permisos:**
     - `openid` (para autenticación)
     - `email` (para obtener email del usuario)
     - `profile` (para obtener nombre)
     - `offline_access` (para refresh token)
     - `Mail.Read` (para leer correos)
     - `Mail.Send` (para enviar correos)
     - `Mail.ReadWrite` (opcional, para marcar como leído)

8. **Grant Admin Consent (Opcional pero recomendado):**
   - Click "Grant admin consent for [tenant]"
   - Esto evita que cada usuario tenga que aprobar permisos

### 4.2 Variables de Entorno Necesarias

Agregar a tu archivo `.env`:

```bash
# ========================================
# GMAIL (Existentes - NO CAMBIAR)
# ========================================
GOOGLE_OAUTH2_CLIENT_ID=tu_client_id_de_google.apps.googleusercontent.com
GOOGLE_OAUTH2_CLIENT_SECRET=GOCSPX-tu_secret_de_google
GOOGLE_OAUTH2_REDIRECT_URI=http://localhost:8000/gmail/callback/

# ========================================
# MICROSOFT OUTLOOK/OFFICE 365 (NUEVAS)
# ========================================
# Client ID de Azure AD (Application ID)
OUTLOOK_CLIENT_ID=12345678-1234-1234-1234-123456789abc

# Client Secret de Azure AD (generado en Certificates & secrets)
OUTLOOK_CLIENT_SECRET=abc~XyZ123_tu_secret_aqui

# Tenant ID de Azure AD (Directory ID)
# Usa 'common' para permitir cualquier cuenta Microsoft
# O usa tu Tenant ID específico para restringir a tu organización
OUTLOOK_TENANT_ID=common

# Redirect URI para OAuth callback
OUTLOOK_REDIRECT_URI=http://localhost:8000/outlook/callback/

# Authority URL (base para autenticación)
OUTLOOK_AUTHORITY=https://login.microsoftonline.com/common
```

### 4.3 Actualizar `settings.py`

```python
# friendlymail/settings.py

# ========== GMAIL CONFIG (Existente) ==========
GOOGLE_OAUTH2_CLIENT_ID = os.environ.get('GOOGLE_OAUTH2_CLIENT_ID')
GOOGLE_OAUTH2_CLIENT_SECRET = os.environ.get('GOOGLE_OAUTH2_CLIENT_SECRET')
GOOGLE_OAUTH2_REDIRECT_URI = os.environ.get('GOOGLE_OAUTH2_REDIRECT_URI', 'http://localhost:8000/gmail/callback/')

GMAIL_SCOPES = [
    'openid',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/userinfo.email'
]

# ========== OUTLOOK CONFIG (NUEVO) ==========
OUTLOOK_CLIENT_ID = os.environ.get('OUTLOOK_CLIENT_ID')
OUTLOOK_CLIENT_SECRET = os.environ.get('OUTLOOK_CLIENT_SECRET')
OUTLOOK_TENANT_ID = os.environ.get('OUTLOOK_TENANT_ID', 'common')
OUTLOOK_REDIRECT_URI = os.environ.get('OUTLOOK_REDIRECT_URI', 'http://localhost:8000/outlook/callback/')

# Authority URL para autenticación
OUTLOOK_AUTHORITY = f"https://login.microsoftonline.com/{OUTLOOK_TENANT_ID}"

# Scopes (permisos) para Microsoft Graph API
OUTLOOK_SCOPES = [
    'openid',
    'email',
    'profile',
    'offline_access',  # Necesario para refresh token
    'https://graph.microsoft.com/Mail.Read',
    'https://graph.microsoft.com/Mail.Send',
    'https://graph.microsoft.com/Mail.ReadWrite'
]
```

---

## 5. Librerías Python Necesarias

### 5.1 Actualizar `requirements.txt`

```txt
# ========== Existentes (Gmail) ==========
Django==4.2.15
google-auth==2.28.2
google-auth-oauthlib==1.2.0
google-auth-httplib2==0.2.0
google-api-python-client==2.124.0
python-dotenv==1.0.0
openai==1.51.0
django-apscheduler==0.6.2

# ========== NUEVAS (Outlook/Microsoft Graph) ==========
# MSAL (Microsoft Authentication Library)
msal==1.31.1

# Requests para llamadas a Microsoft Graph API
requests==2.32.3
```

### 5.2 Instalar Dependencias

```bash
pip install msal==1.31.1 requests==2.32.3
```

---

## 6. Implementación de Outlook Service

### 6.1 Estructura del Servicio

Crear archivo: `gmail_app/outlook_service.py`

```python
import msal
import requests
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class OutlookService:
    """
    Servicio para interactuar con Microsoft Graph API (Outlook/Office 365)
    Similar a GmailService pero para Microsoft
    """

    def __init__(self, user):
        self.user = user
        self.client_id = settings.OUTLOOK_CLIENT_ID
        self.client_secret = settings.OUTLOOK_CLIENT_SECRET
        self.authority = settings.OUTLOOK_AUTHORITY
        self.redirect_uri = settings.OUTLOOK_REDIRECT_URI
        self.scopes = settings.OUTLOOK_SCOPES

    def get_authorization_url(self, request):
        """
        Genera URL de autorización OAuth2 de Microsoft
        Similar a gmail_service.py línea 31
        """
        # Crear cliente MSAL
        msal_app = msal.ConfidentialClientApplication(
            self.client_id,
            authority=self.authority,
            client_credential=self.client_secret
        )

        # Generar state para seguridad CSRF
        import secrets
        state = secrets.token_urlsafe(32)
        request.session['oauth_state'] = state

        # Generar URL de autorización
        auth_url = msal_app.get_authorization_request_url(
            scopes=self.scopes,
            state=state,
            redirect_uri=self.redirect_uri
        )

        return auth_url

    def handle_oauth_callback(self, request):
        """
        Procesa el callback de OAuth2 y guarda tokens
        Similar a gmail_service.py línea 58
        """
        from gmail_app.models import EmailAccount  # Importar nuevo modelo

        # Validar state (CSRF protection)
        state = request.GET.get('state')
        stored_state = request.session.get('oauth_state')

        if not state or state != stored_state:
            raise Exception("Invalid state parameter - possible CSRF attack")

        # Obtener código de autorización
        code = request.GET.get('code')
        if not code:
            error = request.GET.get('error')
            error_description = request.GET.get('error_description', 'Unknown error')
            raise Exception(f"OAuth error: {error} - {error_description}")

        # Crear cliente MSAL
        msal_app = msal.ConfidentialClientApplication(
            self.client_id,
            authority=self.authority,
            client_credential=self.client_secret
        )

        # Intercambiar código por tokens
        result = msal_app.acquire_token_by_authorization_code(
            code=code,
            scopes=self.scopes,
            redirect_uri=self.redirect_uri
        )

        if 'error' in result:
            raise Exception(f"Token acquisition failed: {result.get('error_description')}")

        # Extraer tokens
        access_token = result['access_token']
        refresh_token = result.get('refresh_token')  # Puede ser None si no se pidió offline_access
        expires_in = result.get('expires_in', 3600)  # segundos

        if not refresh_token:
            raise Exception("No refresh token received - ensure 'offline_access' scope is included")

        # Obtener email del usuario usando Microsoft Graph
        user_email = self._get_user_email(access_token)

        # Calcular expiración
        token_expires_at = timezone.now() + timedelta(seconds=expires_in)

        # Guardar o actualizar cuenta
        email_account, created = EmailAccount.objects.update_or_create(
            user=self.user,
            email=user_email,
            provider='outlook',
            defaults={
                'access_token': access_token,
                'refresh_token': refresh_token,
                'token_expires_at': token_expires_at,
                'is_active': True
            }
        )

        logger.info(f"Outlook account {'created' if created else 'updated'}: {user_email}")
        return email_account

    def _get_user_email(self, access_token):
        """Obtiene el email del usuario desde Microsoft Graph"""
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get('https://graph.microsoft.com/v1.0/me', headers=headers)

        if response.status_code != 200:
            raise Exception(f"Failed to get user info: {response.text}")

        user_data = response.json()
        return user_data.get('mail') or user_data.get('userPrincipalName')

    def get_credentials(self):
        """
        Obtiene y refresca credenciales si es necesario
        Similar a gmail_service.py línea 108
        """
        from gmail_app.models import EmailAccount

        try:
            account = EmailAccount.objects.get(user=self.user, provider='outlook', is_active=True)
        except EmailAccount.DoesNotExist:
            raise Exception("No active Outlook account found")

        # Verificar si el token expiró
        if timezone.now() >= account.token_expires_at:
            logger.info("Access token expired, refreshing...")
            account = self._refresh_token(account)

        return account.access_token

    def _refresh_token(self, account):
        """Refresca el access token usando refresh token"""
        msal_app = msal.ConfidentialClientApplication(
            self.client_id,
            authority=self.authority,
            client_credential=self.client_secret
        )

        result = msal_app.acquire_token_by_refresh_token(
            refresh_token=account.refresh_token,
            scopes=self.scopes
        )

        if 'error' in result:
            logger.error(f"Token refresh failed: {result.get('error_description')}")
            account.is_active = False
            account.save()
            raise Exception("Failed to refresh token - please reconnect your account")

        # Actualizar tokens
        account.access_token = result['access_token']
        if 'refresh_token' in result:
            account.refresh_token = result['refresh_token']

        expires_in = result.get('expires_in', 3600)
        account.token_expires_at = timezone.now() + timedelta(seconds=expires_in)
        account.save()

        logger.info("Access token refreshed successfully")
        return account

    def sync_emails(self, max_results=20):
        """
        Sincroniza emails desde Microsoft Graph API
        Similar a gmail_service.py línea 167
        """
        from gmail_app.models import Email, EmailAccount

        access_token = self.get_credentials()
        account = EmailAccount.objects.get(user=self.user, provider='outlook', is_active=True)

        # Llamar a Microsoft Graph API para obtener mensajes
        headers = {'Authorization': f'Bearer {access_token}'}

        # Endpoint: https://graph.microsoft.com/v1.0/me/messages
        # Query parameters para ordenar y limitar
        params = {
            '$top': max_results,
            '$orderby': 'receivedDateTime desc',
            '$select': 'id,subject,from,toRecipients,receivedDateTime,body,isRead,importance'
        }

        response = requests.get(
            'https://graph.microsoft.com/v1.0/me/messages',
            headers=headers,
            params=params
        )

        if response.status_code != 200:
            raise Exception(f"Failed to fetch emails: {response.text}")

        messages = response.json().get('value', [])

        new_count = 0
        updated_count = 0

        for msg in messages:
            msg_id = msg['id']

            # Parsear datos del mensaje
            subject = msg.get('subject', '')
            sender = msg.get('from', {}).get('emailAddress', {}).get('address', '')

            # Recipients (puede haber múltiples)
            recipients = msg.get('toRecipients', [])
            recipient = recipients[0].get('emailAddress', {}).get('address', '') if recipients else ''

            # Fecha
            received_date_str = msg.get('receivedDateTime')
            received_date = datetime.fromisoformat(received_date_str.replace('Z', '+00:00'))

            # Body
            body_content = msg.get('body', {})
            body_html = body_content.get('content', '') if body_content.get('contentType') == 'html' else ''
            body_plain = body_content.get('content', '') if body_content.get('contentType') == 'text' else ''

            # Flags
            is_read = msg.get('isRead', False)
            is_important = msg.get('importance') == 'high'

            # Guardar o actualizar en BD
            email, created = Email.objects.update_or_create(
                email_account=account,
                provider_id=msg_id,
                defaults={
                    'thread_id': msg_id,  # Outlook no tiene thread_id como Gmail
                    'subject': subject[:500],
                    'sender': sender[:255],
                    'recipient': recipient[:255],
                    'body_plain': body_plain,
                    'body_html': body_html,
                    'received_date': received_date,
                    'is_read': is_read,
                    'is_important': is_important
                }
            )

            if created:
                new_count += 1
            else:
                updated_count += 1

        logger.info(f"Outlook sync complete: {new_count} new, {updated_count} updated")

        return {
            'new_emails': new_count,
            'updated_emails': updated_count,
            'total_synced': len(messages)
        }

    def send_email(self, to, subject, body, is_html=True):
        """
        Envía email usando Microsoft Graph API
        Similar a gmail_service.py línea 269
        """
        access_token = self.get_credentials()

        # Construir payload según formato de Microsoft Graph
        message = {
            'subject': subject,
            'body': {
                'contentType': 'HTML' if is_html else 'Text',
                'content': body
            },
            'toRecipients': [
                {
                    'emailAddress': {
                        'address': to
                    }
                }
            ]
        }

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        # Enviar mensaje
        response = requests.post(
            'https://graph.microsoft.com/v1.0/me/sendMail',
            headers=headers,
            json={'message': message}
        )

        if response.status_code not in [200, 202]:
            raise Exception(f"Failed to send email: {response.text}")

        logger.info(f"Email sent successfully to {to}")
        return True
```

---

## 7. Rutas y Vistas Necesarias

### 7.1 Actualizar `gmail_app/urls.py`

```python
from django.urls import path
from . import views

urlpatterns = [
    # ... rutas existentes ...

    # ========== NUEVAS RUTAS OUTLOOK ==========
    path('connect-outlook/', views.connect_outlook, name='connect_outlook'),
    path('outlook/callback/', views.outlook_callback, name='outlook_callback'),
    path('disconnect-outlook/<int:account_id>/', views.disconnect_outlook, name='disconnect_outlook'),
    path('sync-outlook/', views.sync_outlook, name='sync_outlook'),
]
```

### 7.2 Agregar Vistas en `gmail_app/views.py`

```python
from gmail_app.outlook_service import OutlookService

@login_required
def connect_outlook(request):
    """Inicia flujo OAuth2 para Outlook"""
    outlook_service = OutlookService(request.user)
    authorization_url = outlook_service.get_authorization_url(request)
    return redirect(authorization_url)

@login_required
def outlook_callback(request):
    """Callback de OAuth2 para Outlook"""
    try:
        outlook_service = OutlookService(request.user)
        email_account = outlook_service.handle_oauth_callback(request)
        messages.success(request, f'Outlook account {email_account.email} connected successfully!')
        return redirect('dashboard')
    except Exception as e:
        logger.error(f"Outlook OAuth error: {e}")
        messages.error(request, f'Failed to connect Outlook: {str(e)}')
        return redirect('dashboard')

@login_required
def disconnect_outlook(request, account_id):
    """Desconecta cuenta de Outlook"""
    try:
        account = EmailAccount.objects.get(id=account_id, user=request.user, provider='outlook')
        account.is_active = False
        account.save()
        messages.success(request, f'Outlook account {account.email} disconnected')
    except EmailAccount.DoesNotExist:
        messages.error(request, 'Account not found')
    return redirect('dashboard')

@login_required
def sync_outlook(request):
    """Sincroniza emails de Outlook"""
    try:
        outlook_service = OutlookService(request.user)
        result = outlook_service.sync_emails()
        messages.success(request, f"Synced {result['new_emails']} new Outlook emails")
    except Exception as e:
        logger.error(f"Outlook sync error: {e}")
        messages.error(request, f'Sync failed: {str(e)}')
    return redirect('dashboard')
```

---

## 8. Migración de Base de Datos

### 8.1 Plan de Migración

**Opción A: Crear nuevo modelo y migrar (RECOMENDADO)**

```bash
# 1. Crear EmailAccount model
# 2. Migrar datos de GmailAccount a EmailAccount
# 3. Actualizar ForeignKey en Email
# 4. Deprecar GmailAccount (mantener por compatibilidad)

python manage.py makemigrations
python manage.py migrate
```

**Opción B: Modificar modelo existente**

Menos recomendado porque rompe compatibilidad.

### 8.2 Script de Migración de Datos

```python
# Script para migrar de GmailAccount a EmailAccount
from gmail_app.models import GmailAccount, EmailAccount, Email

def migrate_gmail_to_email_account():
    """Migra GmailAccount existentes a EmailAccount"""
    for gmail_acc in GmailAccount.objects.all():
        email_acc, created = EmailAccount.objects.get_or_create(
            user=gmail_acc.user,
            email=gmail_acc.email,
            provider='gmail',
            defaults={
                'access_token': gmail_acc.access_token,
                'refresh_token': gmail_acc.refresh_token,
                'token_expires_at': gmail_acc.token_expires_at,
                'is_active': True
            }
        )

        # Actualizar emails para apuntar a EmailAccount
        Email.objects.filter(gmail_account=gmail_acc).update(email_account=email_acc)

        print(f"Migrated: {gmail_acc.email}")
```

---

## 9. Actualización del Dashboard

### 9.1 Cambios en `dashboard.html`

```html
<!-- Agregar botón para conectar Outlook -->
{% if not outlook_accounts %}
<div class="connect-card">
    <i class="fab fa-microsoft"></i>
    <h3>Connect Outlook</h3>
    <a href="{% url 'connect_outlook' %}" class="connect-button">
        <i class="fab fa-microsoft"></i> Connect Outlook
    </a>
</div>
{% endif %}

<!-- Mostrar indicador de proveedor en cada email -->
<div class="email-item">
    <div class="email-provider-badge">
        {% if email.email_account.provider == 'gmail' %}
            <i class="fab fa-google"></i> Gmail
        {% elif email.email_account.provider == 'outlook' %}
            <i class="fab fa-microsoft"></i> Outlook
        {% endif %}
    </div>
    <!-- ... resto del email ... -->
</div>
```

### 9.2 Ordenamiento Unificado (Ya está resuelto)

Como ambos proveedores guardan en el campo `received_date`, el ordenamiento ya funciona:

```python
# gmail_app/models.py
class Meta:
    ordering = ['-received_date']  # Descendente = más reciente primero
```

Esto asegura que:
- Gmail email de hoy 10:00 AM
- Outlook email de hoy 9:00 AM
- Gmail email de ayer 8:00 PM

Se muestran en ese orden automáticamente.

---

## 10. Consideraciones Importantes

### 10.1 Seguridad

1. **Secrets en .env:** Nunca commitear `.env` al repositorio
2. **HTTPS en producción:** OAuth2 requiere HTTPS para redirect URI
3. **State parameter:** Implementado para prevenir CSRF
4. **Token encryption:** Considerar encriptar tokens en BD (Django `EncryptedTextField`)

### 10.2 Escalabilidad

1. **Rate Limits:**
   - Gmail: 250 mensajes/segundo/usuario
   - Microsoft Graph: 10,000 requests/10 minutos/app

2. **Sincronización:**
   - Considerar sincronización incremental (solo nuevos)
   - Usar webhooks/push notifications para tiempo real
   - Microsoft Graph soporta Delta Query

3. **Paginación:**
   - Implementar paginación para >50 emails
   - Microsoft Graph usa `@odata.nextLink`

### 10.3 Experiencia de Usuario

1. **Indicadores visuales:**
   - Iconos distintos para Gmail vs Outlook
   - Colores diferentes por proveedor

2. **Sincronización:**
   - Botón "Sync All" para ambos proveedores
   - Indicador de progreso por proveedor

3. **Gestión de cuentas:**
   - Panel para ver todas las cuentas conectadas
   - Permitir desconectar cuentas individuales
   - Mostrar fecha de última sincronización por cuenta

### 10.4 Limitaciones a Considerar

1. **Refresh Token Lifetime:**
   - Google: ~6 meses si no se usa
   - Microsoft: ~90 días por defecto
   - Implementar re-autenticación automática

2. **Permisos:**
   - Usuarios deben dar consentimiento explícito
   - Admin consent puede simplificar para organizaciones

3. **Multi-cuenta Gmail:**
   - Actualmente solo permite 1 Gmail por la relación OneToOne
   - Con EmailAccount, permite múltiples Gmail y Outlook

---

## 11. Checklist de Implementación

### Fase 1: Configuración (30 minutos)
- [ ] Registrar app en Azure AD Portal
- [ ] Copiar Client ID, Client Secret, Tenant ID
- [ ] Agregar variables a `.env`
- [ ] Actualizar `settings.py` con config de Outlook
- [ ] Instalar dependencias: `pip install msal requests`

### Fase 2: Modelos (1 hora)
- [ ] Crear modelo `EmailAccount`
- [ ] Agregar campo `provider` y `email_account` a `Email`
- [ ] Crear migración: `python manage.py makemigrations`
- [ ] Aplicar migración: `python manage.py migrate`
- [ ] Migrar datos de `GmailAccount` a `EmailAccount`

### Fase 3: Servicios (2 horas)
- [ ] Crear `outlook_service.py`
- [ ] Implementar `get_authorization_url()`
- [ ] Implementar `handle_oauth_callback()`
- [ ] Implementar `get_credentials()` y `_refresh_token()`
- [ ] Implementar `sync_emails()`
- [ ] Implementar `send_email()`

### Fase 4: Vistas y URLs (1 hora)
- [ ] Agregar rutas en `urls.py`
- [ ] Crear vista `connect_outlook()`
- [ ] Crear vista `outlook_callback()`
- [ ] Crear vista `disconnect_outlook()`
- [ ] Actualizar vista `dashboard()` para multi-proveedor

### Fase 5: Frontend (1 hora)
- [ ] Agregar botón "Connect Outlook" en dashboard
- [ ] Mostrar badge de proveedor en cada email
- [ ] Agregar panel de cuentas conectadas
- [ ] Estilos CSS para iconos de Outlook

### Fase 6: Testing (1 hora)
- [ ] Probar OAuth flow completo
- [ ] Verificar sincronización de emails
- [ ] Verificar ordenamiento unificado
- [ ] Probar desconexión de cuenta
- [ ] Probar refresh de tokens

**Total estimado: 6-7 horas de desarrollo**

---

## 12. Resumen de Variables a Preparar

### En Azure Portal:
1. **Application (client) ID** → `OUTLOOK_CLIENT_ID`
2. **Client Secret Value** → `OUTLOOK_CLIENT_SECRET`
3. **Directory (tenant) ID** → `OUTLOOK_TENANT_ID` (o usar `common`)

### En Archivo `.env`:
```bash
OUTLOOK_CLIENT_ID=tu-client-id-aqui
OUTLOOK_CLIENT_SECRET=tu-secret-aqui
OUTLOOK_TENANT_ID=common
OUTLOOK_REDIRECT_URI=http://localhost:8000/outlook/callback/
```

### Redirect URIs a Configurar en Azure:
- Desarrollo: `http://localhost:8000/outlook/callback/`
- Producción: `https://tu-dominio.com/outlook/callback/`

### Permisos (Scopes) a Solicitar:
- `openid`
- `email`
- `profile`
- `offline_access`
- `Mail.Read`
- `Mail.Send`
- `Mail.ReadWrite`

---

## 13. Conclusión

**Viabilidad: ✅ ALTA**

La integración de Outlook es totalmente viable y sigue patrones similares a Gmail. Los cambios arquitectónicos propuestos (modelo `EmailAccount` unificado) permiten:

1. ✅ Múltiples cuentas de Gmail y Outlook por usuario
2. ✅ Dashboard unificado con correos de todos los proveedores
3. ✅ Ordenamiento cronológico automático (ya implementado)
4. ✅ Extensibilidad futura para otros proveedores (Yahoo, iCloud, etc.)

**Próximos Pasos:**
1. Registrar aplicación en Azure AD
2. Obtener credenciales (Client ID, Secret)
3. Seguir checklist de implementación
4. Probar flujo completo en desarrollo
5. Desplegar a producción

**Tiempo estimado:** 6-7 horas de desarrollo + 30 minutos de configuración

---

**Documento creado:** 2025-11-10
**Versión:** 1.0
**Autor:** Claude (Análisis para FriendlyMail)

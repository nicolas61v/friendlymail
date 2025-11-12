# Setup Guide - Multi-Account Gmail + Outlook Integration

## ✅ Lo que YA está implementado (no necesitas hacer nada)

- ✅ Modelo `EmailAccount` unificado
- ✅ Soporte para múltiples Gmail y múltiples Outlook
- ✅ OutlookService con Microsoft Graph API
- ✅ Vistas y rutas completas
- ✅ Dashboard UI con provider badges
- ✅ Ordenamiento cronológico de últimos 50 emails
- ✅ Botón "Sync All" para sincronizar todo
- ✅ Migraciones de base de datos

---

## 🔧 Lo que TÚ necesitas hacer

### Paso 1: Aplicar Migraciones de Base de Datos (OBLIGATORIO)

```bash
cd /home/user/friendlymail
source venv/bin/activate
python manage.py migrate
```

Esto creará las tablas:
- `gmail_app_emailaccount` (nueva, unificada)
- Actualizará `gmail_app_email` con campos nuevos

### Paso 2: Migrar Datos Existentes (si tienes cuentas Gmail actualmente)

Si ya tienes usuarios con cuentas Gmail conectadas, ejecuta el comando de migración:

```bash
python manage.py migrate_to_emailaccount
```

Este comando:
- Copia datos de `GmailAccount` → `EmailAccount`
- Actualiza emails para usar `email_account` en lugar de `gmail_account`
- Conserva todos tus datos

### Paso 3: Registrar App en Microsoft Azure AD (Para Outlook)

**SOLO si vas a usar Outlook. Puedes saltarte este paso si solo usarás Gmail.**

#### 3.1 Ir a Azure Portal
- URL: https://portal.azure.com
- Iniciar sesión con cuenta Microsoft

#### 3.2 Crear Aplicación
1. Azure Active Directory → App registrations → New registration
2. **Name:** FriendlyMail
3. **Supported account types:** "Accounts in any organizational directory and personal Microsoft accounts"
4. **Redirect URI:**
   - Type: Web
   - URL: `http://localhost:8000/outlook/callback/`
5. Click "Register"

#### 3.3 Copiar Credenciales
En la página "Overview" de tu app, copia:
- **Application (client) ID** → Este será tu `OUTLOOK_CLIENT_ID`
- **Directory (tenant) ID** → Este será tu `OUTLOOK_TENANT_ID`

#### 3.4 Crear Client Secret
1. Ir a "Certificates & secrets"
2. Click "New client secret"
3. Description: "FriendlyMail Production"
4. Expires: 24 months
5. Click "Add"
6. **⚠️ COPIAR INMEDIATAMENTE el "Value"** → Este será tu `OUTLOOK_CLIENT_SECRET`
   - Solo se muestra una vez!

#### 3.5 Configurar Permisos API
1. Ir a "API permissions"
2. Click "Add a permission"
3. Seleccionar "Microsoft Graph"
4. Seleccionar "Delegated permissions"
5. **Agregar estos permisos:**
   - `openid`
   - `email`
   - `profile`
   - `offline_access` (¡IMPORTANTE para refresh token!)
   - `Mail.Read`
   - `Mail.Send`
   - `Mail.ReadWrite`
6. Click "Add permissions"
7. (Opcional) Click "Grant admin consent" para evitar que cada usuario apruebe

### Paso 4: Configurar Variables de Entorno

Edita tu archivo `.env.local` (o crea uno si no existe):

```bash
# ========== GMAIL (ya las tienes) ==========
GOOGLE_OAUTH2_CLIENT_ID=tu_client_id_actual.apps.googleusercontent.com
GOOGLE_OAUTH2_CLIENT_SECRET=tu_secret_actual

# ========== OUTLOOK (NUEVAS - agrégalas si vas a usar Outlook) ==========
OUTLOOK_CLIENT_ID=12345678-1234-1234-1234-123456789abc
OUTLOOK_CLIENT_SECRET=abc~XyZ123_tu_secret_de_azure
OUTLOOK_TENANT_ID=common
OUTLOOK_REDIRECT_URI=http://localhost:8000/outlook/callback/

# ========== OPENAI (ya la tienes) ==========
OPENAI_API_KEY=tu_key_actual
```

**Nota:** Si solo vas a usar Gmail, las variables de Outlook son opcionales (pero no dañan si las dejas vacías).

### Paso 5: Reiniciar el Servidor

```bash
# Si estaba corriendo, detenlo (Ctrl+C)
# Luego reinicia:
source venv/bin/activate
python manage.py runserver
```

---

## 🎉 ¡Listo! Ahora puedes usar la app

### Para conectar Gmail:
1. Ve a http://localhost:8000/dashboard/
2. Click en "Connect Gmail"
3. Autoriza en Google
4. Click "Sync All"

### Para conectar Outlook:
1. Ve a http://localhost:8000/dashboard/
2. Click en "Connect Outlook"
3. Autoriza en Microsoft
4. Click "Sync All"

### Puedes conectar:
- ✅ 1 Gmail
- ✅ Múltiples Gmails (diferentes cuentas)
- ✅ 1 Outlook
- ✅ Múltiples Outlooks
- ✅ Gmail + Outlook al mismo tiempo
- ✅ TODO lo anterior mezclado!

---

## 📧 Cómo Funciona

### Dashboard Unificado
- Muestra últimos **50 emails** de TODAS las cuentas
- Ordenados cronológicamente (más reciente primero)
- Cada email tiene badge del proveedor (Gmail icon o Outlook icon)

### Sync All
- Un solo botón sincroniza TODAS las cuentas conectadas
- Gmail: sincroniza emails de todas las cuentas Gmail
- Outlook: sincroniza emails de todas las cuentas Outlook
- Manejo de errores individual por cuenta

### Connected Accounts
- Lista todas tus cuentas conectadas
- Muestra proveedor, email, fecha de conexión
- Botón "Disconnect" para cada cuenta
- Botones "Add Gmail" / "Add Outlook" para agregar más

---

## 🔧 Troubleshooting

### Error: "No refresh token received" (Outlook)
**Causa:** Falta el scope `offline_access`
**Solución:** Verifica que `OUTLOOK_SCOPES` en settings.py incluya `'offline_access'`

### Error: "redirect_uri_mismatch" (Gmail o Outlook)
**Causa:** La URL de callback no coincide con la configurada
**Solución:**
- Gmail: Verifica en Google Cloud Console que tienes `http://localhost:8000/gmail/callback/`
- Outlook: Verifica en Azure Portal que tienes `http://localhost:8000/outlook/callback/`

### No veo emails después de conectar
**Causa:** No has sincronizado
**Solución:** Click en "Sync All" en el dashboard

### Emails no se mezclan (solo veo de un proveedor)
**Causa:** Posible error en migración
**Solución:**
1. Verifica que los emails tengan `email_account` no null: `python manage.py shell`
   ```python
   from gmail_app.models import Email
   print(Email.objects.filter(email_account__isnull=True).count())  # Debe ser 0
   ```
2. Si no es 0, re-ejecuta: `python manage.py migrate_to_emailaccount`

### Outlook no se conecta / error de permisos
**Causa:** Permisos no configurados correctamente en Azure
**Solución:**
1. Ve a Azure Portal → Tu app → API permissions
2. Asegúrate de tener TODOS los permisos de Mail (Read, Send, ReadWrite)
3. Asegúrate de tener `offline_access`
4. Click "Grant admin consent" si está disponible

---

## 📊 Estructura de Base de Datos

### Modelo EmailAccount (nuevo)
```python
user: ForeignKey(User)           # Permite múltiples cuentas
email: EmailField()              # El email de la cuenta
provider: 'gmail' | 'outlook'    # Tipo de proveedor
access_token: TextField()        # Token OAuth2
refresh_token: TextField()       # Para renovar
token_expires_at: DateTimeField()
is_active: BooleanField()        # Permite desactivar sin borrar
```

### Modelo Email (actualizado)
```python
email_account: ForeignKey(EmailAccount)  # Nueva relación unificada
provider_id: CharField()                 # ID del proveedor (gmail_id, outlook_id)
# ... resto igual
```

### Unique Constraints
- `EmailAccount`: (user, email, provider) → Evita duplicados
- `Email`: No permite duplicados por cuenta

---

## 🚀 Producción

### Para desplegar en producción:

1. **Actualizar Redirect URIs:**
   - Gmail: Google Cloud Console → Agregar `https://tudominio.com/gmail/callback/`
   - Outlook: Azure Portal → Agregar `https://tudominio.com/outlook/callback/`

2. **Actualizar .env en producción:**
   ```bash
   GOOGLE_OAUTH2_REDIRECT_URI=https://tudominio.com/gmail/callback/
   OUTLOOK_REDIRECT_URI=https://tudominio.com/outlook/callback/
   ```

3. **Migrar Base de Datos:**
   ```bash
   python manage.py migrate
   python manage.py migrate_to_emailaccount  # Si tienes datos existentes
   ```

4. **Restart servidor**

---

## 📝 Notas Importantes

### Límites de API
- **Gmail API:** 250 mensajes/segundo/usuario
- **Microsoft Graph:** 10,000 requests/10 min/app
- El sync está limitado a 50 emails por cuenta por sincronización

### Tokens OAuth2
- **Gmail:** Refresh token dura ~6 meses si no se usa
- **Outlook:** Refresh token dura ~90 días por defecto
- La app refresca automáticamente cuando detecta expiración

### Seguridad
- Tokens están encriptados en BD (usa Django secret key)
- OAuth2 state parameter previene CSRF
- Solo tú tienes acceso a tus emails
- Puedes revocar acceso desde Google/Microsoft en cualquier momento

---

## ❓ ¿Necesitas ayuda?

Si algo no funciona:
1. Revisa los logs: `logs/app.log`
2. Verifica que las migraciones se aplicaron: `python manage.py showmigrations gmail_app`
3. Verifica variables de entorno: `python manage.py shell` → `from django.conf import settings` → `print(settings.OUTLOOK_CLIENT_ID)`
4. Revisa la sección Troubleshooting arriba

---

**¡Disfruta tu dashboard unificado con Gmail + Outlook!** 🎉

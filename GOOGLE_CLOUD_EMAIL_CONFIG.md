# Guía: Configurar Google Cloud para que el Email Funcione Correctamente en AWS

## IMPORTANTE: Cambios Necesarios en Google Cloud cuando despliegues en AWS

El problema principal es que **las URLs de callback (redirect URIs) deben apuntar a tu dominio en AWS**, no a localhost.

---

## 1. Actualizar OAuth2 en Google Cloud Console

### Paso 1: Ir a Google Cloud Console
```
https://console.cloud.google.com/
```

### Paso 2: Ir a "Credenciales" → "OAuth 2.0 Client IDs"
- Selecciona tu aplicación web existente (la que creaste para desarrollo)

### Paso 3: Actualizar "Authorized redirect URIs"

**ELIMINA:**
```
http://localhost:8000/auth/google/callback/
http://localhost:8000/accounts/google/login/callback/
http://127.0.0.1:8000/auth/google/callback/
```

**AGREGA TUS NUEVAS URLS EN AWS:**
```
https://yourdomain.com/auth/google/callback/
https://www.yourdomain.com/auth/google/callback/
https://yourdomain.com/accounts/google/login/callback/
https://www.yourdomain.com/accounts/google/login/callback/
```

Ejemplo si usas Elastic Beanstalk:
```
https://friendlymail.elasticbeanstalk.com/auth/google/callback/
https://www.friendlymail.elasticbeanstalk.com/auth/google/callback/
```

### Paso 4: Agregar también en "Authorized JavaScript origins"
```
https://yourdomain.com
https://www.yourdomain.com
https://friendlymail.elasticbeanstalk.com
```

---

## 2. Actualizar settings.py en tu proyecto

### Archivo: `friendlymail/settings.py`

En desarrollo (localhost):
```python
if DEBUG:
    ALLOWED_HOSTS = ['localhost', '127.0.0.1']
else:
    ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com', 'friendlymail.elasticbeanstalk.com']
```

---

## 3. Configurar Gmail API en Google Cloud

### Paso 1: Habilitar Gmail API
1. Ve a Google Cloud Console
2. Busca "Gmail API"
3. Haz click en "Enable"

### Paso 2: Configurar pantalla de consentimiento
1. Ve a "OAuth consent screen"
2. Selecciona "External" (si aún no lo has hecho)
3. Completa:
   - App name: "FriendlyMail"
   - User support email: tu email
   - Developer contact: tu email

### Paso 3: Agregar "scopes" (permisos)
En "Scopes", asegúrate de que estén estos:
```
https://www.googleapis.com/auth/gmail.readonly
https://www.googleapis.com/auth/gmail.modify
https://www.googleapis.com/auth/gmail.send
https://www.googleapis.com/auth/calendar
```

### Paso 4: Agregar usuarios de prueba (en desarrollo)
1. Ve a "Test users"
2. Agrega tu email (el que usas para probar)
3. Esto es necesario en modo "External"

---

## 4. Configurar variables de entorno en AWS

En tu archivo `.env` o variables en AWS:

```env
# Gmail OAuth2
GOOGLE_OAUTH2_CLIENT_ID=329431518363-xxxxxxxxxxxxxxx.apps.googleusercontent.com
GOOGLE_OAUTH2_CLIENT_SECRET=GOCSPX-xxxxxxxxxxxxxxx

# Email settings
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-gmail@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Gmail API settings
GMAIL_API_SCOPES=https://www.googleapis.com/auth/gmail.readonly,https://www.googleapis.com/auth/gmail.modify,https://www.googleapis.com/auth/gmail.send
```

---

## 5. IMPORTANTE: Configurar "App Password" en Gmail (si necesitas SMTP)

Si usas autenticación SMTP directa (no OAuth):

### Paso 1: Habilitar 2FA en tu Gmail
1. Ve a myaccount.google.com/security
2. Busca "2-Step Verification"
3. Habilítalo

### Paso 2: Crear App Password
1. Ve a myaccount.google.com/apppasswords
2. Selecciona:
   - App: Mail
   - Device: Windows Computer (o la que uses)
3. Google te generará una contraseña de 16 caracteres
4. Úsala en `EMAIL_HOST_PASSWORD`

---

## 6. Verificar funcionamiento en AWS

### Test 1: Ver si la API de Gmail funciona
```bash
python manage.py shell
```

```python
from gmail_app.gmail_service import GmailService
from django.contrib.auth.models import User

user = User.objects.first()  # Tu usuario
service = GmailService(user)
emails = service.sync_emails()
print(f"Se sincronizaron {len(emails)} emails")
```

### Test 2: Ver si el auto-send funciona
```bash
python manage.py auto_sync_emails
```

Deberías ver mensajes como:
```
Sincronizando 1 cuentas...
  [tu-usuario] 3 emails sincronizados
    ├─ IA procesó 3 emails
    ├─ 2 respuestas generadas
    └─ 1 respuestas AUTO-ENVIADAS
```

---

## 7. Problemas comunes y soluciones

### Problema: "Redirect URI mismatch"
**Solución:** Verifica que la URL de callback en Google Cloud coincida exactamente con la de tu app (con https, sin trailing slash, etc.)

### Problema: "Invalid client secret"
**Solución:** Asegúrate de estar usando las credenciales correctas. Si cambias de dominio, crea nuevas credenciales en Google Cloud.

### Problema: "Gmail API not enabled"
**Solución:**
1. Ve a Google Cloud Console
2. Busca "Gmail API"
3. Haz click en "Enable"

### Problema: "Insufficient scopes"
**Solución:** Agrega los scopes requeridos en Google Cloud Console bajo "Scopes"

### Problema: Los emails no se sincronizan automáticamente
**Solución:**
1. Verifica que APScheduler esté configurado correctamente
2. Revisa los logs en AWS
3. Ejecuta manualmente: `python manage.py auto_sync_emails`

---

## 8. Configurar APScheduler para que funcione en AWS

### Archivo: `friendlymail/settings.py`

```python
APSCHEDULER_DATETIME_FORMAT = "N j, Y, f:s a"

SCHEDULER_CONFIG = {
    'apscheduler.jobstores.default': {
        'class': 'apscheduler.jobstores.memory:MemoryJobStore'
    },
    'apscheduler.executors.default': {
        'class': 'apscheduler.executors.pool:ThreadPoolExecutor',
        'max_workers': '10'
    },
    'apscheduler.timezone': 'UTC',
}

INSTALLED_APPS = [
    # ...
    'django_apscheduler',
]
```

### Cron job en AWS (Elastic Beanstalk)

Crear archivo: `.ebextensions/cron.config`

```yaml
commands:
  01_create_cron:
    command: |
      echo "*/5 * * * * /var/app/venv/*/bin/python /var/app/current/manage.py auto_sync_emails" | crontab -
    ignoreErrors: true
```

Esto ejecutará `auto_sync_emails` cada 5 minutos.

---

## 9. Monitoreo en AWS

### CloudWatch Logs
```bash
aws logs tail /aws/elasticbeanstalk/friendlymail-env/var/log/eb-engine.log --follow
```

### Verificar que los emails se sincronizan
```bash
aws logs filter-log-events \
  --log-group-name /aws/elasticbeanstalk/friendlymail-env/var/log/eb-engine.log \
  --filter-pattern "auto_sync_emails"
```

---

## RESUMEN CHECKLIST

- [ ] Actualizar "Authorized redirect URIs" en Google Cloud
- [ ] Actualizar "Authorized JavaScript origins" en Google Cloud
- [ ] Habilitar Gmail API en Google Cloud
- [ ] Configurar pantalla de consentimiento
- [ ] Agregar scopes correctos
- [ ] Actualizar ALLOWED_HOSTS en settings.py
- [ ] Configurar variables de entorno en AWS
- [ ] Probar con `python manage.py shell`
- [ ] Probar con `python manage.py auto_sync_emails`
- [ ] Configurar cron job en AWS
- [ ] Configurar CloudWatch para monitoreo
- [ ] Probar login con Google en AWS
- [ ] Probar sincronización automática de emails

---

## CONCLUSIÓN

Los cambios principales son:
1. **Google Cloud:** Actualizar URLs de callback a tu dominio AWS
2. **Django settings:** Actualizar ALLOWED_HOSTS
3. **AWS:** Configurar variables de entorno correctamente
4. **Cron:** Configurar sincronización automática con cron job

El resto de la funcionalidad sigue siendo igual.

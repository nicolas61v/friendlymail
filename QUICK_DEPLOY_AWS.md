# Desplegar FriendlyMail en AWS - FORMA MÁS FÁCIL

Este es el camino más rápido y sencillo. Sin complicaciones.

---

## PASO 1: Preparar tu proyecto local (5 min)

### 1.1 Actualizar requirements.txt
```bash
pip freeze > requirements.txt
```

### 1.2 Actualizar settings.py
En `friendlymail/settings.py`:

```python
# Antes
ALLOWED_HOSTS = ['*']

# Después
import os
if os.getenv('DEBUG', 'False') == 'True':
    ALLOWED_HOSTS = ['localhost', '127.0.0.1']
else:
    ALLOWED_HOSTS = [
        'yourdomain.com',
        'www.yourdomain.com',
        'friendlymail.elasticbeanstalk.com'
    ]
```

### 1.3 Crear archivo Procfile
Crear archivo: `Procfile` (en la raíz del proyecto)

```
web: gunicorn friendlymail.wsgi
release: python manage.py migrate
```

### 1.4 Hacer commit
```bash
git add .
git commit -m "Prepare for AWS deployment"
git push origin main
```

---

## PASO 2: Crear cuenta en AWS (si no tienes) (10 min)

1. Ve a https://aws.amazon.com
2. Click en "Create an AWS Account"
3. Sigue los pasos (necesitarás tarjeta de crédito, pero es gratis el primer año)

---

## PASO 3: Crear credenciales AWS (10 min)

### 3.1 Ir a IAM
1. Ve a https://console.aws.amazon.com/iam
2. Click en "Users" en el menú izquierdo
3. Click en "Create user"

### 3.2 Crear usuario para Elastic Beanstalk
```
Username: friendlymail-deployer
```

### 3.3 Agregar permisos
1. En "Permissions", click en "Attach policies directly"
2. Busca y selecciona: **AdministratorAccess** (para simplificar)
3. Click "Create user"

### 3.4 Crear access keys
1. Click en el usuario que creaste
2. Ve a "Security credentials"
3. Click en "Create access key"
4. Selecciona "Command Line Interface (CLI)"
5. Copia: **Access Key** y **Secret Access Key**

---

## PASO 4: Instalar AWS CLI (5 min)

### 4.1 Instalar
```bash
pip install awsebcli awscli
```

### 4.2 Configurar credenciales
```bash
aws configure
```

Ingresa:
```
AWS Access Key ID: [tu-access-key]
AWS Secret Access Key: [tu-secret-key]
Default region name: us-east-1
Default output format: json
```

---

## PASO 5: Desplegar con Elastic Beanstalk (10 min)

### 5.1 Inicializar Elastic Beanstalk
```bash
cd tu-proyecto
eb init
```

Cuando te pida:
- Select region: **3** (us-east-1)
- Application name: **friendlymail**
- Python version: **Python 3.11**
- CodeCommit: **n**
- SSH: **n**

### 5.2 Crear entorno
```bash
eb create friendlymail-env \
  --database.engine postgres \
  --database.version 15.3 \
  --database.size db.t3.micro \
  --instance-type t3.micro
```

Esto tardará **5-10 minutos**. Espera a que termine.

### 5.3 Configurar variables de entorno
```bash
eb setenv \
  DEBUG=False \
  DJANGO_SECRET_KEY="django-insecure-your-secret-key-here" \
  GOOGLE_OAUTH2_CLIENT_ID="329431518363-xxxxxxx.apps.googleusercontent.com" \
  GOOGLE_OAUTH2_CLIENT_SECRET="GOCSPX-xxxxxxx" \
  OPENAI_API_KEY="sk-proj-xxxxxxx"
```

### 5.4 Esperar a que se actualice
```bash
eb status
```

Deberías ver: `Status: Ready`

---

## PASO 6: Verificar que funciona (5 min)

### 6.1 Obtener URL
```bash
eb open
```

Se abrirá tu app en el navegador. Deberías ver la página de login.

### 6.2 Probar funcionalidad
1. Login con Google
2. Conectar Gmail
3. Ver que los emails se sincronizan

### 6.3 Ver logs si algo falla
```bash
eb logs
```

---

## PASO 7: Actualizar Google Cloud (IMPORTANTE!!)

Cuando despliegues, Google Cloud ya no reconocerá tus URLs. Necesitas actualizarlas.

### 7.1 Obtener la URL de tu app
Cuando hagas `eb open`, obtendrás algo como:
```
https://friendlymail-env.us-east-1.elasticbeanstalk.com
```

O si tienes dominio personalizado:
```
https://yourdomain.com
```

### 7.2 Ir a Google Cloud Console
https://console.cloud.google.com/

### 7.3 Actualizar Authorized redirect URIs
1. Ve a "APIs & Services" → "Credentials"
2. Click en tu OAuth 2.0 Client ID
3. En "Authorized redirect URIs" **REEMPLAZA** con:

```
https://friendlymail-env.us-east-1.elasticbeanstalk.com/auth/google/callback/
https://friendlymail-env.us-east-1.elasticbeanstalk.com/accounts/google/login/callback/
```

O si tienes dominio:
```
https://yourdomain.com/auth/google/callback/
https://www.yourdomain.com/auth/google/callback/
https://yourdomain.com/accounts/google/login/callback/
https://www.yourdomain.com/accounts/google/login/callback/
```

### 7.4 Agregar en "Authorized JavaScript origins"
```
https://friendlymail-env.us-east-1.elasticbeanstalk.com
```

O si tienes dominio:
```
https://yourdomain.com
https://www.yourdomain.com
```

### 7.5 Copiar nuevas credenciales
1. Copia tu nuevo Client ID y Secret
2. Actualiza en AWS:

```bash
eb setenv \
  GOOGLE_OAUTH2_CLIENT_ID="nuevo-id" \
  GOOGLE_OAUTH2_CLIENT_SECRET="nuevo-secret"
```

---

## PASO 8: (OPCIONAL) Usar dominio personalizado

### 8.1 Comprar dominio
Puedes usar:
- Route 53 (AWS) - $12/año
- Namecheap - $5-10/año
- GoDaddy - $10-15/año

### 8.2 Configurar en AWS Route 53
```bash
# Crear zona
aws route53 create-hosted-zone \
  --name tudominio.com \
  --caller-reference timestamp
```

### 8.3 Apuntar a Elastic Beanstalk
1. Ve a Route 53 → Hosted Zones → tu dominio
2. Crea un registro A con alias a tu EB environment

### 8.4 Actualizar Google Cloud NUEVAMENTE
Ahora usa `https://tudominio.com` en lugar de `https://friendlymail-env.us-east-1.elasticbeanstalk.com`

---

## PASO 9: CI/CD automático (BONUS)

Ya creaste el archivo `.github/workflows/deploy.yml`, pero necesitas configurar los secrets en GitHub:

### 9.1 Ir a GitHub
1. Tu repositorio → Settings → Secrets and variables → Actions
2. Click "New repository secret"

### 9.2 Agregar secrets
```
AWS_ACCESS_KEY_ID = [tu-access-key]
AWS_SECRET_ACCESS_KEY = [tu-secret-key]
```

### 9.3 Ahora, cada vez que hagas git push
```bash
git push origin main
```

GitHub automáticamente desplegará a AWS. ¡Sin hacer nada!

---

## PROBLEMAS COMUNES

### "Redirect URI mismatch" cuando hago login
**Solución:** Actualizar Google Cloud console con tu nueva URL de AWS (Paso 7)

### "ModuleNotFoundError" en los logs
**Solución:** Asegúrate de que requirements.txt esté completo:
```bash
pip freeze > requirements.txt
```

### "ALLOWED_HOSTS" error
**Solución:** Actualizar ALLOWED_HOSTS en settings.py con tu URL de AWS

### Los emails no se sincronizan
**Solución:** Ver logs:
```bash
eb logs
eb ssh
python manage.py auto_sync_emails
```

---

## COSTOS

AWS tiene una capa gratuita. Con esta configuración:

- **Elastic Beanstalk + EC2 t3.micro:** Gratis (primer año)
- **RDS PostgreSQL t3.micro:** Gratis (primer año)
- **Data transfer:** Primeros 1 GB gratis/mes

**Después del primer año:** ~$15-20/mes

---

## SIGUIENTE PASO

Una vez desplegado, puedes:

1. Configurar un dominio personalizado
2. Configurar SSL/TLS (HTTPS)
3. Agregar usuarios finales
4. Monitorear con CloudWatch

---

## RESUMEN RÁPIDO

```bash
# Paso 1: Preparar
pip freeze > requirements.txt
git add . && git commit -m "Deploy" && git push

# Paso 2-3: Crear credenciales AWS

# Paso 4: Instalar herramientas
pip install awsebcli awscli

# Paso 5: Desplegar
eb init
eb create friendlymail-env --database.engine postgres --database.size db.t3.micro
eb setenv DEBUG=False DJANGO_SECRET_KEY="..." # etc

# Paso 6: Verificar
eb open

# Paso 7: Actualizar Google Cloud (IMPORTANTE!)
```

¡Eso es todo! 🚀

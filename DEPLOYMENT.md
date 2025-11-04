# 🚀 Deployment en AWS EC2

Guía completa para desplegar FriendlyMail en Amazon EC2 con sincronización automática de emails.

## 📋 Requisitos Previos

- Cuenta de AWS
- Par de claves SSH configurado
- Credenciales de Google OAuth 2.0
- API Key de OpenAI

---

## 🖥️ Paso 1: Crear Instancia EC2

### 1.1 Configuración Recomendada

- **AMI**: Ubuntu Server 22.04 LTS
- **Tipo de Instancia**: t2.small o superior (mínimo 2GB RAM)
- **Almacenamiento**: 20GB GP3
- **Security Group**: Abrir puertos 22 (SSH), 80 (HTTP), 443 (HTTPS)

### 1.2 Security Group Rules

```
Inbound Rules:
- SSH (22)      : Tu IP / 0.0.0.0/0
- HTTP (80)     : 0.0.0.0/0
- HTTPS (443)   : 0.0.0.0/0
- Custom (8000) : 0.0.0.0/0  (para desarrollo)
```

---

## 🔧 Paso 2: Configuración Inicial del Servidor

### 2.1 Conectar por SSH

```bash
ssh -i tu-clave.pem ubuntu@tu-ec2-ip
```

### 2.2 Actualizar Sistema

```bash
sudo apt update && sudo apt upgrade -y
```

### 2.3 Instalar Dependencias

```bash
# Python y herramientas
sudo apt install -y python3-pip python3-venv nginx git supervisor

# PostgreSQL (recomendado para producción)
sudo apt install -y postgresql postgresql-contrib
```

---

## 📦 Paso 3: Clonar y Configurar Proyecto

### 3.1 Clonar Repositorio

```bash
cd /home/ubuntu
git clone https://github.com/nicolas61v/friendlymail.git
cd friendlymail
```

### 3.2 Crear Entorno Virtual

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3.3 Configurar Variables de Entorno

```bash
nano .env.local
```

Agregar:

```env
# Django
SECRET_KEY=tu-secret-key-super-segura-aqui
DEBUG=False
ALLOWED_HOSTS=tu-dominio.com,tu-ec2-ip

# Google OAuth
GOOGLE_OAUTH2_CLIENT_ID=tu-client-id.apps.googleusercontent.com
GOOGLE_OAUTH2_CLIENT_SECRET=tu-client-secret

# OpenAI
OPENAI_API_KEY=sk-tu-api-key-aqui
OPENAI_MODEL=gpt-4o-mini

# Auto-sync (minutos)
AUTO_SYNC_INTERVAL_MINUTES=20

# Database (si usas PostgreSQL)
DB_NAME=friendlymail
DB_USER=friendlymail_user
DB_PASSWORD=tu-password-seguro
DB_HOST=localhost
DB_PORT=5432
```

---

## 🗄️ Paso 4: Configurar Base de Datos (PostgreSQL)

### 4.1 Crear Base de Datos

```bash
sudo -u postgres psql

CREATE DATABASE friendlymail;
CREATE USER friendlymail_user WITH PASSWORD 'tu-password-seguro';
ALTER ROLE friendlymail_user SET client_encoding TO 'utf8';
ALTER ROLE friendlymail_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE friendlymail_user SET timezone TO 'America/Bogota';
GRANT ALL PRIVILEGES ON DATABASE friendlymail TO friendlymail_user;
\q
```

### 4.2 Actualizar settings.py para PostgreSQL

```python
# En friendlymail/settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'friendlymail'),
        'USER': os.environ.get('DB_USER', 'friendlymail_user'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}
```

### 4.3 Migrar Base de Datos

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4.4 Crear Superusuario

```bash
python manage.py createsuperuser
```

---

## ⚙️ Paso 5: Configurar Gunicorn

### 5.1 Instalar Gunicorn

```bash
pip install gunicorn
```

### 5.2 Crear archivo de configuración

```bash
nano gunicorn_config.py
```

Contenido:

```python
import multiprocessing

bind = "127.0.0.1:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
keepalive = 5
errorlog = "/home/ubuntu/friendlymail/logs/gunicorn-error.log"
accesslog = "/home/ubuntu/friendlymail/logs/gunicorn-access.log"
loglevel = "info"
```

---

## 🔄 Paso 6: Configurar Supervisor (para Gunicorn y Scheduler)

### 6.1 Crear configuración de Supervisor

```bash
sudo nano /etc/supervisor/conf.d/friendlymail.conf
```

Contenido:

```ini
[program:friendlymail]
directory=/home/ubuntu/friendlymail
command=/home/ubuntu/friendlymail/venv/bin/gunicorn friendlymail.wsgi:application -c gunicorn_config.py
user=ubuntu
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/home/ubuntu/friendlymail/logs/supervisor.log

[program:friendlymail_scheduler]
directory=/home/ubuntu/friendlymail
command=/home/ubuntu/friendlymail/venv/bin/python manage.py auto_sync_emails
user=ubuntu
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/home/ubuntu/friendlymail/logs/scheduler.log
```

### 6.2 Crear directorio de logs

```bash
mkdir -p /home/ubuntu/friendlymail/logs
touch /home/ubuntu/friendlymail/logs/app.log
```

### 6.3 Actualizar y arrancar Supervisor

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start friendlymail
sudo supervisorctl start friendlymail_scheduler
```

### 6.4 Verificar Estado

```bash
sudo supervisorctl status
```

Deberías ver:

```
friendlymail                     RUNNING   pid 1234, uptime 0:00:05
friendlymail_scheduler           RUNNING   pid 1235, uptime 0:00:05
```

---

## 🌐 Paso 7: Configurar Nginx

### 7.1 Crear configuración de Nginx

```bash
sudo nano /etc/nginx/sites-available/friendlymail
```

Contenido:

```nginx
server {
    listen 80;
    server_name tu-dominio.com tu-ec2-ip;

    client_max_body_size 10M;

    location /static/ {
        alias /home/ubuntu/friendlymail/staticfiles/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 7.2 Activar sitio

```bash
sudo ln -s /etc/nginx/sites-available/friendlymail /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 🔒 Paso 8: Configurar SSL con Let's Encrypt (Opcional pero Recomendado)

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d tu-dominio.com
```

---

## 🎯 Paso 9: Configurar Sincronización Automática

La sincronización ya está configurada para ejecutarse cada 20 minutos automáticamente.

### 9.1 Cambiar intervalo (opcional)

Editar `.env.local`:

```env
# Para sincronizar cada 10 minutos
AUTO_SYNC_INTERVAL_MINUTES=10

# Para sincronizar cada 5 minutos
AUTO_SYNC_INTERVAL_MINUTES=5
```

Luego reiniciar:

```bash
sudo supervisorctl restart friendlymail
```

### 9.2 Verificar que funciona

```bash
# Ver logs del scheduler
tail -f /home/ubuntu/friendlymail/logs/scheduler.log

# Ver logs de la app
tail -f /home/ubuntu/friendlymail/logs/app.log
```

Deberías ver cada 20 minutos:

```
⏰ Iniciando sincronización automática...
  [usuario1] 5 emails sincronizados
    ├─ IA procesó 5 emails
    └─ 3 respuestas generadas
✅ Sincronización automática completada
```

---

## 🛠️ Comandos Útiles

### Ver estado de servicios

```bash
sudo supervisorctl status
sudo systemctl status nginx
```

### Reiniciar servicios

```bash
sudo supervisorctl restart friendlymail
sudo supervisorctl restart friendlymail_scheduler
sudo systemctl restart nginx
```

### Ver logs

```bash
# Logs de la aplicación
tail -f /home/ubuntu/friendlymail/logs/app.log

# Logs del scheduler
tail -f /home/ubuntu/friendlymail/logs/scheduler.log

# Logs de Gunicorn
tail -f /home/ubuntu/friendlymail/logs/gunicorn-error.log

# Logs de Nginx
sudo tail -f /var/log/nginx/error.log
```

### Ejecutar sincronización manual

```bash
cd /home/ubuntu/friendlymail
source venv/bin/activate
python manage.py auto_sync_emails
```

### Sincronizar solo para un usuario

```bash
python manage.py auto_sync_emails --user nombre_usuario
```

---

## 📊 Monitoreo y Mantenimiento

### Verificar que el scheduler está funcionando

```bash
# Ver procesos
ps aux | grep "auto_sync"

# Ver logs en tiempo real
tail -f /home/ubuntu/friendlymail/logs/app.log | grep "sincronización"
```

### Limpiar logs antiguos (opcional)

```bash
# Crear un cron job para limpiar logs
crontab -e

# Agregar (limpia logs mayores a 30 días, cada semana)
0 0 * * 0 find /home/ubuntu/friendlymail/logs -name "*.log" -mtime +30 -delete
```

---

## 🔧 Troubleshooting

### El scheduler no inicia

```bash
# Ver logs de supervisor
sudo tail -f /var/log/supervisor/supervisord.log

# Verificar permisos
sudo chown -R ubuntu:ubuntu /home/ubuntu/friendlymail
```

### Emails duplicados

No debería pasar porque `gmail_id` es único, pero si ocurre:

```bash
# Verificar en Django shell
python manage.py shell

from gmail_app.models import Email
duplicates = Email.objects.values('gmail_id').annotate(count=Count('gmail_id')).filter(count__gt=1)
print(duplicates)
```

### La IA no procesa emails

```bash
# Verificar que OPENAI_API_KEY esté configurado
python manage.py shell

from django.conf import settings
print(settings.OPENAI_API_KEY)
```

---

## 🎉 ¡Listo!

Tu aplicación ahora está:

- ✅ Ejecutándose en EC2 24/7
- ✅ Sincronizando emails automáticamente cada 20 minutos
- ✅ Procesando con IA automáticamente
- ✅ Sin duplicar correos (protegido por `gmail_id` único)
- ✅ Con logs para debugging
- ✅ Listo para escalar

---

## 📈 Próximos Pasos (Opcional)

1. **Configurar dominio personalizado** con Route 53
2. **Configurar SSL** con Let's Encrypt
3. **Agregar CloudWatch** para monitoreo
4. **Configurar backups automáticos** de la base de datos
5. **Escalar horizontalmente** con Load Balancer si es necesario

---

## 🆘 Soporte

Para reportar problemas o pedir ayuda:
- GitHub Issues: https://github.com/nicolas61v/friendlymail/issues
- Logs: Siempre incluir los logs al reportar problemas

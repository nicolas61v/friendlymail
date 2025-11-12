# Guía Completa: Desplegar FriendlyMail en AWS

## 1. Preparación del Proyecto

### 1.1 Actualizar requirements.txt
```bash
pip freeze > requirements.txt
```

Debe incluir:
```
Django==4.2.15
python-dotenv==1.0.0
google-auth==2.28.2
google-auth-oauthlib==1.2.0
google-auth-httplib2==0.2.0
google-api-python-client==2.124.0
msal==1.31.1
requests==2.32.5
openai==1.51.0
django-apscheduler==0.6.2
gunicorn==21.2.0
psycopg2-binary==2.9.9
boto3==1.34.0
```

### 1.2 Crear archivos de configuración

#### Archivo: `.aws-env.example`
```
DJANGO_SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DATABASE_URL=postgresql://user:password@db-host:5432/friendlymail
OPENAI_API_KEY=sk-proj-xxxxx
GOOGLE_OAUTH2_CLIENT_ID=xxxxx
GOOGLE_OAUTH2_CLIENT_SECRET=xxxxx
MICROSOFT_CLIENT_ID=xxxxx
MICROSOFT_CLIENT_SECRET=xxxxx
AWS_ACCESS_KEY_ID=xxxxx
AWS_SECRET_ACCESS_KEY=xxxxx
AWS_STORAGE_BUCKET_NAME=friendlymail-media
AWS_S3_REGION_NAME=us-east-1
```

#### Archivo: `friendlymail/wsgi.py` (verificar)
```python
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'friendlymail.settings')

application = get_wsgi_application()
```

#### Archivo: `Procfile`
```
web: gunicorn friendlymail.wsgi
release: python manage.py migrate
```

---

## 2. Opción A: Desplegar en AWS Elastic Beanstalk (RECOMENDADO - MÁS FÁCIL)

### Paso 1: Instalar herramientas
```bash
pip install awsebcli
aws configure
```

### Paso 2: Inicializar Elastic Beanstalk
```bash
eb init -p python-3.11 friendlymail --region us-east-1
```

Selecciona:
- Región: us-east-1
- SSH: No (por ahora)

### Paso 3: Crear entorno
```bash
eb create friendlymail-env --database.engine postgres --database.version 15.3
```

### Paso 4: Configurar variables de entorno
```bash
eb setenv \
  DJANGO_SECRET_KEY="your-secret-key" \
  DEBUG=False \
  ALLOWED_HOSTS="friendlymail.elasticbeanstalk.com" \
  DATABASE_URL="postgresql://..." \
  OPENAI_API_KEY="sk-proj-..." \
  GOOGLE_OAUTH2_CLIENT_ID="..." \
  GOOGLE_OAUTH2_CLIENT_SECRET="..."
```

### Paso 5: Crear configuración `.ebextensions/django.config`
```yaml
option_settings:
  aws:elasticbeanstalk:application:environment:
    PYTHONPATH: /var/app/current:$PYTHONPATH
    DJANGO_SETTINGS_MODULE: friendlymail.settings
  aws:elasticbeanstalk:container:python:
    WSGIPath: friendlymail.wsgi:application

commands:
  01_migrate:
    command: "source /var/app/venv/*/bin/activate && python manage.py migrate"
    leader_only: true
  02_collectstatic:
    command: "source /var/app/venv/*/bin/activate && python manage.py collectstatic --noinput"

container_commands:
  01_migrate:
    command: "python manage.py migrate"
    leader_only: true
```

### Paso 6: Desplegar
```bash
eb deploy
```

### Paso 7: Verificar
```bash
eb status
eb logs
```

---

## 3. Opción B: Desplegar en AWS EC2 + RDS (MÁS CONTROL)

### Paso 1: Crear RDS PostgreSQL
```bash
aws rds create-db-instance \
  --db-instance-identifier friendlymail-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username admin \
  --master-user-password "your-password" \
  --allocated-storage 20 \
  --publicly-accessible
```

### Paso 2: Crear instancia EC2
```bash
aws ec2 run-instances \
  --image-ids ami-0c55b159cbfafe1f0 \
  --instance-type t3.micro \
  --key-name your-key-pair \
  --security-groups default
```

### Paso 3: Conectarse a la instancia
```bash
ssh -i your-key.pem ec2-user@your-instance-ip
```

### Paso 4: Instalar dependencias en EC2
```bash
sudo yum update -y
sudo yum install python3 python3-pip python3-devel postgresql -y
sudo pip3 install --upgrade pip
```

### Paso 5: Clonar repositorio
```bash
cd /home/ec2-user
git clone https://github.com/tu-usuario/friendlymail.git
cd friendlymail
pip3 install -r requirements.txt
```

### Paso 6: Configurar variables de entorno
```bash
sudo nano /home/ec2-user/friendlymail/.env
```

Agregar:
```
DJANGO_SECRET_KEY=your-secret-key
DEBUG=False
DATABASE_URL=postgresql://admin:password@friendlymail-db.xxxxx.us-east-1.rds.amazonaws.com:5432/friendlymail
OPENAI_API_KEY=sk-proj-xxxxx
GOOGLE_OAUTH2_CLIENT_ID=xxxxx
GOOGLE_OAUTH2_CLIENT_SECRET=xxxxx
```

### Paso 7: Configurar Gunicorn
```bash
pip3 install gunicorn
gunicorn friendlymail.wsgi:application --bind 0.0.0.0:8000
```

### Paso 8: Configurar Nginx como reverse proxy
```bash
sudo yum install nginx -y
sudo nano /etc/nginx/nginx.conf
```

Agregar en `server` block:
```nginx
location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

### Paso 9: Configurar supervisor para Gunicorn
```bash
sudo pip3 install supervisor
sudo nano /etc/supervisor/conf.d/friendlymail.conf
```

```ini
[program:friendlymail]
directory=/home/ec2-user/friendlymail
command=/usr/local/bin/gunicorn friendlymail.wsgi:application --bind 0.0.0.0:8000
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/friendlymail.log
```

---

## 4. Configurar GitHub Actions para CI/CD (AUTOMÁTICO)

### Crear archivo: `.github/workflows/deploy.yml`

```yaml
name: Deploy to AWS

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v2
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: us-east-1

    - name: Deploy to Elastic Beanstalk
      run: |
        pip install awsebcli
        eb init friendlymail --region us-east-1 --platform python-3.11
        eb deploy friendlymail-env --staged
```

---

## 5. Pasos Post-Despliegue

### Recolectar archivos estáticos
```bash
python manage.py collectstatic --noinput
```

### Crear superusuario
```bash
python manage.py createsuperuser
```

### Ejecutar migraciones
```bash
python manage.py migrate
```

---

## 6. Configurar dominio personalizado

### En AWS Route 53:
1. Crea una zona alojada
2. Agrega registros A/CNAME apuntando a tu Elastic Beanstalk

### En tu registrador de dominios:
- Apunta los nameservers a Route 53
- O crea un alias CNAME a tu EB domain

---

## 7. Configurar SSL/TLS (HTTPS)

### Opción 1: AWS Certificate Manager (GRATIS)
```bash
aws acm request-certificate \
  --domain-name tudominio.com \
  --validation-method DNS \
  --region us-east-1
```

### Opción 2: Let's Encrypt con Certbot (en EC2)
```bash
sudo yum install certbot python3-certbot-nginx -y
sudo certbot certonly --nginx -d tudominio.com
```

---

## CONCLUSIÓN

**Recomendación:**
- **Para principiantes:** Elastic Beanstalk (sencillo, escalable automáticamente)
- **Para más control:** EC2 + RDS (más barato pero requiere más mantenimiento)
- **Para CI/CD:** GitHub Actions con cualquiera de los anteriores

# 📚 Índice: Desplegar FriendlyMail en AWS

Este documento te guía por los recursos disponibles para desplegar tu app en AWS.

---

## 🚀 EMPEZAR AQUÍ

### Para principiantes (forma más fácil)
→ **Lee:** `QUICK_DEPLOY_AWS.md`

Este archivo tiene paso a paso todo lo que necesitas. No necesitas leer nada más si solo quieres desplegar rápido.

**Tiempo:** ~1 hora
**Dificultad:** 🟢 Fácil
**Resultado:** App funcionando en AWS

---

## 📖 DOCUMENTOS DISPONIBLES

### 1. QUICK_DEPLOY_AWS.md
**¿Qué es?** La forma más rápida y sencilla de desplegar.

**Contiene:**
- Setup de credenciales AWS
- Despliegue con Elastic Beanstalk
- Configuración de Google Cloud
- Verificación de funcionamiento
- CI/CD automático con GitHub

**Cuándo leerlo:** Primero, si es tu primera vez desplegando

**Cuánto tiempo:** 45 minutos

---

### 2. GOOGLE_CLOUD_CHANGES_CHECKLIST.md
**¿Qué es?** Checklist exacto de qué cambiar en Google Cloud después de desplegar.

**Contiene:**
- URLs a actualizar
- Paso a paso con screenshots
- Problemas comunes
- Verificación final

**Cuándo leerlo:** Después de desplegar en AWS (Paso 7 en QUICK_DEPLOY_AWS.md)

**Cuánto tiempo:** 10 minutos

---

### 3. GOOGLE_CLOUD_EMAIL_CONFIG.md
**¿Qué es?** Guía completa sobre configuración de emails en Google Cloud.

**Contiene:**
- OAuth2 y scopes
- Gmail API setup
- SMTP configuration
- Problemas con sincronización
- Monitoreo y debugging

**Cuándo leerlo:** Si tienes problemas con sincronización de emails

**Cuánto tiempo:** 20 minutos

---

### 4. DEPLOYMENT_AWS_GUIDE.md
**¿Qué es?** Guía detallada con todas las opciones de deployment.

**Contiene:**
- 2 opciones principales: Elastic Beanstalk vs EC2+RDS
- Setup de GitHub Actions CI/CD
- Configuración de SSL/HTTPS
- Dominio personalizado
- Estructura de proyectos

**Cuándo leerlo:** Si quieres entender todas las opciones en detalle

**Cuánto tiempo:** 1-2 horas (lectura)

---

## 🛠️ ARCHIVOS DE CONFIGURACIÓN CREADOS

Estos archivos ya están listos en tu proyecto:

### .ebextensions/django.config
- Configuración de Django para Elastic Beanstalk
- Migraciones automáticas
- Static files

### .ebextensions/cron.config
- Auto-sync de emails cada 5 minutos
- Logs automáticos

### .github/workflows/deploy.yml
- CI/CD automático con GitHub Actions
- Despliegue automático con cada git push

### Procfile
- Configuración de Gunicorn (web server)

---

## 🔄 FLUJO RECOMENDADO

```
┌─────────────────────────────────────────┐
│ 1. Leer QUICK_DEPLOY_AWS.md             │
│    (pasos 1-6: preparar y desplegar)    │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│ 2. Desplegar en AWS                     │
│    (eb init, eb create, esperar...)     │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│ 3. Leer GOOGLE_CLOUD_CHANGES_CHECKLIST  │
│    (actualizar URLs en Google Cloud)    │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│ 4. Probar funcionamiento                │
│    (login con Google, sincronización)   │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│ 5. (Opcional) Configurar dominio        │
│    y HTTPS con Route 53                 │
└─────────────────────────────────────────┘
```

---

## ⚡ QUICK REFERENCE

### Comandos más usados
```bash
# Ver estado
eb status

# Ver logs
eb logs

# Abrir app en navegador
eb open

# Configurar variables de entorno
eb setenv CLAVE=valor

# Desplegar cambios
git push origin main  # (si tienes CI/CD) o eb deploy

# Conectarse por SSH
eb ssh

# Terminar ambiente (para ahorrar costos)
eb terminate
```

---

## 💰 COSTOS

### Primer año (gratis con AWS Free Tier)
- Elastic Beanstalk: Gratis
- EC2 t3.micro: Gratis
- RDS PostgreSQL t3.micro: Gratis
- 1 GB data transfer: Gratis

### Después del primer año
- EC2 t3.micro: ~$8/mes
- RDS t3.micro: ~$15/mes
- Data transfer: ~$1/mes
- **Total:** ~$24/mes

---

## 🆘 SOPORTE RÁPIDO

### "No veo mi archivo QUICK_DEPLOY_AWS.md"
Está en la raíz del proyecto. Abre desde tu editor o:
```bash
cat QUICK_DEPLOY_AWS.md
```

### "Tengo dudas sobre Google Cloud"
→ Leer `GOOGLE_CLOUD_CHANGES_CHECKLIST.md`

### "La sincronización de emails no funciona"
→ Leer `GOOGLE_CLOUD_EMAIL_CONFIG.md` sección "Problemas comunes"

### "Quiero entender todo en detalle"
→ Leer `DEPLOYMENT_AWS_GUIDE.md`

---

## ✅ CHECKLIST FINAL

- [ ] Instalé awsebcli: `pip install awsebcli`
- [ ] Configuré AWS: `aws configure`
- [ ] Inicialicé EB: `eb init`
- [ ] Creé entorno: `eb create`
- [ ] Actualicé Google Cloud
- [ ] Probé login con Google
- [ ] Probé sincronización de emails
- [ ] Configuré GitHub Secrets (opcional)
- [ ] El app está en vivo en AWS ✨

---

## 🎯 PRÓXIMOS PASOS (DESPUÉS DE DESPLEGAR)

1. **Dominio personalizado**
   - Compra en Route 53 o tu registrador favorito
   - Apunta a tu EB environment

2. **HTTPS/SSL**
   - AWS Certificate Manager (gratis)
   - O Let's Encrypt con Certbot

3. **Backups automáticos**
   - RDS backup retention: 7 días
   - S3 para respaldos de media files

4. **Monitoreo**
   - CloudWatch alarms
   - SNS notifications

5. **Escalabilidad**
   - Auto-scaling groups
   - Load balancer

---

## 📞 RESUMEN

- **Forma más fácil:** QUICK_DEPLOY_AWS.md + GOOGLE_CLOUD_CHANGES_CHECKLIST.md
- **Forma detallada:** DEPLOYMENT_AWS_GUIDE.md + GOOGLE_CLOUD_EMAIL_CONFIG.md
- **Forma automática:** GitHub Actions (ya configurado)

**Elige una y sigue adelante. El resto es experiencia.** 🚀

---

## ÚLTIMA COSA

Los cambios en Google Cloud que necesitas hacer son **simples**:
1. Cambiar URLs de callback
2. Cambiar Client ID y Secret
3. Listo

**La magia de AWS ya está configurada en tus archivos.** Solo sigue QUICK_DEPLOY_AWS.md y estarás bien. 😊

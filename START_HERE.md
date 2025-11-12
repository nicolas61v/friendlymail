# 🚀 START HERE: Desplegar FriendlyMail en AWS

**¡Felicidades!** Tu app de FriendlyMail está lista para producción.

---

## ⏱️ TIEMPO TOTAL: ~1 HORA

```
Preparación local:      5 minutos
Crear credenciales AWS: 10 minutos  
Desplegar en AWS:       20 minutos (mayormente automático)
Actualizar Google Cloud: 10 minutos
Probar:                 5 minutos
```

---

## 📋 LO QUE HARÁS

```
Tu computadora          →      AWS
  (local)                   (en la nube)
    ↓                          ↓
[Git Push]  ────────→  [Elastic Beanstalk]
                           ↓
                       [PostgreSQL Database]
                           ↓
                       [tu-app.elasticbeanstalk.com]
                           ↓
                       [Tu app funcionando 24/7]
```

---

## 4 ARCHIVOS PRINCIPALES

Lee en este orden:

### 1️⃣ QUICK_DEPLOY_AWS.md (45 min)
**→ LA FORMA MÁS FÁCIL**

```
Paso 1: Preparar código
Paso 2: Crear cuenta AWS
Paso 3: Crear credenciales
Paso 4: Instalar herramientas
Paso 5: Desplegar ✨ (Aquí es magia)
Paso 6: Verificar que funciona
Paso 7: Actualizar Google Cloud
Paso 8: (Opcional) Dominio personalizado
Paso 9: (Bonus) CI/CD automático
```

Sigue este archivo línea por línea. Funciona. Punto.

---

### 2️⃣ GOOGLE_CLOUD_CHANGES_CHECKLIST.md (10 min)
**→ DESPUÉS DE DESPLEGAR EN AWS**

Solo 3 cambios simples:
1. Cambiar URLs de callback
2. Cambiar Client ID y Secret
3. Listo

Sin esto, Google login no funcionará. Con esto, funciona perfecto.

---

### 3️⃣ DEPLOYMENT_INDEX.md (referencia)
**→ CUANDO NECESITES MÁS INFORMACIÓN**

Mapa de todos los documentos. Úsalo si tienes dudas o quieres entender más.

---

### 4️⃣ OTROS DOCUMENTOS (referencia avanzada)
- `DEPLOYMENT_AWS_GUIDE.md` - Opciones detalladas
- `GOOGLE_CLOUD_EMAIL_CONFIG.md` - Configuración de emails

Solo lee estos si necesitas entender detalles técnicos.

---

## 🎯 OPCIÓN RÁPIDA (RECOMENDADA)

Si tienes prisa y solo quieres que funcione:

```bash
# 1. Preparar
pip freeze > requirements.txt
git add . && git commit -m "Deploy" && git push

# 2. Instalar herramientas
pip install awsebcli awscli

# 3. Configurar AWS (necesitarás credenciales)
aws configure

# 4. Desplegar
eb init
eb create friendlymail-env --database.engine postgres --database.size db.t3.micro

# 5. Configurar variables
eb setenv DEBUG=False DJANGO_SECRET_KEY="..." GOOGLE_OAUTH2_CLIENT_ID="..." GOOGLE_OAUTH2_CLIENT_SECRET="..." OPENAI_API_KEY="..."

# 6. Verificar
eb open

# 7. Actualizar Google Cloud (ir a console.cloud.google.com)
# (Ver GOOGLE_CLOUD_CHANGES_CHECKLIST.md)

# 8. (Opcional) CI/CD automático
# (GitHub secrets + git push automático)
```

---

## ✅ CHECKLIST SUPER RÁPIDO

- [ ] Tengo credenciales AWS (access key + secret)
- [ ] Leí QUICK_DEPLOY_AWS.md
- [ ] Corrí `pip freeze > requirements.txt`
- [ ] Corrí `eb init` 
- [ ] Corrí `eb create`
- [ ] Mi app está en AWS (puedo verla con `eb open`)
- [ ] Actualicé Google Cloud URLs
- [ ] El login con Google funciona ✨
- [ ] Los emails se sincronizan correctamente

---

## 🆘 PROBLEMAS COMUNES

### "¿Dónde consigo credenciales AWS?"
→ Paso 2-3 en QUICK_DEPLOY_AWS.md

### "Veo error de Redirect URI"
→ Olvidaste actualizar Google Cloud (Paso 7 en QUICK_DEPLOY_AWS.md)

### "No aparece mi app en AWS"
→ Ver logs: `eb logs`

### "¿Cuánto me cuesta?"
→ Primer año: GRATIS (AWS Free Tier)
→ Después: ~$24/mes (pero es muy barato)

---

## 🎓 LO QUE PASARÁ

1. **Git Push** → GitHub recibe tu código
2. **GitHub Actions** → Compila y prepara tu app (automático)
3. **AWS Elastic Beanstalk** → Recibe tu app
4. **EC2 Instance** → Se levanta y ejecuta tu código
5. **PostgreSQL Database** → Se conecta
6. **App Online** → ¡Funciona en `https://...`!

Todo automático con CI/CD. Solo necesitas hacer `git push`.

---

## 📱 DESPUÉS DE DESPLEGAR

Tu app estará en:
```
https://friendlymail-env.us-east-1.elasticbeanstalk.com
```

Puedes:
1. Compartir este link
2. Agregar un dominio personalizado
3. Configurar HTTPS
4. Agregar más usuarios

---

## 🚀 SIGUIENTES PASOS

1. **Ahora:** Sigue QUICK_DEPLOY_AWS.md
2. **Después:** Sigue GOOGLE_CLOUD_CHANGES_CHECKLIST.md
3. **Luego:** Celebra que tu app está en producción 🎉

---

## 💡 TIPS

- Lee QUICK_DEPLOY_AWS.md en una pestaña
- Ten otra pestaña con AWS Console abierta
- Ten otra pestaña con Google Cloud Console abierta
- Sigue paso a paso
- Si algo no funciona, Lee los logs: `eb logs`
- Tómate un café ☕ y sé paciente (AWS tarda unos minutos)

---

## ÚLTIMA COSA

**¡No te agobies!** Este proceso es:
- ✅ Muy documentado
- ✅ Muy automatizado
- ✅ Muy probado
- ✅ Muy seguro

Simplemente sigue los pasos y funciona. Literalmente.

---

## VAMOS! 🎉

→ Abre **QUICK_DEPLOY_AWS.md** y empieza.

Te veremos en AWS. 🚀

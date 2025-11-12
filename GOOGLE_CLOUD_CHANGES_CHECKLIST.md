# ✅ CHECKLIST: Cambios en Google Cloud después de desplegar en AWS

## SITUACIÓN ACTUAL

Tu app funciona perfecto en **localhost**. Cuando despliegues en AWS, Google Cloud no reconocerá tu dominio y fallarán los logins con Google.

### Lo que pasará si NO cambias Google Cloud:
```
❌ "Redirect URI mismatch"
❌ No podrás hacer login con Google
❌ Los emails no se sincronizarán
```

---

## QUÉ CAMBIAR EN GOOGLE CLOUD (3 pasos simples)

### ANTES DE HACER NADA
1. Deploya tu app en AWS (sigue QUICK_DEPLOY_AWS.md)
2. Obtén tu URL de AWS:
   ```bash
   eb open
   # O copia la URL que ves en la terminal
   ```

Tu URL será algo como:
```
https://friendlymail-env.us-east-1.elasticbeanstalk.com
```

O si tienes dominio personalizado:
```
https://tudominio.com
```

---

## PASO 1: Ir a Google Cloud Console (2 min)

### 1.1 Abre el navegador
```
https://console.cloud.google.com/
```

### 1.2 Selecciona tu proyecto
- Click en el nombre del proyecto arriba

---

## PASO 2: Actualizar URLs de Callback (3 min)

### 2.1 Ve a "APIs & Services" → "Credentials"
```
https://console.cloud.google.com/apis/credentials
```

### 2.2 Click en tu OAuth 2.0 Client ID
- Busca el que dice "Web application" o "FriendlyMail"
- Click en su nombre para abrirlo

### 2.3 Busca "Authorized redirect URIs"

**ELIMINA ESTO:**
```
http://localhost:8000/auth/google/callback/
http://127.0.0.1:8000/auth/google/callback/
http://localhost:8000/accounts/google/login/callback/
http://127.0.0.1:8000/accounts/google/login/callback/
```

**AGREGA TU NUEVA URL (con HTTPS):**

**Opción A: Si usas Elastic Beanstalk (sin dominio personalizado)**
```
https://friendlymail-env.us-east-1.elasticbeanstalk.com/auth/google/callback/
https://friendlymail-env.us-east-1.elasticbeanstalk.com/accounts/google/login/callback/
```

**Opción B: Si tienes dominio personalizado**
```
https://tudominio.com/auth/google/callback/
https://www.tudominio.com/auth/google/callback/
https://tudominio.com/accounts/google/login/callback/
https://www.tudominio.com/accounts/google/login/callback/
```

### 2.4 Click en "SAVE"

---

## PASO 3: Actualizar JavaScript Origins (2 min)

Aún en la misma pantalla, busca "Authorized JavaScript origins"

**ELIMINA:**
```
http://localhost:8000
http://127.0.0.1:8000
```

**AGREGA:**

**Opción A: Elastic Beanstalk**
```
https://friendlymail-env.us-east-1.elasticbeanstalk.com
```

**Opción B: Dominio personalizado**
```
https://tudominio.com
https://www.tudominio.com
```

### Click en "SAVE" nuevamente

---

## PASO 4: (IMPORTANTE) Obtener nuevas credenciales (2 min)

### 4.1 Aún en la misma pantalla
Copia:
- **Client ID**
- **Client Secret**

### 4.2 Actualizar en AWS
```bash
eb setenv \
  GOOGLE_OAUTH2_CLIENT_ID="nuevo-id-que-copiaste" \
  GOOGLE_OAUTH2_CLIENT_SECRET="nuevo-secret-que-copiaste"
```

### 4.3 Esperar a que se actualice
```bash
eb status
```

Deberías ver `Status: Ready` después de 1-2 minutos.

---

## PASO 5: Verificar que funciona (2 min)

### 5.1 Abre tu app en AWS
```bash
eb open
```

### 5.2 Intenta hacer login con Google
- Click en "Continue with Google"
- Deberías poder entrar sin errores

### 5.3 Si aún ves error
```bash
eb logs
# Busca errores de "Redirect URI"
```

---

## CAMBIOS QUE YA HICIMOS AUTOMÁTICAMENTE

✅ El archivo `friendlymail/settings.py` ya tiene lógica para ALLOWED_HOSTS (Paso 3)

✅ Los archivos de configuración de AWS ya están listos (.ebextensions)

✅ GitHub Actions está configurado para CI/CD automático

✅ Las variables de entorno serán sincronizadas con el `eb setenv` command

---

## RESUMEN DE CAMBIOS EN GOOGLE CLOUD

| Antes (localhost) | Después (AWS) |
|---|---|
| http://localhost:8000/auth/google/callback/ | https://friendlymail-env.us-east-1.elasticbeanstalk.com/auth/google/callback/ |
| http://localhost:8000 | https://friendlymail-env.us-east-1.elasticbeanstalk.com |
| Client ID: antiguo | Client ID: nuevo (copia del console) |
| Client Secret: antiguo | Client Secret: nuevo (copia del console) |

---

## PARA DOMINIO PERSONALIZADO

Si tienes `tudominio.com`:

| Elemento | URL |
|---|---|
| Redirect URI | https://tudominio.com/auth/google/callback/ |
| | https://www.tudominio.com/auth/google/callback/ |
| JavaScript Origin | https://tudominio.com |
| | https://www.tudominio.com |

---

## PREGUNTAS FRECUENTES

### P: ¿Debo crear nuevas credenciales?
**R:** No necesariamente. Puedes reutilizar las mismas, solo actualiza las URLs.

### P: ¿El email dejará de funcionar?
**R:** No. La sincronización de email funciona igual. Lo que cambia es solo el login con Google.

### P: ¿Cuánto tiempo tarda en actualizar?
**R:** Los cambios en Google Cloud son instantáneos. AWS tarda 1-2 minutos en reconfigurar.

### P: ¿Qué pasa con los usuarios existentes?
**R:** Todos tus usuarios locales seguirán funcionando. Solo necesitan hacer login nuevamente con las nuevas credenciales de Google.

### P: ¿Puedo mantener dos versiones (local y AWS)?
**R:** Sí. En Google Cloud puedes tener múltiples URLs:
```
http://localhost:8000/auth/google/callback/
https://friendlymail-env.us-east-1.elasticbeanstalk.com/auth/google/callback/
```

---

## CHECKLIST FINAL

- [ ] Desplegué en AWS (QUICK_DEPLOY_AWS.md)
- [ ] Obtuve mi URL de AWS
- [ ] Fui a Google Cloud Console
- [ ] Actualicé "Authorized redirect URIs"
- [ ] Actualicé "Authorized JavaScript origins"
- [ ] Copié nuevo Client ID y Secret
- [ ] Ejecuté `eb setenv` con nuevas credenciales
- [ ] Esperé a que AWS se actualice
- [ ] Probé login con Google
- [ ] Los emails se sincronizan correctamente

---

## SI ALGO FALLA

### Ver logs
```bash
eb logs
```

### Buscar específicamente errores de Google
```bash
eb logs | grep -i "redirect\|oauth\|google"
```

### SSH a la instancia
```bash
eb ssh
```

### Ejecutar comando manualmente
```bash
cd /var/app/current
python manage.py shell
```

### Ver variables de entorno
```bash
eb printenv
```

---

## PRÓXIMO PASO

Una vez que todo funciona:
1. Configura un dominio personalizado (Route 53)
2. Configura HTTPS (Certificate Manager)
3. Configura backups automáticos (RDS)
4. Monitorea con CloudWatch

Pero por ahora, ¡enfócate en que funcione con la URL de EB!

---

**Última cosa importante:** Los cambios en Google Cloud se aplican inmediatamente, pero AWS tarda 1-2 minutos. Ten paciencia. 😊

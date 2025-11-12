# 🔧 Solución: Error 401 en Azure App Registration (Cuenta de Estudiante)

## 📌 El Problema

Cuando intentas crear una app en Azure Portal (App registrations), ves:
```
{
  "sessionId": "...",
  "subscriptionId": "",
  "resourceGroup": "",
  "errorCode": "401",
  "resourceName": "",
  "details": "Error al cargar el contenido"
}
```

**Significa:** Tu cuenta de estudiante NO tiene permisos para crear aplicaciones en Azure AD.

---

## ❓ ¿Por Qué Pasa Esto?

Las cuentas de estudiante (tuusuario@eafit.edu.co) generalmente:
1. ❌ No tienen acceso a Azure AD (Active Directory)
2. ❌ No pueden crear aplicaciones
3. ❌ Tienen permisos limitados a nivel de recurso
4. ✅ Pero SÍ pueden registrar apps de forma especial

**Solución:** Tienes varias opciones.

---

## ✅ OPCIÓN 1: Usar Cuenta Personal Microsoft (RECOMENDADO - 5 min)

Si tienes una cuenta personal Microsoft (Gmail, Hotmail, etc.):

### Pasos:
1. **Cierra sesión** de tu cuenta de estudiante en Azure Portal
2. **Abre incógnito/privado** (Ctrl+Shift+N en Chrome)
3. Ve a: https://portal.azure.com
4. **Inicia sesión** con tu cuenta personal:
   - Gmail (vinculado a Microsoft)
   - Hotmail
   - Outlook.com
   - Otra cuenta Microsoft
5. **Ahora sí** deberías poder crear apps en App registrations

### Si no tienes cuenta personal:
1. Ve a https://signup.live.com
2. Crea una cuenta Outlook.com gratuita (2 min)
3. Luego inicia sesión en Azure con esa

**Ventaja:** Súper rápido y funciona inmediatamente.

---

## ✅ OPCIÓN 2: Pedir Permisos en tu Universidad

Si **SOLO** quieres usar tu cuenta de estudiante:

### Pasos:
1. **Contacta al departamento de IT** de EAFIT:
   - Email: it@eafit.edu.co
   - O busca "IT Help Desk EAFIT"

2. **Solicita:**
   > "Necesito permisos para crear aplicaciones Azure AD.
   > Quiero registrar una app para un proyecto personal de correos.
   > Usuario: tuusuario@eafit.edu.co"

3. **Espera respuesta** (24-48 horas típicamente)

4. Una vez que te den permisos, podrás crear apps normalmente

**Ventaja:** Oficial, pero tarda tiempo.

---

## ✅ OPCIÓN 3: Usar Outlook.com Directamente (SIN Azure) - 10 min

Si no quieres usar Azure, puedes **registrar tu app en Microsoft App Portal directamente**:

### Pasos:
1. Ve a: https://apps.dev.microsoft.com
   (O https://portal.azure.com → Integrations → App registrations portal)

2. Haz clic en **"+ New app"** (o "+ Add an app")

3. Dale un nombre: **"FriendlyMail"**

4. Verás automáticamente tu **Application ID** (este es el CLIENT_ID)

5. Haz clic en **"Generate new password"** → Copia el valor (CLIENT_SECRET)

6. Agrega **Redirect URI:**
   - Haz clic en **"Add Platform"**
   - Selecciona **"Web"**
   - Escribe: `http://localhost:8000/outlook/callback/`

7. En **"Microsoft Graph Permissions"** → Selecciona:
   - `Mail.Read`
   - `Mail.Send`

8. **Guardar**

Este método es MÁS SIMPLE y no requiere Azure AD.

---

## 🎯 RECOMENDACIÓN: USA OPCIÓN 1 (La más rápida)

**Si tienes cuenta personal Microsoft o Gmail:**

```
1. Abre incógnito
2. https://portal.azure.com
3. Inicia sesión con cuenta personal (Gmail, Hotmail, etc.)
4. App registrations → + New registration
5. Nombre: FriendlyMail
6. Copia CLIENT_ID y TENANT_ID
7. Crea CLIENT_SECRET
8. Configura permisos
9. Listo en 15 minutos
```

**Si NO tienes cuenta personal:**

```
1. https://signup.live.com
2. Crea Outlook.com gratuito (2 min)
3. Regresa a Azure Portal con esa cuenta
4. Sigue pasos arriba (15 min)
```

---

## 🔑 ¿Qué es TENANT_ID con Cuenta Personal?

Cuando uses cuenta personal:
- **TENANT_ID:** Puedes usar `"common"` (permite cualquier cuenta)
- O ve a Azure AD → Tenant information → Directory ID

En `.env.local`:
```
OUTLOOK_TENANT_ID=common
```

O si quieres específico:
```
OUTLOOK_TENANT_ID=tu_tenant_id_aqui
```

---

## 📋 Pasos Completos (Opción 1 - Recomendado)

### 1. Preparar una Cuenta Personal (5 min si no tienes)

**Si tienes Gmail:**
```
Ya tienes (Google vinculado con Microsoft automáticamente)
```

**Si tienes Hotmail/Outlook:**
```
Ya tienes
```

**Si no tienes nada:**
```
1. Ve a https://signup.live.com
2. Completa el formulario
3. Verifica email
4. Tienes cuenta Outlook.com
```

### 2. Ir a Azure Portal en Incógnito

```
1. Presiona Ctrl+Shift+N (Chrome) o Ctrl+Shift+P (Firefox)
2. Ve a https://portal.azure.com
3. Haz clic en "Usar otra cuenta"
4. Inicia sesión con tu cuenta personal
```

### 3. Crear App (10 min - Sigue AZURE_SETUP_GUIDE.md)

```
1. Busca "App registrations"
2. + New registration
3. Nombre: FriendlyMail
4. Supported types: Cuentas personales + organizaciones
5. Redirect: http://localhost:8000/outlook/callback/
6. Register
```

### 4. Copiar Credenciales

```
Overview:
├─ Application (client) ID → OUTLOOK_CLIENT_ID
└─ Directory (tenant) ID → OUTLOOK_TENANT_ID (o usa "common")

Certificates & secrets:
└─ + New client secret → OUTLOOK_CLIENT_SECRET
```

### 5. Configurar Permisos

```
API permissions → + Add a permission
├─ Microsoft Graph → Delegated permissions
├─ Agregar: openid, email, profile, offline_access
├─ Agregar: Mail.Read, Mail.Send, Mail.ReadWrite
└─ Add permissions
```

### 6. Guardar en .env.local

```bash
OUTLOOK_CLIENT_ID=tu_id_aqui
OUTLOOK_CLIENT_SECRET=tu_secret_aqui
OUTLOOK_TENANT_ID=common
OUTLOOK_REDIRECT_URI=http://localhost:8000/outlook/callback/
OUTLOOK_AUTHORITY=https://login.microsoftonline.com/common
```

### 7. Listo

```
Reinicia Django y prueba "Connect Outlook"
```

---

## 🚨 Si el Error 401 Persiste

### Verifica que:

**1. Sesión cerrada de estudiante:**
```
Cierra Azure Portal completamente
Abre en incógnito/privado
```

**2. Cuentas diferentes:**
```
NO mezcles estudiante + personal en la misma pestaña
Usa una pestaña incógnito separada
```

**3. No necesitas suscripción:**
```
Azure AD free tier permite crear apps SIN suscripción
Si pide suscripción, estás en lugar equivocado
```

**4. Estás en el lugar correcto:**
```
CORRECTO: https://portal.azure.com → App registrations
INCORRECTO: Azure Subscriptions → Resource groups
```

---

## 📞 Resumen Rápido

| Problema | Solución |
|----------|----------|
| **Error 401 con @eafit.edu.co** | Usa cuenta personal (Gmail/Outlook) |
| **No tengo cuenta personal** | Crea una en https://signup.live.com |
| **¿Necesito pagar?** | No, Azure AD es gratis |
| **¿Necesito suscripción?** | No, App registrations es gratis |
| **¿Cuánto tarda?** | 5-15 minutos máximo |

---

## ✅ Checklist

- [ ] Tengo cuenta personal Microsoft (Gmail, Outlook, etc.)
- [ ] Abrí incógnito para no mezclar cuentas
- [ ] Inicié sesión en https://portal.azure.com con cuenta personal
- [ ] Puedo ver "App registrations" SIN error 401
- [ ] Creé app "FriendlyMail"
- [ ] Copié CLIENT_ID
- [ ] Copié CLIENT_SECRET
- [ ] Copié TENANT_ID
- [ ] Agregué valores a .env.local
- [ ] Configuré permisos (Mail.Read, Mail.Send)

---

## 🎯 Próximo Paso

1. **Si ya tienes cuenta personal:** Sigue la guía arriba (5-15 min)
2. **Si no tienes:** Crea Outlook.com primero (signup.live.com), luego sigue

Una vez hayas copiado las claves, completa con AZURE_SETUP_GUIDE.md paso 7-10.

**¡Listo! Ya podrás sincronizar Outlook. 🚀**


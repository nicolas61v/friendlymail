# 🔑 Guía Paso a Paso: Obtener Credenciales de Azure para Outlook

## 📌 Resumen Rápido

Necesitas 4 valores de Azure:
1. **OUTLOOK_CLIENT_ID** - Identificador de la aplicación
2. **OUTLOOK_CLIENT_SECRET** - Contraseña de la aplicación
3. **OUTLOOK_TENANT_ID** - ID del directorio
4. **OUTLOOK_AUTHORITY** - URL de autenticación (se genera automáticamente)

Tiempo estimado: **15-20 minutos**

---

## 🚀 PASO 1: Ir a Azure Portal

1. Abre tu navegador
2. Ve a: **https://portal.azure.com**
3. Inicia sesión con tu cuenta Microsoft (Outlook, Gmail o corporativa)
4. **Puede pedirte que verifiques con 2FA** - completa eso

**¿Ya estás en Azure Portal?**
- Deberías ver una pantalla como esta:
  ```
  Microsoft Azure
  ┌─────────────────────────────┐
  │ Home  Subscriptions  ...     │
  │                             │
  │ [Buscador en la parte superior]
  │                             │
  │ Recursos recientes          │
  │ ...                         │
  └─────────────────────────────┘
  ```

---

## 🔍 PASO 2: Buscar "App registrations"

**Opción A: Usando el buscador (RECOMENDADO)**
1. Mira la **parte superior de la pantalla**
2. Debería haber una barra de búsqueda que dice **"Search"**
3. Haz clic en ella
4. Escribe: **"App registrations"**
5. Presiona Enter
6. Click en el resultado que aparece

**Opción B: Usando el menú lateral (si no funciona A)**
1. Mira a la **izquierda** de la pantalla
2. Debería haber un menú con:
   - Home
   - Create a resource
   - ...
3. Busca **"Azure Active Directory"** (puede estar arriba o necesites hacer scroll)
4. Una vez dentro, busca **"App registrations"** en el menú

**¿Dónde debería estar?**
```
Azure Portal Menú Lateral
├─ Home
├─ Create a resource
├─ All services
├─ Subscriptions
├─ ...
├─ Azure Active Directory ← AQUÍ ESTÁ
│  ├─ ...
│  └─ App registrations ← O aquí
└─ ...
```

---

## ➕ PASO 3: Crear Nueva Aplicación

Una vez en "App registrations":

1. **Mira la parte superior derecha**
2. Deberías ver un botón **"+ New registration"** (puede ser azul)
3. Haz clic en él
4. Completa el formulario que aparece:

```
Name: [Campo 1]
Escribe: "FriendlyMail"

Supported account types: [Campo 2 - Radio buttons]
Selecciona: "Accounts in any organizational directory
            and personal Microsoft accounts (e.g. Skype, Xbox, Outlook.com)"
            ← Esta opción permite cualquier cuenta Microsoft

Redirect URI: [Campo 3 - Dropdown + texto]
├─ Dropdown: Selecciona "Web"
└─ Texto: http://localhost:8000/outlook/callback/

[Botón] Register
```

**¿Lo hiciste?**
→ Deberías ver la pantalla de tu nueva app "FriendlyMail"

---

## 📋 PASO 4: Copiar CLIENT ID y TENANT ID

Ahora estás en la página de "FriendlyMail" que creaste.

**Mira la pantalla - deberías ver estos campos:**

```
FriendlyMail
├─ Overview (tab activo)
│
├─ Display name: FriendlyMail
│
├─ Application (client) ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
│  ┌─────────────────────────────────────────┐
│  │ Esta es tu OUTLOOK_CLIENT_ID            │
│  │ [Botón de copiar]                       │
│  │ Cópialo y guárdalo en un notepad        │
│  └─────────────────────────────────────────┘
│
├─ Directory (tenant) ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
│  ┌─────────────────────────────────────────┐
│  │ Esta es tu OUTLOOK_TENANT_ID            │
│  │ [Botón de copiar]                       │
│  │ Cópialo y guárdalo en un notepad        │
│  └─────────────────────────────────────────┘
│
└─ ... otros campos
```

**Acciones:**
1. Busca el campo **"Application (client) ID"**
2. Cópialo (click en el ícono de copiar a la derecha)
3. Pega en tu notepad como: `OUTLOOK_CLIENT_ID = ...`
4. Haz lo mismo con **"Directory (tenant) ID"** como `OUTLOOK_TENANT_ID = ...`

---

## 🔐 PASO 5: Crear CLIENT SECRET (La Contraseña)

**Esto es CRÍTICO - te lo piden solo una vez**

1. En el menú lateral de tu app, busca **"Certificates & secrets"**
   - Deberías estar en: FriendlyMail → Certificates & secrets

```
FriendlyMail
├─ Overview
├─ Integration assistant
├─ Quickstart
├─ Certificates & secrets ← CLICK AQUÍ
├─ Token configuration
├─ API permissions
├─ App roles
└─ ...
```

2. Una vez dentro, verás tabs:
   - "Certificates"
   - "Client secrets" ← Haz clic aquí

3. Ahora haz clic en el botón azul **"+ New client secret"**

4. Se abrirá un formulario:
   ```
   Add a client secret

   Description: [Campo de texto]
   Escribe: "FriendlyMail Production"

   Expires: [Dropdown]
   Selecciona: "24 months"

   [Botón] Add
   ```

5. **¡IMPORTANTE! Después de hacer clic en "Add":**
   - Verás tu nuevo secret en una tabla
   - Hay una columna "Value" con caracteres
   - **COPIA INMEDIATAMENTE este Value**
   - NO SALGAS DE ESTA PÁGINA sin copiarlo
   - Si cierras sin copiar, no podrás verlo de nuevo

```
Client secrets
┌─────────────────────────────────────────────────────────┐
│ Description      │ Expires      │ Value                 │
│ FriendlyMail Prod│ 12/11/2026   │ abc~XyZ123_tu_secr... │
│                  │              │ [Botón de copiar]     │
└─────────────────────────────────────────────────────────┘
     ↑                                  ↑
  Mira aquí                     COPIA ESTE VALOR
```

6. Pega en tu notepad como: `OUTLOOK_CLIENT_SECRET = ...`

---

## ✅ PASO 6: Configurar Permisos API

Ahora necesitas decirle a Azure qué puede hacer tu app con el email.

1. En el menú lateral, busca **"API permissions"**
   ```
   FriendlyMail
   ├─ Overview
   ├─ Certificates & secrets
   ├─ API permissions ← CLICK AQUÍ
   └─ ...
   ```

2. Verás algo como:
   ```
   Configured permissions (vacío o con algo)
   [Botón azul] + Add a permission
   ```

3. Haz clic en **"+ Add a permission"**

4. Se abrirá una ventana. En el lado izquierdo, busca y haz clic en:
   **"Microsoft Graph"**
   ```
   Commonly used Microsoft APIs
   ├─ Microsoft Graph ← CLICK AQUÍ
   ├─ Azure Service Management
   └─ ...

   Recent APIs
   ...
   ```

5. Luego elige **"Delegated permissions"** (debería estar por defecto)

6. Ahora se abrirá una lista de permisos. Necesitas agregar estos:
   - [ ] `openid` - Busca y marca
   - [ ] `email` - Busca y marca
   - [ ] `profile` - Busca y marca
   - [ ] `offline_access` - Busca y marca
   - [ ] `Mail.Read` - Busca y marca
   - [ ] `Mail.Send` - Busca y marca
   - [ ] `Mail.ReadWrite` - Busca y marca

   **Cómo buscar:** Hay un campo de búsqueda arriba. Escribe el permiso y marca el checkbox.

7. Una vez marcados TODOS, haz clic en **"Add permissions"** (botón abajo)

8. Espera a que aparezca de vuelta en la pantalla de permisos

**¿Lo hiciste bien?**
Deberías ver en "Configured permissions":
```
Configured permissions
├─ email (Microsoft Graph) - Delegated
├─ Mail.Read (Microsoft Graph) - Delegated
├─ Mail.ReadWrite (Microsoft Graph) - Delegated
├─ Mail.Send (Microsoft Graph) - Delegated
├─ offline_access (Microsoft Graph) - Delegated
├─ openid (Microsoft Graph) - Delegated
└─ profile (Microsoft Graph) - Delegated
```

---

## 📝 PASO 7: Verificar tus Credenciales

En tu notepad deberías tener:
```
OUTLOOK_CLIENT_ID = xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
OUTLOOK_CLIENT_SECRET = abc~XyZ123_tu_secreto_aqui
OUTLOOK_TENANT_ID = xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
OUTLOOK_REDIRECT_URI = http://localhost:8000/outlook/callback/
OUTLOOK_AUTHORITY = https://login.microsoftonline.com/common
```

**Verifica que:**
- ✅ CLIENT_ID tiene formato UUID (xxxx-xxxx-xxxx...)
- ✅ CLIENT_SECRET empieza con "abc~" o similar
- ✅ TENANT_ID tiene formato UUID
- ✅ REDIRECT_URI es exacto: `http://localhost:8000/outlook/callback/`
- ✅ AUTHORITY es: `https://login.microsoftonline.com/common` (nota: `/common` no `/TENANT_ID`)

---

## 🔧 PASO 8: Agregar a tu Archivo .env.local

1. Abre tu archivo: `C:\...\friendlymail\.env.local`

2. Agrega al final:
   ```bash
   # ========================================
   # MICROSOFT OUTLOOK/OFFICE 365
   # ========================================
   OUTLOOK_CLIENT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
   OUTLOOK_CLIENT_SECRET=abc~XyZ123_tu_secreto_aqui
   OUTLOOK_TENANT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
   OUTLOOK_REDIRECT_URI=http://localhost:8000/outlook/callback/
   OUTLOOK_AUTHORITY=https://login.microsoftonline.com/common
   ```

   **Reemplaza:**
   - `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` con tu CLIENT_ID
   - `abc~XyZ123_tu_secreto_aqui` con tu CLIENT_SECRET
   - El TENANT_ID con el tuyo

3. Guarda el archivo

---

## ✨ PASO 9: Verificar en settings.py

Tu `friendlymail/settings.py` ya debería tener esto (verifica):

```python
# MICROSOFT OUTLOOK CONFIG
OUTLOOK_CLIENT_ID = os.environ.get('OUTLOOK_CLIENT_ID')
OUTLOOK_CLIENT_SECRET = os.environ.get('OUTLOOK_CLIENT_SECRET')
OUTLOOK_TENANT_ID = os.environ.get('OUTLOOK_TENANT_ID', 'common')
OUTLOOK_REDIRECT_URI = os.environ.get('OUTLOOK_REDIRECT_URI', 'http://localhost:8000/outlook/callback/')
OUTLOOK_AUTHORITY = os.environ.get('OUTLOOK_AUTHORITY', f"https://login.microsoftonline.com/{OUTLOOK_TENANT_ID}")

OUTLOOK_SCOPES = [
    'openid',
    'email',
    'profile',
    'offline_access',
    'https://graph.microsoft.com/Mail.Read',
    'https://graph.microsoft.com/Mail.Send',
    'https://graph.microsoft.com/Mail.ReadWrite'
]
```

Si no está, agrégalo. (Mira el archivo `OUTLOOK_INTEGRATION_ANALYSIS.md` sección 4.3)

---

## 🚀 PASO 10: Verificar que las Librerías estén Instaladas

Abre terminal en tu proyecto:

```bash
pip install msal requests
```

Verifica que funciona:
```bash
python -c "import msal; print('✅ msal instalado')"
python -c "import requests; print('✅ requests instalado')"
```

---

## ✅ CHECKLIST FINAL

Antes de intentar conectar Outlook:

- [ ] Creaste app en Azure Portal
- [ ] Copié OUTLOOK_CLIENT_ID (formato UUID)
- [ ] Copié OUTLOOK_CLIENT_SECRET (value del secret)
- [ ] Copié OUTLOOK_TENANT_ID (formato UUID)
- [ ] Agregué los 4 valores a `.env.local`
- [ ] settings.py tiene OUTLOOK_* variables
- [ ] Instalé `msal` y `requests`
- [ ] settings.py tiene OUTLOOK_SCOPES
- [ ] Configuré los permisos en API permissions (Mail.Read, Mail.Send, etc.)

---

## 🧪 Probar la Configuración

1. Reinicia tu servidor Django:
   ```bash
   python manage.py runserver
   ```

2. Abre tu navegador: `http://localhost:8000`

3. Inicia sesión con tu usuario FriendlyMail

4. Debería haber un botón **"Connect Outlook"** o similar

5. Haz clic en él

6. Te redirigirá a Microsoft para autorizar

7. Autorizas y deberías volver a tu app

**Si funciona:**
- ✅ Ves un mensaje de éxito
- ✅ Tu cuenta Outlook aparece conectada
- ✅ Puedes sincronizar emails

**Si no funciona:**
- Ver sección de debugging abajo

---

## 🐛 Debugging: Si Algo No Funciona

### Error 1: "OUTLOOK_CLIENT_ID not found" o similar

**Causa:** Las variables de entorno no se cargaron

**Solución:**
```bash
# 1. Verifica que .env.local existe y tiene los valores
cat .env.local | grep OUTLOOK

# 2. Reinicia el servidor
python manage.py runserver

# 3. Verifica en Django shell
python manage.py shell
from django.conf import settings
print(settings.OUTLOOK_CLIENT_ID)  # Debería mostrar tu UUID
```

### Error 2: "Invalid redirect URI"

**Causa:** El Redirect URI en Azure no coincide con el de settings.py

**Solución:**
1. Ve a Azure Portal
2. FriendlyMail → Authentication
3. Verifica que está: `http://localhost:8000/outlook/callback/`
4. Si está diferente, cámbialo o agrega otra
5. Reinicia Django

### Error 3: "No refresh token received"

**Causa:** El permiso `offline_access` no está configurado

**Solución:**
1. Ve a Azure Portal
2. FriendlyMail → API permissions
3. Busca `offline_access` en Microsoft Graph
4. Si no está, agrégalo (+ Add a permission)
5. Guarda y reinicia

### Error 4: "Invalid client secret"

**Causa:** El CLIENT_SECRET está mal copiado o expiró

**Solución:**
1. Ve a Azure Portal
2. FriendlyMail → Certificates & secrets
3. Borra el secret antiguo
4. Crea uno nuevo
5. COPIA el valor inmediatamente
6. Actualiza `.env.local`
7. Reinicia Django

---

## 📞 Resumen Rápido

```
PASO 1: https://portal.azure.com
PASO 2: Buscar "App registrations"
PASO 3: + New registration → FriendlyMail
PASO 4: Copiar Application ID y Tenant ID
PASO 5: Certificates & secrets → + New client secret
PASO 6: API permissions → Agregar Mail.Read, Mail.Send, etc.
PASO 7: Guardar valores en .env.local
PASO 8: Reiniciar Django
PASO 9: Probar "Connect Outlook"
PASO 10: Sincronizar emails
```

**Tiempo total:** 15-20 minutos

---

## 🎯 ¿Ya lo configuraste?

Próximo paso: Ve a `/connect-outlook/` en tu FriendlyMail y prueba a conectar tu cuenta Outlook.

Si funciona → ¡Listo! Ya puedes sincronizar emails de Outlook.

Si no funciona → Revisa el debugging arriba o escribe en logs/app.log


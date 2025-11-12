# ✅ Guía: Múltiples Cuentas del Mismo Proveedor

## 📌 El Problema Que Acabamos de Arreglar

**Antes:**
- Podías conectar 1 Gmail + 1 Outlook
- Si ya tenías 1 Gmail, NO aparecía el botón para agregar otro Gmail
- El template mostraba el botón solo si `not has_gmail` (es decir, 0 cuentas Gmail)

**Ahora:**
- Puedes conectar infinitas cuentas del mismo proveedor
- Aparecen siempre los botones "Add Gmail Account" y "Add Outlook Account"
- El modelo ya lo soportaba, era solo un problema de UI

---

## 🔧 Cómo Funciona la Arquitectura

### El Modelo EmailAccount

```python
class EmailAccount(models.Model):
    user = ForeignKey(User)
    email = EmailField()
    provider = CharField(['gmail', 'outlook'])

    class Meta:
        unique_together = [['user', 'email', 'provider']]
        # ↑ Previene duplicados del MISMO email del MISMO proveedor
```

**Esto permite:**

✅ `user1 + gmail1@gmail.com + gmail`
✅ `user1 + gmail2@gmail.com + gmail` ← Diferente email, misma cuenta
✅ `user1 + outlook1@outlook.com + outlook`
❌ `user1 + gmail1@gmail.com + gmail` ← Duplicado (no permitido)

### El Flujo de Conexión

```
Usuario hace clic en "Add Gmail Account"
    ↓
Redirige a Google OAuth
    ↓
Usuario autoriza (puede ser diferente email)
    ↓
handle_oauth_callback() ejecuta:
    ├─ EmailAccount.objects.update_or_create(
    │   user=user,
    │   email=profile['emailAddress'],  ← El EMAIL que autorizó
    │   provider='gmail',
    │   defaults={tokens...}
    │)
    │ ✅ Si es email diferente: crea NUEVA cuenta
    │ ✅ Si es el mismo email: actualiza tokens
    └─ Redirige a dashboard

Dashboard muestra TODAS las cuentas conectadas
```

---

## 👥 Ejemplos de Uso

### Caso 1: Profesor con Múltiples Cuentas Gmail

```
Profesor Vasquez:
├─ Gmail Personal: vasquez@gmail.com
│  └─ Usado para correspondencia personal
├─ Gmail Universidad: vasquez@eafit.edu.co
│  └─ Usado para correspondencia académica
└─ Gmail Secundario: vasquez.dev@gmail.com
   └─ Usado para cosas técnicas

En FriendlyMail:
Dashboard → Connected Accounts (3):
├─ vasquez@gmail.com (Gmail) - 45 emails
├─ vasquez@eafit.edu.co (Gmail) - 127 emails
└─ vasquez.dev@gmail.com (Gmail) - 12 emails

Unified Inbox: 184 emails (de todas las cuentas)
```

### Caso 2: Profesor con Gmail + Outlook

```
Profesor Garcia:
├─ Gmail: garcia@gmail.com (personal)
├─ Outlook: garcia@microsoft.com (empresa)
└─ Gmail: garcia@company.com (empresa Gmail)

Dashboard:
├─ 2 cuentas Gmail
├─ 1 cuenta Outlook
└─ Unified Inbox: 287 emails totales
```

---

## 🚀 Cómo Agregar Múltiples Cuentas

### Paso 1: Ve al Dashboard
```
http://localhost:8000/dashboard/
```

### Paso 2: Mira la Sección "Connected Accounts"

Deberías ver algo como:
```
Connected Accounts (2)
├─ vasquez@gmail.com (Gmail) - 45 emails
└─ vasquez@eafit.edu.co (Gmail) - 127 emails

[Add Gmail Account] [Add Outlook Account]
```

### Paso 3: Haz clic en "Add Gmail Account" (o Outlook)

El botón **siempre aparece** ahora, sin importar cuántas cuentas Gmail ya tengas.

### Paso 4: Autoriza con Google (u Outlook)

**Importante:** Puedes autorizar con:
- ✅ Un email Gmail **diferente** (crea nueva cuenta)
- ✅ El mismo email Gmail (actualiza los tokens)

### Paso 5: Eres Redirigido al Dashboard

Verás tu nueva cuenta listada:
```
Connected Accounts (3)
├─ vasquez@gmail.com (Gmail)
├─ vasquez@eafit.edu.co (Gmail)
└─ vasquez.dev@gmail.com (Gmail) ← Nueva
```

---

## 🔄 Sincronización con Múltiples Cuentas

### El Flujo de Sync

```python
dashboard.sync_all_accounts()
    ↓
Para cada EmailAccount conectada:
    ├─ GmailService.sync_emails(email_account_id=account.id)
    │  └─ Obtiene últimos 20 emails de ESA cuenta
    ├─ AIProcessor procesa esos emails (si IA está activa)
    └─ Guarda emails con email_account = esa cuenta

Resultado:
Unified Inbox muestra TODOS los emails de TODAS las cuentas
```

### Ejemplo: Sincronizar 2 Cuentas Gmail

```
Dashboard → [Sync All]
    ↓
Gmail Service:
├─ Cuenta 1: vasquez@gmail.com
│  └─ Obtiene: 20 emails
├─ Cuenta 2: vasquez@eafit.edu.co
│  └─ Obtiene: 20 emails
└─ Total: 40 nuevos emails sincronizados

Unified Inbox → 40 emails (20 de cada cuenta)
Botón de Provider muestra cuál es de cuál:
├─ "Hola Vasquez" de amigo@gmail.com [Gmail] vasquez@gmail.com
└─ "Exam Schedule" de student@example.com [Gmail] vasquez@eafit.edu.co
```

---

## 📊 Tabla: Antes vs Después

| Aspecto | Antes | Después |
|---------|-------|---------|
| **Máx cuentas Gmail** | 1 | Infinitas |
| **Máx cuentas Outlook** | 1 | Infinitas |
| **Botón "Add Gmail"** | Solo si 0 Gmail | Siempre |
| **Flujo Sync** | Solo 1 cuenta | Todas las cuentas |
| **Unified Inbox** | 1 cuenta | Todas combinadas |
| **Provider Badge** | No | Sí (muestra cuál es de cuál) |

---

## 🎯 Archivos Modificados

**dashboard.html (líneas 569-579)**

**Cambio:**
```html
<!-- ANTES: Botones condicionales -->
{% if not has_gmail or gmail_accounts.count == 0 %}
    <a href="...">Add Gmail</a>
{% endif %}

<!-- DESPUÉS: Botones siempre presentes -->
<a href="...">Add Gmail Account</a>
<a href="...">Add Outlook Account</a>
```

**Por qué:**
- Ahora puedes agregar infinitas cuentas
- Los botones deben ser siempre visibles
- El modelo y backend ya lo soportaban, solo era UI

---

## ✅ Checklist de Verificación

```
☐ Voy al Dashboard
☐ Veo mis cuentas conectadas
☐ Hago clic en "Add Gmail Account" (o Outlook)
☐ Autorizo con un email DIFERENTE
☐ Soy redirigido al Dashboard
☐ Veo la nueva cuenta en "Connected Accounts"
☐ Hago "Sync All"
☐ Los emails de ambas cuentas aparecen en Unified Inbox
☐ Cada email muestra su provider badge ([Gmail] o [Outlook])
```

---

## 🔗 Arquitectura de Enrutamiento

```
Email → EmailAccount → Sincronización → Dashboard
  ↓           ↓
provider_id   provider (gmail/outlook)
              ↓
          ¿De cuál cuenta es?
```

Cada email está vinculado a exactamente una `EmailAccount`. Cuando sincronizas, el sistema sabe:
- De cuál cuenta vino
- A cuál usuario pertenece
- Qué provider usó

---

## 📞 Preguntas Frecuentes

### P: ¿Qué pasa si intento agregar el mismo email dos veces?
**R:** Se actualiza la misma cuenta (tokens, etc). No se duplica.

```
EmailAccount.objects.update_or_create(
    user=user,
    email='vasquez@gmail.com',  # El mismo
    provider='gmail',
    defaults={...tokens...}
)
# ↑ Actualiza, no crea nueva
```

### P: ¿Los emails de múltiples cuentas aparecen juntos?
**R:** Sí, en "Unified Inbox" ordenados por fecha.

```python
emails = Email.objects.filter(
    email_account__in=email_accounts  # TODAS las cuentas del usuario
).order_by('-received_date')  # Ordenados por fecha reciente
```

### P: ¿Sincroniza todas las cuentas automáticamente?
**R:** Sí, `sync_all_accounts()` itera a través de todas:

```python
for account in email_accounts:
    gmail_service.sync_emails(email_account_id=account.id)
```

### P: ¿Puedo desconectar solo una cuenta?
**R:** Sí, hay botón de "Disconnect" para cada cuenta:

```html
<button onclick="disconnectAccount({{ item.account.id }}, ...)">
    <i class="fas fa-unlink"></i> Disconnect
</button>
```

### P: ¿El auto-send funciona en todas las cuentas?
**R:** Sí, procesa todas las cuentas del usuario (ver `auto_sync_emails.py`).

---

## 🎓 Resumen

**El cambio es simple:**
- El template dejó de ser restrictivo
- Los botones ahora siempre aparecen
- El modelo, servicio y backend ya lo soportaban

**Resultado:**
- Puedes tener múltiples cuentas del mismo proveedor
- Todas se sincronizan automáticamente
- Unified Inbox muestra todos los emails combinados

---

**Cambio implementado:** ✅
**Fecha:** 2025-11-12
**Impacto:** Permite workflow profesional real con múltiples cuentas de trabajo/personal

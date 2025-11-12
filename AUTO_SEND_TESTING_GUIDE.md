# 🧪 Guía de Testing: Verificar que Auto-Send Funciona

## ✅ Pre-Requisitos

Antes de testear, verifica que tienes:

```
☐ Gmail conectada en FriendlyMail
☐ IA configurada (/ai-config/)
☐ Auto-send HABILITADO (checkbox marcado)
☐ Cuenta Gmail con acceso a IMAP/INBOX
☐ Terminal abierta en tu proyecto Django
☐ Logs habilitados (logs/app.log debe existir)
```

---

## 🚀 TEST 1: Verificar que Auto-Send Está Habilitado

### Paso 1: Ve a la Configuración de IA

```
1. Abre: http://localhost:8000/ai-config/
2. Deberías ver un formulario
3. Busca el checkbox: "Auto-send responses" o "Auto enviar respuestas"
4. ✅ DEBE estar MARCADO
5. Busca: "IA is active"
6. ✅ DEBE estar MARCADO
7. Haz clic en "Save" o "Guardar"
```

### Paso 2: Verifica en la Base de Datos

```bash
sqlite3 db.sqlite3

# Query: Ver configuración de IA
SELECT id, user_id, auto_send, is_active FROM gmail_app_aicontext;

# Resultado esperado:
# id | user_id | auto_send | is_active
# 1  | 1       | 1         | 1
#            ↑ DEBE SER 1 (True)
#                      ↑ DEBE SER 1 (True)
```

---

## 🧪 TEST 2: Enviar un Email a tu Cuenta y Sincronizar

### Paso 1: Envía un Email a tu Cuenta Gmail

Desde **otra cuenta personal** (amigo, Gmail segunda, etc.):

Envía un email a tu cuenta de FriendlyMail con:
- **To:** tuusuario@gmail.com
- **Subject:** "¿Cuándo es el examen final?" (o algo que IA responda)
- **Body:** "Hola profesor, ¿cuándo es el examen final de tu clase?"

### Paso 2: Sincroniza en FriendlyMail

```
1. Ve a http://localhost:8000/dashboard/
2. Haz clic en "Sync Now" o "Sincronizar"
3. Espera a que termine (deberías ver "Synced X emails")
4. Verifica que el email nuevo aparece en la lista
```

### Paso 3: Verifica que la IA Generó Respuesta

```bash
sqlite3 db.sqlite3

# Query: Ver respuestas generadas
SELECT
    ar.id,
    ar.status,
    ar.response_subject,
    ar.created_at
FROM gmail_app_airesponse ar
ORDER BY ar.created_at DESC
LIMIT 1;

# Resultado esperado:
# id | status           | response_subject         | created_at
# 1  | pending_approval | Re: ¿Cuándo es el exam... | 2025-11-12 14:30:00
#        ↑ IMPORTANTE: DEBE SER pending_approval
```

---

## ⏱️ TEST 3: Esperar a que el Scheduler Auto-Envíe

### Opción A: Esperar a que el Scheduler Se Ejecute (20 min)

El scheduler automático ejecuta cada 20 minutos:

```bash
# Mira los logs en vivo
tail -f logs/app.log | grep -i "auto\|sent"

# Espera hasta ver algo como:
# [15:00] Auto-enviado: Re: ¿Cuándo es el examen final?
# [15:00] Email sent successfully! Message ID: ...
```

### Opción B: Ejecutar el Scheduler Manualmente (Recomendado para Testing)

```bash
# Ejecutar sincronización manualmente para UN usuario
python manage.py auto_sync_emails --user=tuusuario

# Salida esperada:
# Sincronizando 1 cuentas...
#   [tuusuario] 1 emails sincronizados
#     ├─ IA procesó 1 emails
#     ├─ 1 respuestas generadas
#     └─ 1 respuestas AUTO-ENVIADAS  ← ¡ESTO ES LO IMPORTANTE!
# Sincronización completada: 1 exitosas, 0 errores
```

Si ves **"1 respuestas AUTO-ENVIADAS"**, ¡significa que el fix funciona! ✅

---

## 🔍 TEST 4: Verificar que el Email Se Envió

### Paso 1: Verifica en la Base de Datos que Status = 'sent'

```bash
sqlite3 db.sqlite3

# Query: Ver estado de la respuesta
SELECT
    ar.id,
    ar.status,
    ar.sent_at,
    ar.response_subject
FROM gmail_app_airesponse ar
ORDER BY ar.id DESC
LIMIT 1;

# Resultado esperado:
# id | status | sent_at             | response_subject
# 1  | sent   | 2025-11-12 15:00:00 | Re: ¿Cuándo es el exam...
#        ↑ DEBE CAMBIAR DE pending_approval A sent
```

### Paso 2: Verifica en los Logs

```bash
# Buscar en logs
grep -i "auto.*enviado" logs/app.log

# Resultado esperado:
# 2025-11-12 15:00:00 Auto-enviado: Re: ¿Cuándo es el examen? a estudiante@gmail.com
# 2025-11-12 15:00:00 Email sent successfully. Message ID: abc123xyz
```

### Paso 3: Verifica en tu Correo Personal

**Email original:**
```
De: amigo@gmail.com
Asunto: ¿Cuándo es el examen final?
Cuerpo: Hola profesor, ¿cuándo es el examen final?
```

**Respuesta automática que debería recibir en la bandeja:**
```
De: tuusuario@gmail.com (Respondido automáticamente)
Asunto: Re: ¿Cuándo es el examen final?
Cuerpo: [Respuesta generada por IA]

"El examen final será el próximo viernes a las 3:00 PM.
Saludos,
[Tu rol]"
```

Si ves este email en tu bandeja, ¡el fix funciona perfectamente! ✅✅✅

---

## 📊 TEST 5: Verificar el Flujo Completo

### Checklist de Verificación

```
ANTES DE EJECUTAR:
☐ Auto-send habilitado en /ai-config/
☐ IA activa

DURANTE:
☐ Envié email a mi cuenta
☐ Sincronicé en FriendlyMail
☐ IA generó respuesta

DESPUÉS (Opción A - Esperar):
☐ Esperé 20 minutos
☐ Scheduler ejecutó automáticamente
☐ Status cambió a 'sent'

DESPUÉS (Opción B - Manual):
☐ Ejecuté: python manage.py auto_sync_emails --user=tuusuario
☐ Vi "AUTO-ENVIADAS" en salida
☐ Status cambió a 'sent'

RESULTADO FINAL:
☐ Recibí respuesta en mi email personal
☐ El email está firmado con mi rol
☐ El contenido es coherente
☐ La timestamp es reciente
```

---

## 🐛 Debugging: Si Algo No Funciona

### Problema 1: "Status sigue siendo 'approved'" o "pending_approval"

**Causa:** El scheduler no ejecutó, o auto_send no está activo

**Solución:**
```bash
# Verifica que auto_send = 1
sqlite3 db.sqlite3
SELECT auto_send, is_active FROM gmail_app_aicontext WHERE user_id = TU_USER_ID;

# Si no está activo, ve a /ai-config/ y marca los checkboxes
```

### Problema 2: "Error enviando email en los logs"

**Busca en los logs:**
```bash
grep -i "error\|failed" logs/app.log | tail -10
```

**Errores comunes:**
```
❌ "Invalid field 'gmail_id'" → Ya fue corregido con el provider_id fix
❌ "No Gmail account found" → Gmail no está conectada
❌ "Token expired" → Necesitas reconectar Gmail
❌ "Permission denied" → Gmail scopes incorrectos
```

### Problema 3: "El email nunca llega a la bandeja personal"

**Causas posibles:**
```
1. Status es 'sent' pero email no llegó
   → Probablemente fue a spam
   → Chequea tu carpeta de "Spam" o "All Mail"

2. Status no es 'sent'
   → El scheduler no ejecutó
   → Ejecuta manualmente: python manage.py auto_sync_emails --user=tuusuario

3. Email se envió pero a dirección incorrecta
   → Verifica que email.sender está correcto
   → Query: SELECT sender FROM gmail_app_email WHERE id = EMAIL_ID;
```

### Problema 4: "AttributeError: 'Email' object has no attribute 'gmail_id'"

**Causa:** Código viejo que busca `gmail_id`

**Solución:**
```
Este error ya fue corregido con el fix.
Si aparece, significa que hay otro lugar que usa gmail_id.
Busca: grep -r "gmail_id" gmail_app/
```

---

## 📈 Métricas de Éxito

### ✅ El Fix Funciona Si:

```
1. Status Correcto:
   ✅ Respuesta creada con status = 'pending_approval'
   ✅ Cambió a status = 'sent' después del auto-envío

2. Comportamiento:
   ✅ Logs muestran "Auto-enviado: ..."
   ✅ Scheduler envía automáticamente
   ✅ No requiere aprobación manual

3. Usuario Final:
   ✅ Recibe email de respuesta automática
   ✅ Email llega dentro de 20 minutos
   ✅ El contenido es correcto
```

### ❌ El Fix NO Funciona Si:

```
1. Status permanece en 'approved'
   → El scheduler no vio la respuesta
   → Verifica el fix fue aplicado correctamente

2. Status es 'pending_approval' pero nunca cambia a 'sent'
   → El scheduler ejecutó pero failed
   → Revisa los logs para ver el error exacto

3. Email nunca llega
   → Se envió (status = 'sent') pero no llegó
   → Probablemente en spam o error en dirección
```

---

## 🎯 Resumen: Cómo Testear en 10 Minutos

```bash
# 1. Habilitar auto-send (1 min)
Abre http://localhost:8000/ai-config/
Marca "Auto-send" e "IA active"
Guarda

# 2. Enviar email de prueba (1 min)
Desde otra cuenta: Envía a tuusuario@gmail.com
Subject: "¿Cuándo es el examen?"

# 3. Sincronizar (1 min)
http://localhost:8000/sync-all/
O clic en "Sync Now"

# 4. Auto-enviar manualmente (1 min)
python manage.py auto_sync_emails --user=tuusuario

# 5. Verificar resultado (2 min)
sqlite3 db.sqlite3
SELECT status, sent_at FROM gmail_app_airesponse ORDER BY id DESC LIMIT 1;
Debería mostrar status='sent'

# 6. Chequear email personal (3 min)
Abre tu email personal
Busca respuesta automática
Si está ahí, ¡funciona! ✅
```

**Tiempo total: 10-15 minutos**

---

## 📞 Resumen Final

| Aspecto | Antes (Bug) | Después (Fix) |
|---------|-------------|--------------|
| Status al crear | 'approved' | 'pending_approval' |
| Scheduler ve | No encuentra | Encuentra y envía |
| Email llega | ❌ No | ✅ Sí |
| Comando output | "0 auto-enviadas" | "1 respuestas AUTO-ENVIADAS" |
| Time-to-delivery | Nunca | < 20 minutos |

---

Si el fix está instalado y sigues estos pasos, **el auto-send debería funcionar perfectamente**. 🚀


# ⏱️ Configuración de Auto-Send: Intervalo de 20 Minutos

## 📌 La Respuesta Corta

**Sí, el auto-send se ejecuta cada 20 minutos automáticamente.**

---

## 🔍 Dónde Está Configurado

### Ubicación: `friendlymail/settings.py` línea 221

```python
# Auto-sync interval in minutes
AUTO_SYNC_INTERVAL_MINUTES = 20
```

### Cómo Funciona

```
Scheduler (APScheduler) ejecuta cada 20 minutos:
├─ Detecta respuestas pendientes (status='pending_approval')
├─ Si auto_send=True en AIContext
│  └─ Envía automáticamente
│  └─ Cambia status a 'sent'
└─ Repite cada 20 minutos
```

---

## 📊 Flujo Temporal

```
MOMENTO 0:00 (Email llega)
├─ Email sincronizado desde Gmail
├─ IA genera respuesta con status='pending_approval'
└─ Esperando scheduler...

MOMENTO 0:01 - 19:59 (Esperando...)
└─ Respuesta en estado 'pending_approval'
   (Puede haber múltiples respuestas esperando)

MOMENTO 20:00 (Scheduler ejecuta ✅)
├─ Revisa todas las respuestas pendientes
├─ Para cada una con auto_send=True:
│  ├─ Envía email
│  └─ Status → 'sent'
└─ Se duerme 20 minutos más

MOMENTO 20:01 - 39:59 (Esperando...)
└─ Respuesta ya enviada (status='sent')

MOMENTO 40:00 (Scheduler ejecuta de nuevo ✅)
└─ Revisa nuevas respuestas pendientes
   (si hay más)
```

---

## ⚙️ Cómo Se Configura

### Opción 1: Cambiar en settings.py (Recomendado)

**Archivo:** `friendlymail/settings.py` línea 221

```python
# Cambiar de 20 a lo que quieras:

# Cada 5 minutos
AUTO_SYNC_INTERVAL_MINUTES = 5

# Cada 10 minutos
AUTO_SYNC_INTERVAL_MINUTES = 10

# Cada hora
AUTO_SYNC_INTERVAL_MINUTES = 60

# Cada 2 horas
AUTO_SYNC_INTERVAL_MINUTES = 120
```

Después de cambiar, **reinicia Django:**
```bash
python manage.py runserver
```

### Opción 2: Cambiar en variables de entorno

**Archivo:** `.env.local`

```bash
AUTO_SYNC_INTERVAL_MINUTES=10
```

Luego en `settings.py`:
```python
AUTO_SYNC_INTERVAL_MINUTES = int(os.environ.get('AUTO_SYNC_INTERVAL_MINUTES', '20'))
```

### Opción 3: Ejecutar Manualmente (Sin Esperar)

Si necesitas que auto-send se ejecute **AHORA** sin esperar 20 minutos:

```bash
python manage.py auto_sync_emails --user=tuusuario
```

Esto ejecuta el scheduler **inmediatamente** para ese usuario.

---

## 📋 Qué Pasa en Cada Ejecución (Cada 20 min)

```python
# Código en: gmail_app/management/commands/auto_sync_emails.py

Cada 20 minutos:
  Para cada usuario en la BD:
    ├─ GmailService.sync_emails()
    │  └─ Obtiene últimos 20 emails de Gmail
    ├─ IA procesa cada email
    │  ├─ Analiza intent
    │  ├─ Genera respuesta (status='pending_approval')
    │  └─ Si auto_send=True:
    │     ├─ Envía email
    │     ├─ Status → 'sent'
    │     └─ Log: "Auto-enviado: ..."
    │
    └─ OutlookService.sync_emails()
       └─ (Similar para Outlook)
```

---

## ⏰ Ejemplos de Tiempo

### Ejemplo 1: Email llega a las 14:30

```
14:30 → Email recibido
14:31 → Usuario sincroniza manualmente
        ├─ Email importado
        ├─ IA genera respuesta
        └─ Status: pending_approval

14:40 → ESPERANDO...
        (scheduler ejecuta cada 20 min)

15:00 → Scheduler ejecuta ✅
        ├─ Ve respuesta pending
        ├─ auto_send=True
        ├─ Envía email
        └─ Status: sent

15:01 → Usuario recibe respuesta automática ✅
```

**Espera máxima: 20 minutos desde que scheduler ejecuta**

### Ejemplo 2: Varias respuestas esperando

```
14:30 → Email 1 llega → IA genera respuesta A
14:40 → Email 2 llega → IA genera respuesta B
14:50 → Email 3 llega → IA genera respuesta C

15:00 → Scheduler ejecuta
        ├─ Envía respuesta A
        ├─ Envía respuesta B
        ├─ Envía respuesta C
        └─ Todas se envían en batch

15:01 → 3 usuarios reciben respuestas automáticas ✅
```

---

## 🎯 Recomendaciones

### Para Producción

```
AUTO_SYNC_INTERVAL_MINUTES = 5-10

Razón: Mejor experiencia de usuario
(respuesta en máximo 10 minutos)
```

### Para Desarrollo/Testing

```
AUTO_SYNC_INTERVAL_MINUTES = 1

Razón: Testing más rápido
Pero: Carga innecesaria a la API
```

### Balance Recomendado

```
AUTO_SYNC_INTERVAL_MINUTES = 15

Razón:
- Respuesta en <15 minutos
- No sobrecarga la API
- Balance entre UX y eficiencia
```

---

## ⚡ Si Necesitas Envío Inmediato

### Opción 1: Ejecutar Scheduler Manualmente

```bash
python manage.py auto_sync_emails --user=tuusuario
```

**Ventaja:** Se ejecuta ya mismo
**Desventaja:** Requiere terminal abierta

### Opción 2: Crear Endpoint Manual

Agregar a `views.py`:

```python
@login_required
def trigger_auto_send(request):
    """Trigger auto-send immediately without waiting for scheduler"""
    try:
        from gmail_app.ai_service import EmailAIProcessor

        # Procesar respuestas pendientes
        pending = AIResponse.objects.filter(
            status='pending_approval',
            email_intent__email__email_account__user=request.user
        )

        for response in pending:
            if request.user.ai_context.auto_send:
                # Enviar automáticamente
                ...

        messages.success(request, "Auto-send triggered!")
    except Exception as e:
        messages.error(request, str(e))

    return redirect('ai_responses')
```

Luego en template:
```html
<button>Enviar Automáticamente Ahora</button>
```

---

## 📊 Supervisar el Scheduler

### Ver si el Scheduler Está Activo

```bash
# En los logs
tail -f logs/app.log | grep -i "auto\|sync"

# Deberías ver cada 20 minutos:
# [15:00] Sincronizando 1 cuentas...
# [15:00] [tuusuario] X emails sincronizados
# [15:00] X respuestas AUTO-ENVIADAS
```

### Ver Trabajos Programados

```bash
python manage.py shell

from django_apscheduler.models import DjangoJobExecution
DjangoJobExecution.objects.filter(success=True).order_by('-run_time')[-5:]

# Verás los últimos 5 ejecutamientos exitosos
```

---

## 🔧 Cambiar el Intervalo (Paso a Paso)

### Quiero que sea cada 5 minutos

1. Abre: `friendlymail/settings.py`
2. Busca línea 221: `AUTO_SYNC_INTERVAL_MINUTES = 20`
3. Cambia a: `AUTO_SYNC_INTERVAL_MINUTES = 5`
4. Guarda
5. Reinicia Django: `python manage.py runserver`
6. Listo, ahora se ejecuta cada 5 minutos

### Quiero que sea cada hora

1. Abre: `friendlymail/settings.py`
2. Busca línea 221: `AUTO_SYNC_INTERVAL_MINUTES = 20`
3. Cambia a: `AUTO_SYNC_INTERVAL_MINUTES = 60`
4. Guarda
5. Reinicia Django: `python manage.py runserver`
6. Listo, ahora se ejecuta cada hora

---

## ✅ Checklist

- [ ] Entiendo que auto-send ejecuta cada 20 minutos
- [ ] Sé cómo cambiar el intervalo (settings.py:221)
- [ ] Sé cómo ejecutar manualmente (comando auto_sync_emails)
- [ ] Sé cómo verificar que se ejecutó (revisar logs)
- [ ] Conozco el máximo tiempo de espera (<20 minutos)

---

## 📞 Resumen Rápido

| Pregunta | Respuesta |
|----------|-----------|
| **¿Cada cuánto se envía?** | Cada 20 minutos (configurable) |
| **¿Dónde cambiar?** | settings.py línea 221 |
| **¿Cómo ejecutar ya?** | `python manage.py auto_sync_emails --user=tuusuario` |
| **¿Máximo espera?** | ~20 minutos desde que scheduler ejecuta |
| **¿Se ejecuta en segundo plano?** | Sí, automáticamente |
| **¿Se para si cierro Django?** | Sí, el scheduler es parte de Django |

---

Si quieres cambiar el intervalo o necesitas más ayuda, avísame. 🚀


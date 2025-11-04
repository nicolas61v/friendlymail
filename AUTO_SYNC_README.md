# 🔄 Sincronización Automática de Emails

## ✨ ¿Qué es?

FriendlyMail ahora sincroniza automáticamente tus emails de Gmail **cada 20 minutos** (o el intervalo que configures). No necesitas hacer clic en "Sync Now" manualmente.

## 🚀 Características

- ✅ **Sincronización automática** cada 20 minutos
- ✅ **No duplica correos** (protegido por `gmail_id` único)
- ✅ **Procesa con IA automáticamente** si está configurada
- ✅ **Auto-envío de respuestas** (si lo habilitas)
- ✅ **Logs detallados** de cada sincronización
- ✅ **Manejo robusto de errores**
- ✅ **Funciona 24/7** en segundo plano

---

## ⚙️ Configuración

### Cambiar el intervalo de sincronización

Edita el archivo `.env.local` y agrega:

```env
# Sincronizar cada 10 minutos
AUTO_SYNC_INTERVAL_MINUTES=10

# Sincronizar cada 5 minutos (no recomendado, puede exceder cuotas de Gmail API)
AUTO_SYNC_INTERVAL_MINUTES=5

# Sincronizar cada 30 minutos
AUTO_SYNC_INTERVAL_MINUTES=30
```

Luego reinicia el servidor:

```bash
# Si estás en desarrollo
# Detén el servidor (Ctrl+C) y vuelve a iniciarlo
python manage.py runserver

# Si estás en producción (EC2)
sudo supervisorctl restart friendlymail
```

### Activar/Desactivar sincronización automática

En `friendlymail/settings.py`:

```python
# Para desactivar
SCHEDULER_AUTOSTART = False

# Para activar (default)
SCHEDULER_AUTOSTART = True
```

---

## 🔍 Cómo funciona

### 1. Al iniciar Django

Cuando Django arranca, el scheduler se inicia automáticamente (si `SCHEDULER_AUTOSTART = True`).

### 2. Cada X minutos

El scheduler ejecuta el comando `auto_sync_emails` que:

1. Busca todos los usuarios con Gmail conectado
2. Para cada usuario:
   - Descarga emails nuevos de Gmail
   - **No descarga duplicados** (gmail_id es único)
   - Si tiene IA configurada:
     - Procesa cada email con IA
     - Genera respuestas automáticas
     - Si tiene auto-envío activado, aprueba las respuestas

### 3. Logs

Cada sincronización queda registrada:

```
⏰ Iniciando sincronización automática...
  [usuario1] 5 emails sincronizados
    ├─ IA procesó 5 emails
    └─ 3 respuestas generadas
  [usuario2] 0 emails nuevos
✅ Sincronización automática completada
```

---

## 🛠️ Comandos Manuales

### Sincronizar todos los usuarios

```bash
python manage.py auto_sync_emails
```

### Sincronizar solo un usuario

```bash
python manage.py auto_sync_emails --user nombre_usuario
```

### Ver el estado del scheduler

```bash
# Logs en tiempo real
tail -f logs/app.log

# Buscar sincronizaciones
tail -f logs/app.log | grep "sincronización"
```

---

## 🔒 Prevención de Duplicados

### ¿Cómo se previenen?

El campo `gmail_id` en el modelo `Email` tiene la restricción `unique=True`. Esto significa que:

1. Django **automáticamente** previene que se guarde el mismo email dos veces
2. Si intenta sincronizar un email que ya existe, **se ignora silenciosamente**
3. No importa cuántas veces ejecutes la sincronización, **nunca habrá duplicados**

### Verificar

```bash
python manage.py shell

from gmail_app.models import Email
from django.db.models import Count

# Ver si hay duplicados (debería ser 0)
duplicates = Email.objects.values('gmail_id').annotate(
    count=Count('gmail_id')
).filter(count__gt=1)

print(f"Duplicados encontrados: {duplicates.count()}")
```

---

## 📊 Monitoreo

### Ver última sincronización

```bash
# Ver últimas 50 líneas de logs
tail -50 logs/app.log | grep "sincronización"
```

### Ver estadísticas

```bash
python manage.py shell

from gmail_app.models import Email, GmailAccount

# Emails por usuario
for account in GmailAccount.objects.all():
    count = account.emails.count()
    print(f"{account.user.username}: {count} emails")

# Total de emails
print(f"Total: {Email.objects.count()} emails")
```

---

## 🐛 Troubleshooting

### El scheduler no sincroniza

1. Verificar que esté habilitado:
```python
# En settings.py
SCHEDULER_AUTOSTART = True
```

2. Verificar logs:
```bash
tail -f logs/app.log
```

3. Buscar errores:
```bash
tail -f logs/app.log | grep "ERROR"
```

### Token de Gmail expirado

Si ves:

```
[usuario1] Token expirado - Se requiere reconexión
```

El usuario debe:
1. Ir al dashboard
2. Hacer clic en "Connect Gmail"
3. Re-autorizarse

### Cuota de Gmail API excedida

Si ves:

```
Gmail API quota exceeded
```

Opciones:
1. Aumentar intervalo de sincronización a 30 minutos
2. Revisar cuotas en Google Cloud Console
3. Solicitar aumento de cuota (si necesario)

---

## 🎯 Límites de Gmail API

Gmail API tiene límites de uso. Recomendaciones:

| Usuarios | Intervalo Recomendado |
|----------|----------------------|
| 1-5      | 10 minutos          |
| 6-20     | 15 minutos          |
| 21-50    | 20 minutos          |
| 51+      | 30 minutos          |

---

## 📈 Auto-Envío de Respuestas

### Activar auto-envío

1. Ve a **AI Configuration**
2. Expande **Opciones Avanzadas**
3. Activa **Envío Automático**
4. Guarda

⚠️ **ADVERTENCIA**: Con auto-envío activado, la IA enviará emails **sin tu aprobación**. Usa con precaución.

### Recomendaciones

- **NO** activar en producción hasta estar seguro
- Probar primero con auto-envío desactivado
- Revisar respuestas generadas manualmente
- Solo activar cuando confíes 100% en la IA

---

## 🚀 En Producción (EC2)

Ver **DEPLOYMENT.md** para guía completa de deployment en AWS EC2.

Resumen:
1. Configurar Supervisor para mantener proceso vivo
2. Configurar Nginx como proxy inverso
3. El scheduler corre en background automáticamente
4. Logs en `/home/ubuntu/friendlymail/logs/`

---

## 💡 Tips

### Desarrollo Local

Durante desarrollo, puedes:

```bash
# Desactivar scheduler para no gastar cuota de Gmail API
# En settings.py:
SCHEDULER_AUTOSTART = False

# O aumentar intervalo
AUTO_SYNC_INTERVAL_MINUTES = 60  # 1 hora
```

### Producción

En producción:

```bash
# Mantener intervalo razonable
AUTO_SYNC_INTERVAL_MINUTES = 20

# Siempre habilitar scheduler
SCHEDULER_AUTOSTART = True

# Monitorear logs regularmente
tail -f logs/app.log | grep "sincronización"
```

---

## 📞 Soporte

¿Problemas? Reportar en:
- GitHub Issues: https://github.com/nicolas61v/friendlymail/issues
- Siempre incluir logs relevantes

---

## ✅ Checklist de Verificación

Después de instalar, verifica:

- [ ] Scheduler inicia al arrancar Django (ver logs)
- [ ] Primera sincronización se ejecuta correctamente
- [ ] No hay errores en los logs
- [ ] No hay duplicados en la base de datos
- [ ] IA procesa emails (si está configurada)
- [ ] Respuestas se generan correctamente

---

¡Listo! Ahora tus emails se sincronizan automáticamente. 🎉

# Guía Completa: Sistema de Respuestas de IA

## 📋 Introducción

FriendlyMail ahora incluye un sistema completo y mejorado para gestionar respuestas de IA. Esta guía te muestra todas las características y cómo usarlas.

---

## 🎯 Características Principales

### 1. Resumen Superior
Al entrar a **AI Responses**, verás 3 cards estadísticas:
- **Total Emails**: Cantidad total de emails sincronizados
- **Respondidos por IA**: Emails que la IA generó una respuesta
- **Pendientes de Aprobación**: Respuestas esperando tu aprobación

### 2. Tab "Todos los Emails"
Tabla interactiva donde ves **TODOS** los emails con:
- **Email**: Remitente y asunto
- **Decisión IA**:
  - `1` = La IA dice que debería responder
  - `0` = La IA dice que debería escalar/ignorar
- **Confianza**: Porcentaje de confianza de la IA (0-100%)
- **Acción**: Botón para aprobar si hay respuesta pendiente

**Características de la tabla:**
- 🔍 Búsqueda por asunto/remitente
- ↕️ Ordenamiento por cualquier columna
- 📄 Paginación (25 registros por página)
- 📊 Estadísticas de confianza visuales

### 3. Tab "Pendientes"
Respuestas generadas por la IA que esperan tu aprobación:

**Para cada respuesta, puedes:**
1. **Editar** - Cambiar el asunto o cuerpo antes de enviar
2. **Aprobar** - Envía el email automáticamente
3. **Rechazar** - Descarta con feedback

### 4. Edición de Respuestas
Cuando haces clic en **"Editar"**:
1. Ves el email original completo
2. Puedes modificar el asunto
3. Puedes modificar el cuerpo del mensaje
4. Haces clic en "Guardar Cambios"
5. Vuelves a AI Responses con los cambios guardados

---

## 🚀 Cómo Usar

### Flujo Típico

```
1. Entra a Dashboard → AI Responses

2. Mira el RESUMEN SUPERIOR:
   └─ ¿Cuántos emails? ¿Cuántos pendientes?

3. OPCIÓN A: Ver todos los emails
   └─ Click en tab "Todos los Emails"
   └─ Busca, filtra, ordena
   └─ Entiende qué decidió la IA

4. OPCIÓN B: Procesar pendientes
   └─ Click en tab "Pendientes"
   └─ Para cada respuesta:
      ├─ Si le falta algo: Haz click "Editar"
      ├─ Si está bien: Haz click "Aprobar"
      └─ Si no te gusta: Haz click "Rechazar"
```

### Ejemplo Práctico

**Escenario:** Tienes 87 emails, 1 pendiente de aprobación

```
PASO 1: Entra a AI Responses
  └─ Ves en el resumen:
     ├─ Total Emails: 87
     ├─ Respondidos: 1
     └─ Pendientes: 1

PASO 2: Haz click en tab "Pendientes"
  └─ Ves: "Fechas de parcial" con respuesta de la IA

PASO 3: Quieres editar la respuesta
  └─ Haz click en botón "Editar"
  └─ Ahora ves:
     ├─ Email original: "Fechas de parcial"
     ├─ Asunto actual: "Re: Fechas de parcial"
     └─ Cuerpo actual: "Hola Nicolás, Las fechas..."

PASO 4: Modificas algo si lo necesitas
  └─ Cambias el asunto a: "Re: Fechas de los parciales"
  └─ Cambias el cuerpo para agregar más detalles
  └─ Haz click "Guardar Cambios"

PASO 5: De vuelta en AI Responses
  └─ Ves la respuesta con tus cambios
  └─ Haz click "Aprobar"
  └─ El email se envía automáticamente

PASO 6: Listo
  └─ Email enviado
  └─ Lo ves en tab "Enviadas"
```

---

## 📊 Entendiendo la Tabla "Todos los Emails"

### Decisión IA Explicada

| Valor | Significado | Ejemplo |
|-------|-------------|---------|
| `1` | Responder | "Fechas de parcial" → Responder |
| `0` | Escalar | "Asunto desconocido" → Escalar |
| `—` | No procesado | Email sin análisis aún |

### Confianza Explicada

- **90-100%**: La IA está muy segura
- **70-89%**: La IA está bastante segura
- **50-69%**: La IA tiene dudas
- **0-49%**: La IA no está segura

### Ejemplo de Lectura

| Email | Decisión | Confianza | Acción |
|-------|----------|-----------|--------|
| Fechas de parcial | 1 | 85% | Aprobar |
| Alerta de seguridad | 0 | 0% | — |
| Horarios de clase | 1 | 92% | Aprobar |

---

## ⚙️ Configuración del Rol

La IA decide si responder basándose en tu **Rol IA** configurado.

### ¿Cómo cambio lo que la IA responde?

1. Ve a **Dashboard → AI Roles**
2. Click en tu rol (ej: "Maestro")
3. Click en tab **Configuration**
4. En "Topics This Role Can Respond To", agrega los temas:
   ```
   fechas de examenes
   fechas de parcial
   horarios de clase
   ```
5. Click "Save Changes"

### Después de cambiar Topics

La próxima sincronización de emails usará los nuevos topics. Los emails antiguos NO se reprocesarán automáticamente.

Si quieres reprocessar emails viejos:
```bash
python manage.py auto_sync_emails
```

---

## 🔧 Endpoints Técnicos

### Editar Respuesta
```
GET  /response/edit/<response_id>/  → Mostrar formulario
POST /response/edit/<response_id>/  → Guardar cambios
```

### API de Emails
```
GET /api/emails-ai-status/
```

**Response:**
```json
{
  "success": true,
  "emails": [
    {
      "id": 123,
      "subject": "Fechas de parcial",
      "sender": "estudiante@eafit.edu.co",
      "received_date": "2025-11-12T10:30:00Z",
      "has_intent": true,
      "ai_decision": 1,
      "confidence": 85.5,
      "has_response": true,
      "response_status": "pending_approval",
      "intent_type": "schedule_inquiry"
    }
  ]
}
```

---

## ⚠️ Troubleshooting

### Problema: No aparecen emails en "Todos los Emails"

**Solución:**
1. Ve a Dashboard
2. Haz click en "Sincronizar" o "Sync Now"
3. Espera a que termine
4. Vuelve a AI Responses

### Problema: No hay respuestas pendientes

**Posibles causas:**
1. No hay emails que coincidan con los topics configurados
2. La IA decidió escalarlos, no responderlos
3. auto_send está activado y ya los envió automáticamente

**Solución:**
1. Revisa los topics configurados en tu rol
2. Mira el tab "Todos los Emails" para ver las decisiones
3. Si auto_send está ON, mira el tab "Enviadas"

### Problema: Botón "Editar" no funciona

**Solución:**
1. Recarga la página (F5)
2. Si aún no funciona, limpia el cache del navegador
3. Intenta en modo incógnito

### Problema: Modal "Rechazar" no aparece

**Solución:**
- Similar al problema anterior, recarga la página

---

## 💡 Tips y Trucos

### 1. Búsqueda Rápida
En la tabla "Todos los Emails", usa el cuadro de búsqueda:
- Escribe "examen" para ver todos los emails sobre exámenes
- Escribe "profesor@" para ver emails de un profesor específico

### 2. Ordenar por Confianza
Haz click en la columna "Confianza" para ver:
- Los emails que la IA tiene **más segura** (arriba)
- Los emails que la IA tiene **menos segura** (abajo)

### 3. Editar Antes de Aprobar
**Siempre** haz click en "Editar" si:
- La respuesta tiene errores
- Quieres personalizar el mensaje
- Quieres agregar información

### 4. Rechazo con Feedback
Cuando rechazas, déjate un memo de por qué:
- "Información incompleta"
- "Necesita revisión manual"
- "El estudiante merece una respuesta personal"

---

## 📱 Responsive Design

El sistema funciona en:
- ✅ Desktop (escritorio)
- ✅ Tablet
- ✅ Móvil (teléfono)

En móvil:
- Swipe izquierda/derecha para navegar tabs
- Toca el email para ver detalles completos
- Toca "Editar" para abrir el formulario

---

## 🔐 Seguridad

### ¿Mis emails están seguros?

✅ Sí:
- Solo TÚ puedes editar tus respuestas
- Las respuestas se guardan como borradores
- Necesitas hacer click "Aprobar" para enviar
- Toda acción se registra en los logs

### ¿Puede la IA ver información sensible?

✅ Sí, pero está segura:
- La IA solo accede a los emails configurados
- No accede a emails personales
- Solo procesa lo que TÚ sincronizas
- Puedes desactivar IA en cualquier momento

---

## 📈 Métricas y Analytics

### Cómo saber si la IA funciona bien

Mira el **Resumen Superior**:
- Si **Total > Respondidos**: La IA está escalando emails
- Si **Respondidos ≈ Total**: La IA responde casi todo
- Si **Pendientes = 0**: Todo está aprobado/enviado

### Cómo mejorar la precisión

1. Revisa los emails que la IA está escalando
2. Si debería responder, agrega esos temas al rol
3. Si no debería responder, déjalo así
4. Con el tiempo, la IA mejora

---

## ❓ Preguntas Frecuentes

**P: ¿Puedo deshacer un email enviado?**
R: No. Una vez aprobado, se envía inmediatamente. Siempre edita antes de aprobar.

**P: ¿Cuánto tiempo tarda la sincronización?**
R: Depende del total de emails. Normalmente 30 segundos a 2 minutos.

**P: ¿Qué significa "Confianza 0%"?**
R: La IA no está segura del tipo de email. Revísalo manualmente.

**P: ¿Puedo cambiar la Decisión IA?**
R: No directamente, pero puedes editar la respuesta o rechazarla.

**P: ¿Es obligatorio editar?**
R: No. Puedes aprobar directamente si la respuesta te parece bien.

---

## 🚀 Próximas Mejoras Planeadas

- [ ] Historial de cambios en respuestas
- [ ] Templates predefinidos
- [ ] Respuestas condicionales
- [ ] Análisis de sentimiento
- [ ] Calificación de respuestas

---

## 📞 Soporte

Si tienes problemas:

1. Revisa el **Troubleshooting** arriba
2. Recarga la página (F5)
3. Limpia el cache del navegador
4. Intenta en modo incógnito
5. Revisa los logs: Dashboard → Logs

---

## ✅ Checklist para Empezar

- [ ] Sincronizar emails (Dashboard → Sync)
- [ ] Ir a AI Responses
- [ ] Ver el Resumen Superior
- [ ] Explorar tab "Todos los Emails"
- [ ] Ver respuesta pendiente
- [ ] Editar la respuesta (opcional)
- [ ] Aprobar y enviar
- [ ] ¡Listo!

---

## 📝 Resumen

| Feature | Cómo | Dónde |
|---------|------|-------|
| Ver emails | Tabla | Tab "Todos los Emails" |
| Ver respuestas | Cards | Tab "Pendientes" |
| Editar respuesta | Click "Editar" | Tab "Pendientes" |
| Aprobar | Click "Aprobar" | Tab "Pendientes" |
| Rechazar | Click "Rechazar" | Tab "Pendientes" |
| Buscar | Cuadro búsqueda | Tab "Todos los Emails" |
| Cambiar Topics | Dashboard → AI Roles | Configuración |

---

**¡Disfruta del nuevo sistema de respuestas de IA! 🎉**

---

*Última actualización: 12 de Noviembre, 2025*

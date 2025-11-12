# 🎭 Guía Completa: Sistema de Múltiples Roles de IA

## 📌 ¿Qué Es el Sistema de Roles?

Antes tenías **1 rol por usuario**. Ahora puedes tener **infinitos roles** cada uno con su propia configuración independiente:

```
ANTES:
Usuario Vasquez
  └─ AIContext (1 rol)
      ├─ Rol: "Profesor"
      ├─ Topics: exámenes, horarios
      └─ Auto-send: ON

AHORA:
Usuario Vasquez
  ├─ AIRole: "Profesor" ✅ ACTIVO
  │   ├─ Topics: exámenes, horarios
  │   ├─ Auto-send: ON
  │   ├─ Temporal Rules: Exam Info (Nov 1-15)
  │   └─ Allowed Domains: @eafit.edu.co
  │
  ├─ AIRole: "Coordinador" (inactivo)
  │   ├─ Topics: trámites administrativos
  │   ├─ Auto-send: OFF (requiere aprobación)
  │   └─ Allowed Domains: cualquiera
  │
  └─ AIRole: "Director" (inactivo)
      ├─ Topics: decisiones estratégicas
      ├─ Auto-send: OFF
      └─ Allowed Domains: @eafit.edu.co
```

---

## 🚀 Casos de Uso Reales

### Caso 1: Profesor Multi-Rol

**Rol "Profesor de Algoritmos"** (Active)
- Responde automáticamente: exámenes, tareas, horarios
- Temporal Rules: "Exam Info" (Nov 1-15), "Project Deadline" (Oct 15-25)
- Auto-send: ON
- Allowed: @eafit.edu.co

**Rol "Coordinador de Departamento"** (Inactive)
- Responde: solicitudes administrativas, reuniones
- Auto-send: OFF (revisión manual requerida)
- Allowed: todas las direcciones

**Rol "Director"** (Inactive)
- Responde: decisiones de grado, apelaciones
- Auto-send: OFF (siempre requiere aprobación)
- High priority, nunca automático

### Caso 2: Profesional Múltiples Empresas

**Rol "Empresa A"**
- Empresa A support responses
- Auto-send: ON
- Temporal rules por proyecto

**Rol "Empresa B"**
- Empresa B support responses
- Auto-send: OFF
- Temporal rules por temporada

**Rol "Personal"**
- Respuestas personales
- Auto-send: OFF
- Solo amigos cercanos

---

## 🎯 Características del Sistema

### 1. **Solo UN Rol Activo por Usuario**

```
┌─────────────────────────────────────┐
│ Usuario puede tener 10 roles        │
│ Pero SOLO 1 activo a la vez         │
│                                      │
│ Al activar Rol B:                   │
│  • Rol A se desactiva automáticamente│
│  • Nuevo emails usan configuración B │
│                                      │
│ Cambiar rol = Cambiar comportamiento│
│   del IA instantáneamente            │
└─────────────────────────────────────┘
```

### 2. **Configuración Independiente por Rol**

Cada rol tiene:
- ✏️ **Nombre único** (no se puede cambiar después)
- 📝 **Descripción del contexto** (para la IA)
- 🎚️ **Nivel de complejidad** (simple/medium/advanced)
- ✅ **Topics que puede responder** (uno por línea)
- ❌ **Topics para escalar** (uno por línea)
- 📧 **Dominios permitidos** (opcional, para filtrar)
- 📤 **Auto-send** (cada rol decide independientemente)

### 3. **Reglas de Tiempo (Temporal Rules)**

Cada rol puede tener múltiples reglas:

```
ROL "Profesor"
  ├─ Exam Info (Oct 15 - Nov 15)
  │   └─ Keywords: "exam", "examen", "test"
  │   └─ Template: "El examen será..."
  │
  ├─ Project Deadline (Sept 1 - Oct 30)
  │   └─ Keywords: "project", "proyecto"
  │   └─ Template: "El proyecto está debido..."
  │
  └─ Finals Period (Nov 1 - Dec 31)
      └─ Keywords: "final", "prep", "study"
```

### 4. **Flujo de Procesamiento**

```
Email llega a Inbox
  ↓
¿Hay un rol ACTIVO?
  ├─ SÍ → Usar configuración del rol activo
  │   ├─ Aplicar dominios permitidos
  │   ├─ Analizar intent con IA
  │   ├─ Buscar temporal rules del rol
  │   └─ Generar respuesta
  │
  └─ NO → Escalar (no hacer nada)

Respuesta generada
  ↓
¿Auto-send está ON en el rol?
  ├─ SÍ → Enviar automáticamente
  └─ NO → Esperar aprobación del usuario
```

---

## 💻 Cómo Usar: Paso a Paso

### Paso 1: Ver tus Roles

```
Menú → AI Roles
```

Verás una página con:
- Tarjetas de cada rol
- Badge mostrando cuál está ACTIVO
- Botones de acciones rápidas

### Paso 2: Crear un Nuevo Rol

```
[Create New Role]
```

Formulario:
1. **Nombre del rol** (ej: "Profesor")
2. **Descripción** (ej: "Profesor de Algoritmos en EAFIT")
3. **Complejidad** (simple/medium/advanced)
4. **Topics que puedo responder** (uno por línea)
5. **Topics para escalar** (uno por línea)
6. **Dominios** (opcional, ej: @eafit.edu.co)
7. **Auto-send** (checkbox)

### Paso 3: Activar un Rol

```
En la lista de roles → [Activate]
```

O ir al rol y ver que dice "✓ ACTIVE"

### Paso 4: Configurar el Rol

```
Rol seleccionado → [Configure]
```

Dos tabs:
- **Configuration:** Editar temas, dominios, auto-send
- **Temporal Rules:** Crear reglas de tiempo

### Paso 5: Agregar Reglas de Tiempo

```
Rol → Temporal Rules tab → [Add Temporal Rule]
```

Campos:
- 📌 **Nombre:** Descripción de la regla (ej: "Exam Info")
- 🔑 **Keywords:** Palabras que activan la regla (comma-separated)
- 📅 **Fechas:** Inicio y fin de la regla
- 📝 **Template:** Respuesta para emails que coincidan
- ⚙️ **Prioridad:** Número (mayor = más importante)
- 📊 **Status:** Draft/Active/Scheduled

---

## 🔄 Cambiar de Rol

### Cambio Rápido

```
AI Roles → Rol inactivo → [Activate]

✅ Rol cambió instantáneamente
✅ Nuevos emails usan esta configuración
✅ El resto de los emails del rol anterior no se afectan
```

### Antes de Cambiar

Considera:
- ¿Tengo respuestas pendientes en el rol anterior?
- ¿Quiero que las nuevas respuestas usen este rol?
- ¿He configurado bien este rol?

---

## 🏗️ Arquitectura Técnica

### Modelo de Datos

```python
AIRole
  ├─ user (ForeignKey)  # Permite múltiples roles por usuario
  ├─ name (CharField)   # Único por usuario (profesor, coordinador)
  ├─ context_description
  ├─ is_active (Boolean) # Solo 1 true por usuario
  ├─ complexity_level
  ├─ can_respond_topics
  ├─ cannot_respond_topics
  ├─ allowed_domains
  ├─ auto_send (Boolean) # Cada rol decide
  ├─ created_at
  └─ updated_at

TemporalRule
  ├─ ai_role (ForeignKey) # Pertenece a específico rol
  ├─ ai_context (ForeignKey) # Legacy support
  ├─ name
  ├─ keywords
  ├─ start_date / end_date
  ├─ response_template
  ├─ status
  └─ priority
```

### Lógica de Procesamiento

```python
# En ai_service.py
def process_email(email):
    user = email.email_account.user

    # Obtener rol ACTIVO (o AIContext legacy)
    ai_context = AIRole.get_active_role(user)

    if not ai_context:
        return escalate()  # No configurado

    # Usar configuración del rol activo
    analyze_intent(email, ai_context)
    find_matching_rules(email, ai_context)
    generate_response(email, ai_context)
```

### Auto-send en Cada Rol

```python
# En auto_sync_emails.py
for email in synced_emails:
    intent, response = ai_processor.process_email(email)

    # Usar auto_send del ROL ACTUAL
    if ai_context.auto_send and response.status == 'pending_approval':
        send_email(response)
        response.status = 'sent'
```

---

## 🔐 Validaciones & Seguridad

### Validaciones de Roles

```
✅ Nombre único por usuario
   No puedes tener 2 "Profesor" en la misma cuenta

✅ Al menos 1 rol debe existir
   No puedes eliminar tu único rol
   Se pide crear otro antes de borrar el actual

✅ Solo 1 rol activo
   Al activar uno, los otros se desactivan automáticamente

✅ Control de acceso
   Solo el dueño del usuario puede editar sus roles
```

### Reglas de Tiempo

```
✅ Keywords son requeridos
✅ Fechas deben ser válidas (start < end)
✅ Status debe ser uno de: draft, active, scheduled, expired, disabled
✅ Prioridad entre 1-100
```

---

## 📊 Ejemplos Avanzados

### Ejemplo 1: Profesor Semestral

```
SEMESTRE 1 (Feb - Jun):
Rol "Profesor Alg 1"
  ├─ Topics: algoritmos básicos, loops, arrays
  ├─ Reglas: Exam (Apr), Proyecto (May)
  └─ Auto-send: ON

SEMESTRE 2 (Aug - Dec):
Rol "Profesor Alg 2"  ← Activate esto
  ├─ Topics: estructuras avanzadas, recursión
  ├─ Reglas: Exam (Oct), Proyecto (Nov)
  └─ Auto-send: ON
```

### Ejemplo 2: Múltiples Clientes

```
Cliente A Support
  ├─ Allowed Domains: @clientea.com
  ├─ Topics: tickets, issues, updates
  └─ Auto-send: ON

Cliente B Support  ← Activate cuando trabajes con B
  ├─ Allowed Domains: @clienteb.com
  ├─ Topics: tickets, issues, updates
  └─ Auto-send: OFF (requiere revisión)
```

### Ejemplo 3: Escalado Progresivo

```
Rol "Junior Assistant"
  ├─ Topics: preguntas simples
  ├─ Auto-send: ON
  └─ Escalate: asuntos complejos

Rol "Senior Coordinator"
  ├─ Topics: preguntas complejas
  ├─ Auto-send: OFF
  └─ Escalate: decisiones gerenciales

Rol "Director"
  ├─ Topics: decisiones finales
  ├─ Auto-send: OFF (siempre)
  └─ Escalate: nada (todo se revisa)
```

---

## 🐛 Troubleshooting

### P: Cambié de rol pero los emails siguen siendo respondidos de la forma antigua

**R:** El cambio de rol solo afecta a NUEVOS emails. Los pendientes en el rol anterior todavía usan esa configuración. Espera a que se procesen o aprueba/rechaza manualmente.

### P: Creé una regla temporal pero no se dispara

**R:** Chequea:
1. ¿Status está "active"? (no "draft")
2. ¿Está el rol ACTIVO?
3. ¿Las fechas son correctas? (hoy dentro del rango)
4. ¿Los keywords coinciden exactamente?

### P: ¿Puedo tener reglas iguales en dos roles?

**R:** Sí, cada rol tiene sus propias reglas. Si activas el Rol A, solo se usan reglas del Rol A.

### P: ¿Qué pasa si borro un rol?

**R:**
- Se elimina la configuración
- Se elimina temporales rules de ese rol
- Los emails YA procesados se mantienen
- PERO: No puedes borrar si es el único rol

---

## 📈 Mejores Prácticas

### 1. **Organiza tus Roles**

```
✅ BIEN:
  - Profesor (cursos que dictas)
  - Coordinador (tareas administrativas)
  - Personal (correos personales)

❌ MALO:
  - Rol1, Rol2, Rol3...
  - "Test", "test2", "TESTFINAL"
```

### 2. **Usa Nombres Claros**

```
✅ "Profesor Algoritmos 1" (sabes exactamente qué es)
❌ "prof" (demasiado vago)
```

### 3. **Documento Roles para el Equipo**

```
Si trabajas con otros:

ROLES DISPONIBLES:
1. Profesor - Auto-send, responde a estudiantes
2. Coordinador - Aprobación manual, asuntos admin
3. Director - Muy restrictivo, escala todo
```

### 4. **Test antes de Activar**

```
Nuevo rol:
1. Crea el rol
2. Configura topics
3. Agrega 1-2 temporal rules
4. Cambia a "draft" status
5. Test con emails de prueba
6. Cuando funciona → Activar
```

---

## 🎓 Flujo Típico de Un Día

```
08:00 AM
  └─ Activo "Profesor" role
  └─ Enseño clases, responde preguntas de estudiantes automáticamente
  └─ Auto-send: ON

14:00 PM
  └─ Cambio a "Coordinador" role
  └─ Manejo asuntos administrativos
  └─ Auto-send: OFF (reviso todo)

18:00 PM
  └─ Cambio a "Personal" role
  └─ Responde amigos y familia
  └─ Auto-send: ON (solo gente de confianza)
```

---

## ✅ Checklist: Configurar Múltiples Roles

```
☐ Accedo a AI Roles management
☐ Veo el rol activo actual
☐ Creo 1er rol adicional con [Create New Role]
☐ Configuro nombre único y descripción
☐ Defino topics que puedo responder
☐ Defino topics para escalar
☐ Activo auto-send si deseo
☐ Hago [Save Configuration]
☐ Creo una temporal rule como prueba
☐ Cambio a este nuevo rol con [Activate]
☐ Compruebo que los nuevos emails usan esta configuración
☐ Créo otro rol más para completar setup
```

---

## 📞 Resumen Rápido

| Aspecto | Antes (AIContext) | Ahora (AIRole) |
|---------|------------------|---|
| **Roles por usuario** | 1 | Infinitos |
| **Configuración** | 1 para todo | Independiente por rol |
| **Activación** | Siempre activo | Switch entre roles |
| **Temporal Rules** | 1 conjunto | Por cada rol |
| **Auto-send** | 1 setting global | Por rol |
| **Cambiar behavior** | Editar UIContext | Activar otro rol |

---

## 🎯 Próximos Pasos

1. ✅ Crea tus roles principales
2. ✅ Configura 1-2 temporal rules por rol
3. ✅ Prueba activ/deactiv roles
4. ✅ Observa cómo IA responde diferente
5. ✅ Ajusta según necesites

**El sistema está listo para producción.**

¡Disfruta de tus múltiples roles! 🎭

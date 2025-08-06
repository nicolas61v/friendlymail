# 📧 Smart Email Assistant

> Automatiza respuestas inteligentes a correos repetitivos usando IA y contexto personalizado

## 🎯 ¿Qué hace?

Conecta tu correo, define un contexto (ej: info de tu clase), establece fecha límite, y la IA responde automáticamente emails rutinarios basándose en tu información.

**Perfecto para**: Docentes con preguntas repetitivas de estudiantes, soporte técnico, consultas frecuentes.

## ✨ Características

- 🔗 Integración con Gmail/Outlook
- 🤖 Respuestas inteligentes con LLM
- 📅 Control con fechas límite
- 🎯 Filtrado automático importante vs. rutinario
- 📊 Dashboard de actividad

## 🛠️ Stack Tecnológico

- **Backend**: Django/Flask (Python) + Supabase
- **Frontend**: React + Tailwind CSS
- **LLM**: OpenAI GPT / Anthropic Claude
- **Deploy**: Railway / AWS

## 🚀 Instalación Rápida

```bash
# Backend
git clone https://github.com/tu-usuario/smart-email-assistant.git
cd smart-email-assistant
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Configurar credenciales
python manage.py migrate && python manage.py runserver

# Frontend
cd frontend
npm install && npm start
```

## ⚙️ Configuración

```env
# .env file
SUPABASE_URL=tu_supabase_url
SUPABASE_KEY=tu_supabase_key
OPENAI_API_KEY=tu_openai_key
GOOGLE_CLIENT_ID=tu_google_client_id
GOOGLE_CLIENT_SECRET=tu_google_secret
```

## 📖 Uso

1. **Conecta tu email** (OAuth2 seguro)
2. **Define contexto**:
   ```
   Soy docente de Programación Web
   Horarios: Lunes/Miércoles 2-4 PM
   Puede responder sobre: fechas de entrega, software, conceptos de clase
   NO responder: notas, temas médicos, quejas
   ```
3. **Configura reglas** (fecha límite, filtros)
4. **Monitorea actividad** en el dashboard

## 🔧 Plan de Desarrollo

- **Fase 1 (4 sem)**: MVP - Auth, Gmail, LLM básico
- **Fase 2 (3 sem)**: Contexto, filtros, dashboard
- **Fase 3 (3 sem)**: Múltiples providers, colas, tests
- **Fase 4 (2 sem)**: Deploy, monitoring, docs

## 🤝 Contribuir

1. Fork → Feature branch → Pull Request
2. Tests: `python -m pytest` / `npm test`

## 📞 Contacto

- 🐛 Issues: [GitHub Issues](https://github.com/tu-usuario/smart-email-assistant/issues)
- 👥 Equipo: [@nicolas61v](https://github.com/nicolas61v)

---
⭐ **¿Te gusta? ¡Dale una estrella!** ⭐

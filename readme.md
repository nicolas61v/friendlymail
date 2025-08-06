# 📧 Smart Email Assistant

> Automate intelligent responses to repetitive emails using AI and personalized context

## 🎯 What does it do?

Connect your email, define a context (e.g., class info), set a deadline, and the AI automatically responds to routine emails based on your information.

**Perfect for**: Teachers with repetitive student questions, tech support, frequent inquiries.

## ✨ Features

- 🔗 Gmail/Outlook integration
- 🤖 Intelligent responses with LLM
- 📅 Time control with deadlines
- 🎯 Automatic filtering important vs. routine
- 📊 Activity dashboard

## 🛠️ Tech Stack

- **Backend**: Django/Flask (Python) + Supabase
- **Frontend**: React + Tailwind CSS
- **LLM**: OpenAI GPT / Anthropic Claude
- **Deploy**: Railway / AWS

## 🚀 Quick Installation

```bash
# Backend
git clone https://github.com/your-username/smart-email-assistant.git
cd smart-email-assistant
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Configure credentials
python manage.py migrate && python manage.py runserver

# Frontend
cd frontend
npm install && npm start
```

## ⚙️ Configuration

```env
# .env file
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
OPENAI_API_KEY=your_openai_key
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_secret
```

## 📖 Usage

1. **Connect your email** (secure OAuth2)
2. **Define context**:
   ```
   I'm a Web Programming teacher
   Schedule: Monday/Wednesday 2-4 PM
   Can answer about: deadlines, software, class concepts
   DON'T answer: grades, medical topics, complaints
   ```
3. **Configure rules** (deadline, filters)
4. **Monitor activity** on the dashboard

## 🔧 Development Plan

- **Phase 1 (4 weeks)**: MVP - Auth, Gmail, basic LLM
- **Phase 2 (3 weeks)**: Context, filters, dashboard
- **Phase 3 (3 weeks)**: Multiple providers, queues, tests
- **Phase 4 (2 weeks)**: Deploy, monitoring, docs

## 🤝 Contributing

1. Fork → Feature branch → Pull Request
2. Tests: `python -m pytest` / `npm test`

## 📞 Contact

- 🐛 Issues: [GitHub Issues](https://github.com/your-username/smart-email-assistant/issues)
- 👥 Team: [@nicolas61v](https://github.com/nicolas61v)

---
⭐ **Like it? Give it a star!** ⭐

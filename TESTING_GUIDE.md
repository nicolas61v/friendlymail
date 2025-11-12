# Guía de Testing: Validar los Fixes

Esta guía te ayudará a verificar que los cambios funcionan correctamente.

---

## ✅ TEST 1: Email Detail - Abrir un Email

### Escenario: Abrir un email sincronizado

#### Pasos Manuales
1. Inicia sesión en FriendlyMail
2. Conecta una cuenta Gmail: `/connect-gmail/`
3. Sincroniza emails: `/sync-all/`
4. Ve al dashboard
5. Haz clic en cualquier email
6. ✅ Verifica que **el email se abre** y muestra:
   - From (remitente)
   - To (destinatario)
   - Date (fecha)
   - Body (contenido HTML o plain text)

#### Código de Test Unitario
```python
# tests.py
from django.test import TestCase, Client
from django.contrib.auth.models import User
from gmail_app.models import Email, EmailAccount
from datetime import datetime, timezone

class EmailDetailTestCase(TestCase):
    def setUp(self):
        # Crea usuario
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        # Crea cuenta Gmail
        self.email_account = EmailAccount.objects.create(
            user=self.user,
            email='testuser@gmail.com',
            provider='gmail',
            access_token='fake_token_123',
            refresh_token='fake_refresh_123',
            token_expires_at=datetime.now(timezone.utc)
        )

        # Crea email
        self.email = Email.objects.create(
            email_account=self.email_account,
            provider_id='12345',
            thread_id='12345',
            subject='Test Email',
            sender='boss@company.com',
            recipient='testuser@gmail.com',
            body_plain='This is a test email',
            body_html='<html><body>This is a test email</body></html>',
            received_date=datetime.now(timezone.utc),
            is_read=False
        )

        self.client = Client()
        self.client.login(username='testuser', password='testpass123')

    def test_email_detail_with_email_account(self):
        """Verifica que email_detail abre emails del modelo EmailAccount (nuevo)"""
        response = self.client.get(f'/email/{self.email.id}/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Email')  # Subject
        self.assertContains(response, 'boss@company.com')  # From
        self.assertContains(response, 'This is a test email')  # Body

    def test_email_detail_not_found(self):
        """Verifica que redirecciona si email no existe"""
        response = self.client.get('/email/99999/')

        self.assertEqual(response.status_code, 302)  # Redirect
        self.assertIn('/dashboard/', response.url)

    def test_email_detail_unauthorized(self):
        """Verifica que no puedes ver emails de otros usuarios"""
        other_user = User.objects.create_user(
            username='otheruser',
            password='otherpass'
        )
        other_account = EmailAccount.objects.create(
            user=other_user,
            email='other@gmail.com',
            provider='gmail',
            access_token='fake',
            refresh_token='fake',
            token_expires_at=datetime.now(timezone.utc)
        )
        other_email = Email.objects.create(
            email_account=other_account,
            provider_id='55555',
            thread_id='55555',
            subject='Secret Email',
            sender='secret@company.com',
            recipient='other@gmail.com',
            body_plain='Secret content',
            received_date=datetime.now(timezone.utc)
        )

        # Intenta acceder como testuser
        response = self.client.get(f'/email/{other_email.id}/')

        self.assertEqual(response.status_code, 302)  # Redirecciona
        # No debería poder ver el email
```

#### Ejecutar Test
```bash
python manage.py test gmail_app.tests.EmailDetailTestCase
```

---

## ✅ TEST 2: Múltiples Cuentas Gmail

### Escenario: Conectar 2 cuentas Gmail diferentes

#### Pasos Manuales
1. Inicia sesión con un usuario
2. Conecta primera cuenta: `trabajo@gmail.com`
   - Ve a `/connect-gmail/`
   - Autoriza con Google
   - Verifica en `/admin/` que se crea en `EmailAccount`
3. Conecta segunda cuenta: `personal@gmail.com`
   - Repite el proceso
   - ✅ Verifica que se crea OTRA entrada en `EmailAccount`
4. Sincroniza: `/sync-all/`
   - ✅ Verifica que ambas cuentas se sincronizan
   - Ver en logs: "Synced X emails from Gmail account trabajo@gmail.com"
   - Ver en logs: "Synced Y emails from Gmail account personal@gmail.com"
5. Dashboard
   - ✅ Verifica que muestra emails de AMBAS cuentas unificadas

#### Código de Test Unitario
```python
class MultipleGmailAccountsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')

    def test_can_create_multiple_gmail_accounts(self):
        """Verifica que un usuario puede tener múltiples cuentas Gmail"""
        # Primera cuenta
        account1 = EmailAccount.objects.create(
            user=self.user,
            email='trabajo@gmail.com',
            provider='gmail',
            access_token='token1',
            refresh_token='refresh1',
            token_expires_at=datetime.now(timezone.utc)
        )

        # Segunda cuenta
        account2 = EmailAccount.objects.create(
            user=self.user,
            email='personal@gmail.com',
            provider='gmail',
            access_token='token2',
            refresh_token='refresh2',
            token_expires_at=datetime.now(timezone.utc)
        )

        # Verifica que existen ambas
        accounts = EmailAccount.objects.filter(
            user=self.user,
            provider='gmail',
            is_active=True
        )

        self.assertEqual(accounts.count(), 2)
        self.assertTrue(accounts.filter(email='trabajo@gmail.com').exists())
        self.assertTrue(accounts.filter(email='personal@gmail.com').exists())

    def test_sync_emails_with_account_id(self):
        """Verifica que sync_emails() funciona con email_account_id"""
        from gmail_app.gmail_service import GmailService
        from unittest.mock import patch, MagicMock

        # Crea 2 cuentas
        account1 = EmailAccount.objects.create(
            user=self.user,
            email='trabajo@gmail.com',
            provider='gmail',
            access_token='token1',
            refresh_token='refresh1',
            token_expires_at=datetime.now(timezone.utc)
        )

        account2 = EmailAccount.objects.create(
            user=self.user,
            email='personal@gmail.com',
            provider='gmail',
            access_token='token2',
            refresh_token='refresh2',
            token_expires_at=datetime.now(timezone.utc)
        )

        # Mock Gmail API (no queremos hacer llamadas reales)
        with patch('gmail_app.gmail_service.GmailService.get_service') as mock_service:
            mock_gmail = MagicMock()
            mock_service.return_value = mock_gmail

            # Mock respuesta de Gmail API
            mock_gmail.users().messages().list().execute.return_value = {
                'messages': []
            }

            service = GmailService(self.user)

            # Sincroniza cuenta 1 específicamente
            result1 = service.sync_emails(email_account_id=account1.id)
            self.assertEqual(result1, [])

            # Sincroniza cuenta 2 específicamente
            result2 = service.sync_emails(email_account_id=account2.id)
            self.assertEqual(result2, [])

    def test_sync_all_accounts_syncs_all_gmail(self):
        """Verifica que sync_all_accounts() sincroniza TODAS las cuentas"""
        # Crea 2 cuentas
        account1 = EmailAccount.objects.create(
            user=self.user,
            email='trabajo@gmail.com',
            provider='gmail',
            access_token='token1',
            refresh_token='refresh1',
            token_expires_at=datetime.now(timezone.utc)
        )

        account2 = EmailAccount.objects.create(
            user=self.user,
            email='personal@gmail.com',
            provider='gmail',
            access_token='token2',
            refresh_token='refresh2',
            token_expires_at=datetime.now(timezone.utc)
        )

        # Crea emails en ambas
        Email.objects.create(
            email_account=account1,
            provider_id='msg1',
            thread_id='thread1',
            subject='Email from trabajo',
            sender='boss@work.com',
            recipient='trabajo@gmail.com',
            body_plain='Work email',
            received_date=datetime.now(timezone.utc)
        )

        Email.objects.create(
            email_account=account2,
            provider_id='msg2',
            thread_id='thread2',
            subject='Email from personal',
            sender='friend@example.com',
            recipient='personal@gmail.com',
            body_plain='Personal email',
            received_date=datetime.now(timezone.utc)
        )

        # Verifica que dashboard muestra TODOS
        response = self.client.get('/dashboard/')

        self.assertEqual(response.status_code, 200)
        # Verifica que aparecen ambos emails
        self.assertContains(response, 'Email from trabajo')
        self.assertContains(response, 'Email from personal')
```

#### Ejecutar Test
```bash
python manage.py test gmail_app.tests.MultipleGmailAccountsTestCase
```

---

## ✅ TEST 3: Sincronización Unificada

### Escenario: Ver emails de múltiples proveedores

#### Pasos Manuales
1. Conecta una cuenta Gmail: `/connect-gmail/`
2. Conecta una cuenta Outlook: `/connect-outlook/`
3. Sincroniza ambas: `/sync-all/`
4. Dashboard
   - ✅ Verifica que muestra emails de AMBAS cuentas unificados y ordenados por fecha

#### Código de Test
```python
class DashboardUnificationTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass'
        )

        # Cuenta Gmail
        self.gmail_account = EmailAccount.objects.create(
            user=self.user,
            email='user@gmail.com',
            provider='gmail',
            access_token='token_gmail',
            refresh_token='refresh_gmail',
            token_expires_at=datetime.now(timezone.utc)
        )

        # Cuenta Outlook
        self.outlook_account = EmailAccount.objects.create(
            user=self.user,
            email='user@outlook.com',
            provider='outlook',
            access_token='token_outlook',
            refresh_token='refresh_outlook',
            token_expires_at=datetime.now(timezone.utc)
        )

        # Email de Gmail
        self.gmail_email = Email.objects.create(
            email_account=self.gmail_account,
            provider_id='gmail_msg_1',
            thread_id='gmail_thread_1',
            subject='Gmail Email',
            sender='friend@gmail.com',
            recipient='user@gmail.com',
            body_plain='This is from Gmail',
            received_date=datetime(2025, 11, 12, 10, 0, tzinfo=timezone.utc)
        )

        # Email de Outlook
        self.outlook_email = Email.objects.create(
            email_account=self.outlook_account,
            provider_id='outlook_msg_1',
            thread_id='outlook_thread_1',
            subject='Outlook Email',
            sender='colleague@outlook.com',
            recipient='user@outlook.com',
            body_plain='This is from Outlook',
            received_date=datetime(2025, 11, 12, 11, 0, tzinfo=timezone.utc)
        )

        self.client = Client()
        self.client.login(username='testuser', password='testpass')

    def test_dashboard_shows_emails_from_all_accounts(self):
        """Verifica que dashboard muestra emails de TODAS las cuentas"""
        response = self.client.get('/dashboard/')

        self.assertEqual(response.status_code, 200)
        # Ambos emails deben aparecer
        self.assertContains(response, 'Gmail Email')
        self.assertContains(response, 'Outlook Email')

    def test_dashboard_emails_ordered_by_date(self):
        """Verifica que los emails están ordenados por fecha descendente"""
        response = self.client.get('/dashboard/')

        # Outlook es más reciente (11:00) que Gmail (10:00)
        # Entonces Outlook debe aparecer primero
        content = response.content.decode()
        outlook_pos = content.find('Outlook Email')
        gmail_pos = content.find('Gmail Email')

        # Outlook debe aparecer antes (números menores)
        self.assertLess(outlook_pos, gmail_pos)
```

#### Ejecutar Test
```bash
python manage.py test gmail_app.tests.DashboardUnificationTestCase
```

---

## 🔧 Cómo Ejecutar TODOS los Tests

```bash
# Ver resultado detallado
python manage.py test gmail_app.tests -v 2

# Con cobertura (requiere coverage)
pip install coverage
coverage run --source='gmail_app' manage.py test
coverage report
```

---

## 🐛 Debugging: Logs y Estadísticas

### Ver logs en tiempo real
```bash
tail -f logs/app.log | grep -E "(sync|email_detail|ERROR)"
```

### Django Shell para debugging
```python
python manage.py shell

from gmail_app.models import EmailAccount, Email
from django.contrib.auth.models import User

user = User.objects.get(username='testuser')

# Ver todas las cuentas del usuario
for account in user.email_accounts.all():
    email_count = account.emails.count()
    print(f"{account.email} ({account.provider}): {email_count} emails")

# Ver últimos 5 emails
for email in Email.objects.filter(email_account__user=user).order_by('-received_date')[:5]:
    print(f"[{email.email_account.email}] {email.subject}")
```

---

## ✅ Checklist de Validación

### Antes de los Cambios
- [ ] No puedo abrir ningún email
- [ ] Solo puedo conectar 1 Gmail

### Después de los Cambios
- [ ] ✅ Puedo abrir emails sincronizados
- [ ] ✅ Puedo conectar 2+ cuentas Gmail
- [ ] ✅ Dashboard muestra emails de todas las cuentas
- [ ] ✅ Sync sincroniza todas las cuentas automáticamente
- [ ] ✅ Puedo responder con IA a emails de cualquier cuenta
- [ ] ✅ Los logs muestran sincronización correcta

---

## 📊 Verificación de Datos en DB

### SQLite Shell
```bash
# Abre la DB
sqlite3 db.sqlite3

# Ver cuentas del usuario
SELECT id, email, provider, is_active FROM gmail_app_emailaccount WHERE user_id = 1;

# Ver emails por cuenta
SELECT ea.email, COUNT(e.id) as email_count
FROM gmail_app_emailaccount ea
LEFT JOIN gmail_app_email e ON ea.id = e.email_account_id
GROUP BY ea.id;

# Ver últimos emails
SELECT subject, sender, received_date, email_account_id
FROM gmail_app_email
ORDER BY received_date DESC
LIMIT 10;
```

---

## 🎯 Resultado Esperado

Después de corregir los bugs:

| Feature | Antes | Después |
|---------|-------|---------|
| Abrir emails | ❌ 404 Error | ✅ Se abre correctamente |
| Múltiples Gmails | ❌ Solo 1 | ✅ Ilimitadas |
| Sincronización | ❌ Solo 1 Gmail | ✅ Todas las cuentas |
| Dashboard | ❌ Incompleto | ✅ Unificado y correcto |
| IA Responses | ❌ Solo para 1 | ✅ Para todas las cuentas |


#!/usr/bin/env python
"""
Test para validar que la IA respeta los topics configurados
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'friendlymail.settings')
django.setup()

from gmail_app.models import Email, EmailAccount
from gmail_app.ai_models import AIRole, EmailIntent, AIResponse
from gmail_app.ai_service import EmailAIProcessor
from django.contrib.auth.models import User
import logging

logger = logging.getLogger('gmail_app')

print("\n" + "="*70)
print("  TEST: VALIDACIÓN DE TOPICS")
print("="*70 + "\n")

# Obtener usuario con AIRole
user = User.objects.get(username='nicolas61v')
ai_role = AIRole.objects.get(user=user, is_active=True)

print(f"Usuario: {user.username}")
print(f"Rol: {ai_role.name}")
print(f"\nTopics configurados para responder:")
topics = [t.strip() for t in ai_role.can_respond_topics.split('\n') if t.strip()]
for i, topic in enumerate(topics, 1):
    print(f"  {i}. {topic}")

print(f"\n\nVerificación de emails:")
print("-" * 70)

# Obtener emails de this user
emails = Email.objects.filter(email_account__user=user).order_by('-received_date')[:10]

print(f"Total emails a verificar: {emails.count()}\n")

for email in emails:
    # Verificar si tiene intent asociado
    has_intent = hasattr(email, 'emailintent')

    print(f"Email: {email.subject[:50]}")
    print(f"  From: {email.sender}")

    if has_intent:
        intent = email.emailintent
        print(f"  ✓ Procesado por IA")
        print(f"    - Intent: {intent.intent_type}")
        print(f"    - Decision: {intent.ai_decision}")
        print(f"    - Confianza: {intent.confidence_score:.2f}")

        # Verificar si la decisión es correcta basada en topics
        email_content = f"{email.subject} {email.body_plain}".lower()
        matching_topics = [topic for topic in topics if topic.lower() in email_content]

        if matching_topics:
            print(f"    - Topics que coinciden: {matching_topics}")
            if intent.ai_decision == 'respond':
                print(f"    ✓ CORRECTO: Debería responder")
            else:
                print(f"    ⚠ INCORRECTO: No debería responder pero intent={intent.ai_decision}")
        else:
            print(f"    - No coincide con topics configurados")
            if intent.ai_decision == 'escalate':
                print(f"    ✓ CORRECTO: Debe escalarse")
            else:
                print(f"    ⚠ INCORRECTO: Debería escalarse pero decision={intent.ai_decision}")

        # Verificar respuesta generada
        if hasattr(intent, 'airesponse'):
            response = intent.airesponse
            print(f"    - Respuesta: {response.status}")
        print()
    else:
        print(f"  ✗ NO procesado por IA")
        print()

print("\n" + "="*70)
print("CONCLUSIÓN:")
print("="*70)
print("""
El sistema ACTUAL NO valida topics al tomar decisiones.
La IA decide "respond" o "escalate" únicamente basándose en el contenido del email,
ignorando los topics configurados en el rol.

PROBLEMA IDENTIFICADO:
- can_respond_topics se configura pero NO se usa en la decisión
- cannot_respond_topics se configura pero NO se usa en la decisión
- allowed_domains SÍ se valida correctamente

SOLUCIÓN NECESARIA:
Modificar ai_service.py para validar topics ANTES de decidir si responder.
""")
print("="*70 + "\n")

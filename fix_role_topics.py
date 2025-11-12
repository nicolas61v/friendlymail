#!/usr/bin/env python
"""
Script para actualizar los topics del rol de IA
Esto asegura que la IA responda a emails sobre "fechas de parcial"
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'friendlymail.settings')
django.setup()

from gmail_app.ai_models import AIRole

# Obtener el rol activo
role = AIRole.objects.filter(is_active=True).first()

if role:
    print(f"Rol actual: {role.name}")
    print(f"Topics actuales:")
    print(f"  Puede responder: {role.can_respond_topics}")
    print()

    # Actualizar topics para que responda a más cosas relacionadas con fechas
    new_topics = """fechas de examenes
fechas de parcial
fechas de evaluacion
temas que se veran en los examenes
horarios de clase
cronograma del curso
preguntas sobre el temario
dudas academicas"""

    role.can_respond_topics = new_topics
    role.save()

    print("[OK] Topics actualizados a:")
    print(f"  {role.can_respond_topics}")
    print()
    print("Ahora la IA responderá a:")
    print("  - Fechas de exámenes")
    print("  - Fechas de parcial")
    print("  - Fechas de evaluación")
    print("  - Temas de exámenes")
    print("  - Horarios")
    print("  - Cronograma")
    print("  - Preguntas sobre temario")
    print("  - Dudas académicas")

else:
    print("[ERROR] No hay rol activo configurado")

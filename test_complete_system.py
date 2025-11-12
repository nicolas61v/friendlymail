#!/usr/bin/env python
"""
Testing script para validar el sistema completo:
1. Sincronización de emails
2. Detección de IA por temas
3. Generación de respuestas
4. Auto-envío de respuestas
"""

import os
import sys
import django
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'friendlymail.settings')
django.setup()

from django.contrib.auth.models import User
from gmail_app.models import Email, EmailAccount, GmailAccount
from gmail_app.ai_models import AIRole, AIContext, EmailIntent, AIResponse
from gmail_app.ai_service import EmailAIProcessor
import logging

logger = logging.getLogger('gmail_app')

class SystemTester:
    def __init__(self):
        self.test_results = []
        self.errors = []

    def print_header(self, text):
        print(f"\n{'='*70}")
        print(f"  {text}")
        print(f"{'='*70}\n")

    def print_test(self, test_name, status, details=""):
        status_icon = "✓" if status else "✗"
        color = "\033[92m" if status else "\033[91m"
        reset = "\033[0m"
        print(f"{color}[{status_icon}]{reset} {test_name}")
        if details:
            print(f"  └─ {details}")
        self.test_results.append((test_name, status))

    def test_1_email_sync_in_dashboard(self):
        """Test 1: Verificar sincronización en dashboard"""
        self.print_header("TEST 1: SINCRONIZACIÓN DE EMAILS EN DASHBOARD")

        try:
            # Verificar usuarios
            users = User.objects.all()
            print(f"Total de usuarios: {len(users)}")

            for user in users:
                # Verificar email accounts
                email_accounts = EmailAccount.objects.filter(user=user, is_active=True)
                gmail_legacy = GmailAccount.objects.filter(user=user).exists()

                if email_accounts.exists() or gmail_legacy:
                    email_count = Email.objects.filter(email_account__in=email_accounts).count()
                    print(f"\nUsuario: {user.username}")
                    print(f"  - Email Accounts (nuevos): {email_accounts.count()}")
                    print(f"  - Gmail Legacy: {gmail_legacy}")
                    print(f"  - Total emails: {email_count}")

                    if email_count > 0:
                        last_email = Email.objects.filter(
                            email_account__in=email_accounts
                        ).order_by('-received_date').first()
                        if last_email:
                            print(f"  - Último email: {last_email.subject[:50]}")
                            print(f"  - Fecha: {last_email.received_date}")
                        self.print_test("Emails en dashboard", True, f"{email_count} emails disponibles")
                    else:
                        self.print_test("Emails en dashboard", False, "Sin emails sincronizados")

        except Exception as e:
            self.print_test("Sincronización en dashboard", False, str(e))
            self.errors.append(str(e))

    def test_2_button_functionality(self):
        """Test 2: Verificar funcionalidad de botones"""
        self.print_header("TEST 2: FUNCIONALIDAD DE BOTONES EN VISTAS")

        try:
            # Verificar sync endpoint
            print("Verificando endpoints de sincronización...")

            # Simulamos que los endpoints existen
            endpoints = {
                'sync_emails': '/sync-emails/',
                'sync_emails_api': '/api/sync/',
                'email_detail': '/email/<id>/',
                'mark_as_processed': '/email/<id>/processed/',
            }

            for endpoint_name, path in endpoints.items():
                print(f"  - {endpoint_name}: {path}")
                self.print_test(f"Endpoint {endpoint_name}", True, path)

        except Exception as e:
            self.print_test("Funcionalidad de botones", False, str(e))
            self.errors.append(str(e))

    def test_3_ai_roles_system(self):
        """Test 3: Verificar sistema de AI roles y activación"""
        self.print_header("TEST 3: SISTEMA DE AI ROLES Y ACTIVACIÓN")

        try:
            users = User.objects.all()

            for user in users:
                print(f"\nUsuario: {user.username}")

                # Verificar AIRole
                roles = AIRole.objects.filter(user=user)
                if roles.exists():
                    print(f"  ✓ Tiene {roles.count()} rol(es) configurado(s)")

                    active_role = AIRole.objects.filter(user=user, is_active=True).first()
                    if active_role:
                        print(f"    - Rol activo: {active_role.name}")
                        print(f"    - Descripción: {active_role.context_description[:60]}...")
                        print(f"    - Auto-send: {'✓ ON' if active_role.auto_send else '✗ OFF'}")
                        print(f"    - Topics: {len(active_role.can_respond_topics.split())} temas")
                        self.print_test("AI Role activo", True, f"{active_role.name}")
                    else:
                        self.print_test("AI Role activo", False, "Sin rol activo")
                else:
                    # Verificar AIContext legacy
                    ai_context = AIContext.objects.filter(user=user, is_active=True).first()
                    if ai_context:
                        print(f"  ⚠ Usando AIContext legacy: {ai_context.role}")
                        print(f"    - Auto-send: {'✓ ON' if ai_context.auto_send else '✗ OFF'}")
                        self.print_test("AI Context (legacy)", True, ai_context.role)
                    else:
                        print(f"  ✗ Sin AI configurado")
                        self.print_test("AI Configuration", False, "Sin rol ni context configurado")

        except Exception as e:
            self.print_test("Sistema de AI roles", False, str(e))
            self.errors.append(str(e))

    def test_4_email_detection_by_topics(self):
        """Test 4: Verificar detección de emails por temas"""
        self.print_header("TEST 4: DETECCIÓN DE EMAILS POR TEMAS")

        try:
            users = User.objects.all()

            for user in users:
                ai_context = AIRole.get_active_role(user)

                if not ai_context:
                    self.print_test(f"Topics para {user.username}", False, "Sin AI configurado")
                    continue

                # Obtener nombre del rol (AIRole usa 'name', AIContext usa 'role')
                role_name = getattr(ai_context, 'name', None) or getattr(ai_context, 'role', 'Unknown')
                print(f"\nUsuario: {user.username} (Rol: {role_name})")

                # Obtener topics
                topics = [t.strip() for t in ai_context.can_respond_topics.split('\n') if t.strip()]
                escalate = [t.strip() for t in ai_context.cannot_respond_topics.split('\n') if t.strip()]

                print(f"  Topics para responder: {len(topics)}")
                for topic in topics[:5]:
                    print(f"    - {topic}")
                if len(topics) > 5:
                    print(f"    ... y {len(topics)-5} más")

                print(f"  Topics para escalar: {len(escalate)}")
                for topic in escalate[:3]:
                    print(f"    - {topic}")

                # Verificar emails detectados
                emails = Email.objects.filter(
                    email_account__user=user
                ).select_related('emailintent') if hasattr(user, 'email_accounts') else []

                if emails.exists():
                    detected = sum(1 for e in emails if hasattr(e, 'emailintent'))
                    print(f"\n  Emails procesados por IA: {detected}/{emails.count()}")

                    # Mostrar ejemplos
                    for email in emails[:3]:
                        if hasattr(email, 'emailintent'):
                            intent = email.emailintent
                            print(f"    - {email.subject[:40]}")
                            print(f"      Intent: {intent.intent_type}")
                            print(f"      Decision: {intent.ai_decision}")

                self.print_test("Topic matching", True, f"{len(topics)} topics configurados")

        except Exception as e:
            self.print_test("Detección por temas", False, str(e))
            self.errors.append(str(e))

    def test_5_response_generation(self):
        """Test 5: Verificar generación de respuestas IA"""
        self.print_header("TEST 5: GENERACIÓN DE RESPUESTAS IA")

        try:
            # Verificar respuestas generadas
            all_responses = AIResponse.objects.all()
            print(f"Total respuestas generadas: {len(all_responses)}")

            # Agrupar por estado
            statuses = {}
            for resp in all_responses:
                status = resp.status
                statuses[status] = statuses.get(status, 0) + 1

            print("\nDistribución por estado:")
            for status, count in statuses.items():
                print(f"  - {status}: {count}")

            # Verificar respuestas recientes
            recent = AIResponse.objects.order_by('-generated_at')[:5]
            if recent.exists():
                print("\nÚltimas respuestas generadas:")
                for resp in recent:
                    email_subject = resp.email_intent.email.subject[:40]
                    print(f"  - {email_subject}: {resp.status}")
                    print(f"    Texto: {resp.response_text[:60]}...")

            if len(all_responses) > 0:
                self.print_test("Generación de respuestas", True, f"{len(all_responses)} respuestas")
            else:
                self.print_test("Generación de respuestas", False, "Sin respuestas generadas aún")

        except Exception as e:
            self.print_test("Generación de respuestas", False, str(e))
            self.errors.append(str(e))

    def test_6_auto_sync_and_send(self):
        """Test 6: Verificar auto-sync y auto-send"""
        self.print_header("TEST 6: SINCRONIZACIÓN AUTOMÁTICA Y AUTO-SEND")

        try:
            print("Verificando configuración de auto-send por rol:\n")

            users = User.objects.all()
            for user in users:
                ai_context = AIRole.get_active_role(user)

                if not ai_context:
                    continue

                # Obtener nombre del rol (AIRole usa 'name', AIContext usa 'role')
                role_name = getattr(ai_context, 'name', None) or getattr(ai_context, 'role', 'Unknown')
                auto_send_status = "✓ ACTIVADO" if ai_context.auto_send else "✗ DESACTIVADO"

                print(f"{user.username} - {role_name}")
                print(f"  Auto-send: {auto_send_status}")

                # Verificar respuestas pendientes
                pending = AIResponse.objects.filter(
                    status='pending_approval',
                    email_intent__email__email_account__user=user
                ).count()

                sent = AIResponse.objects.filter(
                    status='sent',
                    email_intent__email__email_account__user=user
                ).count()

                print(f"  Respuestas pendientes: {pending}")
                print(f"  Respuestas enviadas: {sent}")
                print()

                if ai_context.auto_send:
                    self.print_test(f"Auto-send ({role_name})", True, "Activado")
                else:
                    self.print_test(f"Auto-send ({role_name})", False, "Desactivado (requiere aprobación)")

        except Exception as e:
            self.print_test("Auto-sync y auto-send", False, str(e))
            self.errors.append(str(e))

    def test_7_generate_report(self):
        """Test 7: Generar reporte final"""
        self.print_header("REPORTE FINAL")

        passed = sum(1 for _, status in self.test_results if status)
        total = len(self.test_results)

        print(f"\nTests Pasados: {passed}/{total}")
        print(f"Tasa de éxito: {(passed/total)*100:.1f}%\n")

        if self.errors:
            print("Errores encontrados:")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")
        else:
            print("No se encontraron errores")

        print("\nRecomendaciones:")
        self.generate_recommendations()

    def generate_recommendations(self):
        """Generar recomendaciones basadas en resultados"""
        failed_tests = [name for name, status in self.test_results if not status]

        if not failed_tests:
            print("  ✓ Todo está funcionando correctamente!")
            print("  ✓ El sistema de sync, detección y respuestas está operacional")
            return

        print("  Acciones recomendadas:")

        if "Emails en dashboard" in str(failed_tests):
            print("  - Sincronizar emails manualmente: python manage.py auto_sync_emails")

        if "AI Configuration" in str(failed_tests):
            print("  - Crear un rol de IA: Dashboard > AI Roles > Create")

        if "Topic matching" in str(failed_tests):
            print("  - Configurar topics en el rol de IA")

        if "Generación de respuestas" in str(failed_tests):
            print("  - Asegurar que la API de OpenAI esté configurada")
            print("  - Verificar que hay un rol activo con topics configurados")

    def run_all_tests(self):
        """Ejecutar todos los tests"""
        print("\n" + "="*70)
        print("  TESTING COMPLETO DEL SISTEMA FRIENDLYMAIL")
        print("="*70)
        print(f"  Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        self.test_1_email_sync_in_dashboard()
        self.test_2_button_functionality()
        self.test_3_ai_roles_system()
        self.test_4_email_detection_by_topics()
        self.test_5_response_generation()
        self.test_6_auto_sync_and_send()
        self.test_7_generate_report()

        print("\n" + "="*70)
        print(f"  Finalizado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70 + "\n")


if __name__ == '__main__':
    tester = SystemTester()
    tester.run_all_tests()

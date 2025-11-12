#!/usr/bin/env python
"""
Solucionar problema de UnicodeEncodeError en Windows
El problema es que Windows (cmd) usa cp1252 encoding que no soporta emojis/caracteres especiales
"""

import os
import sys

# Opción 1: Agregar esto a friendlymail/settings.py para logging
print("OPCIÓN 1: Agregar a friendlymail/settings.py\n")
print("""
# Al principio del archivo settings.py, agregar:
import io
import sys

# Configurar UTF-8 para Windows
if sys.platform == 'win32':
    # Redirigir stdout/stderr a UTF-8
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

    # O más simple:
    import os
    os.environ['PYTHONIOENCODING'] = 'utf-8'
""")

print("\n" + "="*70)
print("\nOPCIÓN 2: Ejecutar Django con encoding UTF-8\n")
print("""
# En lugar de: python manage.py runserver
# Usa:         PYTHONIOENCODING=utf-8 python manage.py runserver

# O en Windows:
# Usando PowerShell: $env:PYTHONIOENCODING='utf-8'; python manage.py runserver
# Usando CMD: chcp 65001 && python manage.py runserver
""")

print("\n" + "="*70)
print("\nOPCIÓN 3: Modificar logging en friendlymail/settings.py\n")
print("""
# En la sección LOGGING, cambiar el formato sin emojis:

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {name} - {message}',  # SIN emojis
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}
""")

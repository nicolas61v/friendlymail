"""
System utility views - Logs, diagnostics
"""
import logging
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

logger = logging.getLogger('gmail_app')


@login_required
def system_logs(request):
    """Display system logs for debugging"""
    try:
        with open('logs/app.log', 'r') as f:
            logs = f.readlines()[-100:]  # Last 100 lines
        return JsonResponse({
            'success': True,
            'logs': logs
        })
    except FileNotFoundError:
        return JsonResponse({
            'success': False,
            'error': 'Log file not found'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

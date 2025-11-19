"""
AI Role management views - Create, edit, activate, delete AI roles and temporal rules
"""
import logging
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from ..ai_models import AIRole, TemporalRule

logger = logging.getLogger('gmail_app')


@login_required
def ai_roles_list(request):
    """List all AI roles for the current user with management options"""
    try:
        # Get all roles for this user
        roles = AIRole.objects.filter(user=request.user).order_by('-is_active', '-updated_at')
        active_role = AIRole.get_active_role(request.user)

        context = {
            'roles': roles,
            'active_role': active_role,
            'total_roles': roles.count(),
            'has_roles': roles.exists()
        }

        return render(request, 'gmail_app/ai_roles_list.html', context)
    except Exception as e:
        logger.error(f"Error loading AI roles for user {request.user.username}: {e}")
        messages.error(request, f'❌ Error loading roles: {str(e)}')
        return redirect('dashboard')


@login_required
def ai_role_create(request):
    """Create a new AI role"""
    if request.method == 'GET':
        context = {
            'complexity_choices': AIRole.COMPLEXITY_CHOICES
        }
        return render(request, 'gmail_app/ai_role_create.html', context)

    elif request.method == 'POST':
        try:
            role_name = request.POST.get('name', '').strip()
            can_respond_topics = request.POST.get('can_respond_topics', '').strip()

            # Validate role name
            if not role_name:
                messages.error(request, '❌ Role name is required')
                return redirect('ai_role_create')

            # Validate topics (required for AI to respond)
            if not can_respond_topics:
                messages.error(request, '❌ You must specify at least one topic that the AI can respond to. Without topics, the AI will not respond to any emails.')
                return redirect('ai_role_create')

            # Check if role name already exists for this user
            if AIRole.objects.filter(user=request.user, name=role_name).exists():
                messages.error(request, f'❌ You already have a role named "{role_name}"')
                return redirect('ai_role_create')

            # Create new role
            role = AIRole.objects.create(
                user=request.user,
                name=role_name,
                context_description=request.POST.get('context_description', ''),
                complexity_level=request.POST.get('complexity_level', 'simple'),
                can_respond_topics=can_respond_topics,
                cannot_respond_topics=request.POST.get('cannot_respond_topics', ''),
                allowed_domains=request.POST.get('allowed_domains', ''),
                auto_send=request.POST.get('auto_send') == 'on',
                is_active=True  # New roles are active by default
            )

            messages.success(request, f'✅ AI role "{role.name}" created successfully!')
            logger.info(f"AI role created by user {request.user.username}: {role.name}")

            return redirect('ai_role_edit', role_id=role.id)

        except Exception as e:
            logger.error(f"Error creating AI role for user {request.user.username}: {e}")
            messages.error(request, f'❌ Error creating role: {str(e)}')
            return redirect('ai_roles_list')


@login_required
def ai_role_edit(request, role_id):
    """Edit an existing AI role"""
    try:
        role = AIRole.objects.get(id=role_id, user=request.user)
    except AIRole.DoesNotExist:
        messages.error(request, '❌ Role not found')
        return redirect('ai_roles_list')

    if request.method == 'GET':
        # Get temporal rules for this role
        rules = TemporalRule.objects.filter(
            ai_role=role
        ).order_by('-priority', '-created_at')

        context = {
            'role': role,
            'temporal_rules': rules,
            'complexity_choices': AIRole.COMPLEXITY_CHOICES,
            'is_active_role': role.is_active
        }

        return render(request, 'gmail_app/ai_role_edit.html', context)

    elif request.method == 'POST':
        try:
            # Validate topics (required for AI to respond)
            can_respond_topics = request.POST.get('can_respond_topics', '').strip()
            if not can_respond_topics:
                messages.error(request, '❌ You must specify at least one topic that the AI can respond to. Without topics, the AI will not respond to any emails.')
                return redirect('ai_role_edit', role_id=role_id)

            # Update role fields
            role.context_description = request.POST.get('context_description', '')
            role.complexity_level = request.POST.get('complexity_level', 'simple')
            role.can_respond_topics = can_respond_topics
            role.cannot_respond_topics = request.POST.get('cannot_respond_topics', '')
            role.allowed_domains = request.POST.get('allowed_domains', '')
            role.auto_send = request.POST.get('auto_send') == 'on'

            role.save()

            messages.success(request, f'✅ AI role "{role.name}" updated successfully!')
            logger.info(f"AI role updated by user {request.user.username}: {role.name}")

            return redirect('ai_role_edit', role_id=role.id)

        except Exception as e:
            logger.error(f"Error updating AI role {role_id} for user {request.user.username}: {e}")
            messages.error(request, f'❌ Error updating role: {str(e)}')
            return redirect('ai_role_edit', role_id=role.id)


@login_required
def ai_role_activate(request, role_id):
    """Activate an AI role (deactivate others)"""
    try:
        role = AIRole.objects.get(id=role_id, user=request.user)

        # The save() method will automatically deactivate other roles
        role.is_active = True
        role.save()

        messages.success(request, f'✅ Switched to role "{role.name}"')
        logger.info(f"User {request.user.username} activated AI role: {role.name}")

        return redirect('ai_roles_list')

    except AIRole.DoesNotExist:
        messages.error(request, '❌ Role not found')
        return redirect('ai_roles_list')
    except Exception as e:
        logger.error(f"Error activating AI role {role_id} for user {request.user.username}: {e}")
        messages.error(request, f'❌ Error activating role: {str(e)}')
        return redirect('ai_roles_list')


@login_required
def ai_role_delete(request, role_id):
    """Delete an AI role"""
    try:
        role = AIRole.objects.get(id=role_id, user=request.user)
        role_name = role.name

        # Check if this is the last role
        other_roles = AIRole.objects.filter(user=request.user).exclude(id=role_id)
        if not other_roles.exists():
            messages.error(request, '❌ Cannot delete your only role. Create another role first.')
            return redirect('ai_roles_list')

        # If deleting active role, activate the first available role
        if role.is_active:
            first_other_role = other_roles.first()
            first_other_role.is_active = True
            first_other_role.save()

        role.delete()

        messages.success(request, f'🗑️ AI role "{role_name}" deleted successfully')
        logger.info(f"AI role deleted by user {request.user.username}: {role_name}")

        return redirect('ai_roles_list')

    except AIRole.DoesNotExist:
        messages.error(request, '❌ Role not found')
        return redirect('ai_roles_list')
    except Exception as e:
        logger.error(f"Error deleting AI role {role_id} for user {request.user.username}: {e}")
        messages.error(request, f'❌ Error deleting role: {str(e)}')
        return redirect('ai_roles_list')


@login_required
def ai_role_temporal_rule_save(request, role_id):
    """Save or update a temporal rule for a specific role"""
    if request.method == 'POST':
        try:
            role = AIRole.objects.get(id=role_id, user=request.user)

            rule_id = request.POST.get('rule_id')

            if rule_id:
                # Update existing rule
                rule = TemporalRule.objects.get(id=rule_id, ai_role=role)
                action = 'updated'
            else:
                # Create new rule
                rule = TemporalRule(ai_role=role)
                action = 'created'

            # Update fields
            rule.name = request.POST.get('name', '')
            rule.description = request.POST.get('description', '')
            rule.start_date = request.POST.get('start_date')
            rule.end_date = request.POST.get('end_date')
            rule.keywords = request.POST.get('keywords', '')
            rule.email_filters = request.POST.get('email_filters', '')
            rule.response_template = request.POST.get('response_template', '')
            rule.status = request.POST.get('status', 'draft')
            rule.priority = int(request.POST.get('priority', 1))

            rule.save()

            messages.success(request, f'⏰ Temporal rule "{rule.name}" {action} successfully!')
            logger.info(f"Temporal rule {action} by user {request.user.username} in role {role.name}: {rule.name}")

        except AIRole.DoesNotExist:
            messages.error(request, '❌ Role not found')
        except Exception as e:
            logger.error(f"Error saving temporal rule for user {request.user.username}: {e}")
            messages.error(request, f'❌ Error saving rule: {str(e)}')

    return redirect('ai_role_edit', role_id=role_id)


@login_required
def ai_role_temporal_rule_delete(request, role_id, rule_id):
    """Delete a temporal rule from a role"""
    try:
        role = AIRole.objects.get(id=role_id, user=request.user)
        rule = TemporalRule.objects.get(id=rule_id, ai_role=role)
        rule_name = rule.name
        rule.delete()

        messages.success(request, f'🗑️ Rule "{rule_name}" deleted successfully')
        logger.info(f"Temporal rule deleted by user {request.user.username} in role {role.name}: {rule_name}")

    except (AIRole.DoesNotExist, TemporalRule.DoesNotExist):
        messages.error(request, '❌ Role or rule not found')
    except Exception as e:
        logger.error(f"Error deleting temporal rule for user {request.user.username}: {e}")
        messages.error(request, f'❌ Error deleting rule: {str(e)}')

    return redirect('ai_role_edit', role_id=role_id)

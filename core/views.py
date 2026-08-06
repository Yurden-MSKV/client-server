import json
import logging
import os
from io import BytesIO

import requests
from decouple import config
from django.conf import settings
from django.core.files import File
from django.http import JsonResponse, HttpResponseForbidden, HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from core.models import User

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def sync_user_view(request):
    # Явно отключаем CSRF проверку для этого запроса (доп. страховка)
    setattr(request, '_dont_enforce_csrf_checks', True)

    logger.info("=== sync_user_view called ===")
    logger.info(f"Path: {request.path}")
    logger.info(f"Method: {request.method}")
    logger.info(f"Headers: {dict(request.headers)}")

    auth_header = request.headers.get('Authorization')
    logger.info(f"Auth header: {auth_header}")

    expected_token = getattr(settings, 'PROVIDER_SYNC_SECRET', None)
    logger.info(f"Expected token: {expected_token}")

    if not expected_token:
        logger.error("Server misconfiguration: PROVIDER_SYNC_SECRET not set")
        return JsonResponse({'error': 'Server misconfiguration'}, status=500)

    if auth_header != f'Bearer {expected_token}':
        logger.warning("Invalid token")
        return HttpResponseForbidden('Invalid token')

    logger.info("Token valid")

    try:
        data = json.loads(request.body)
        logger.info(f"Received data: {data}")
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    required_fields = ['id', 'email', 'first_name']
    if not all(field in data for field in required_fields):
        logger.error("Missing required fields")
        return JsonResponse({'error': 'Missing required fields'}, status=400)

    from .models import User
    user, created = User.objects.update_or_create(
        provider_id=data['id'],
        defaults={
            'email': data['email'],
            'first_name': data['first_name'],
            'last_name': data['last_name'],
            'is_staff': data['is_staff'],
            'is_active': data['is_active'],
            'bio': data['bio'],
            'pic': data['pic']
        }
    )

    logger.info(f"User {'created' if created else 'updated'} with provider_id={data['id']}")

    status_code = 201 if created else 200
    response = JsonResponse({
        'status': 'success',
        'action': 'created' if created else 'updated',
        'provider_id': user.provider_id,
        'local_id': user.id
    }, status=status_code)

    logger.info("Returning response")
    return response


def sync_user_from_root(user):
    social = user.social_auth.filter(provider='myauthserver').first()
    if not social:
        return

    access_token = social.extra_data.get('access_token')
    if not access_token:
        return

    url = f'http://{config("CURRENT_IP")}:8000/api/userinfo/'
    try:
        response = requests.get(
            url,
            headers={'Authorization': f'Bearer {access_token}'},
            timeout=3
        )
        if response.status_code == 200:
            data = response.json()
            updated = False

            if user.is_superuser != data.get('is_superuser', False):
                user.is_superuser = data.get('is_superuser', False)
                updated = True

            avatar_url = data.get('pic')

            if avatar_url:
                res = requests.get(avatar_url, timeout=3)
                if res.status_code == 200:
                    filename = os.path.basename(avatar_url.split('?')[0])
                    user.pic.save(filename, File(BytesIO(res.content)), save=False)
                    updated = True
            else:
                if user.pic:
                    user.pic.delete(save=False)
                    updated = True

            social.extra_data.update(data)
            social.save()

            if updated:
                user.save()

    except Exception as e:
        print(f"[SYNC ERROR] Не удалось обновить профиль: {e}")


def index(request):
    if request.user.is_authenticated:
        return redirect('profile_page')
    else:
        return redirect('social:begin', 'myauthserver')


def profile_page(request):
    if request.user.is_authenticated:
        sync_user_from_root(request.user)

        return render(request, 'profile_page.html', {'user': request.user})
    else:
        return HttpResponse('Ты не залогинен.')

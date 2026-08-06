import os
from io import BytesIO

import requests
from decouple import config
from django.core.files import File
from social_core.backends.oauth import BaseOAuth2


class MyOAuth2Backend(BaseOAuth2):
    name = 'myauthserver'
    REDIRECT_STATE = False

    # AUTHORIZATION_URL = 'http://127.0.0.1:8000/o/authorize/'
    AUTHORIZATION_URL = f'http://{config('CURRENT_IP')}:8000/o/authorize/'
    # ACCESS_TOKEN_URL = 'http://127.0.0.1:8000/o/token/'
    ACCESS_TOKEN_URL = f'http://{config('CURRENT_IP')}:8000/o/token/'
    # ACCESS_TOKEN_METHOD = 'POST'
    ACCESS_TOKEN_METHOD = 'POST'
    # REFRESH_TOKEN_URL = 'http://127.0.0.1:8000/o/token/'
    REFRESH_TOKEN_URL = f'http://{config('CURRENT_IP')}:8000/o/token/'

    EXTRA_DATA = [
        ('username', 'username'),
        ('email', 'email'),
        ('is_superuser', 'is_superuser'),
        ('access_token', 'access_token'),
        ('pic', 'pic'),
    ]

    def get_user_details(self, response):
        print(f"[DEBUG] get_user_details вызван. response keys: {response.keys()}")
        return {
            'username': response.get('username'),
            'email': response.get('email'),
            'first_name': response.get('first_name', ''),
            'last_name': response.get('last_name', ''),
            'is_superuser': response.get('is_superuser', False),
            'pic': response.get('pic'),
        }

    def user_data(self, access_token, *args, **kwargs):
        print(f"[DEBUG] user_data вызван с токеном: {access_token[:10]}...")
        url = f'http://{config('CURRENT_IP')}:8000/api/userinfo/'
        return self.get_json(url, headers={
            'Authorization': f'Bearer {access_token}'
        })

    def update_user_details(self, user, response, *args, **kwargs):
        print(f"[DEBUG] update_user_details ВЫЗВАН для {user.username}")
        print(f"[DEBUG] response содержит is_superuser: {response.get('is_superuser')}")
        print(f"[DEBUG] текущий user.is_superuser: {user.is_superuser}")

        is_superuser = response.get('is_superuser')
        if is_superuser is not None and user.is_superuser != is_superuser:
            user.is_superuser = is_superuser
            user.save()
            self.strategy.storage.user.changed(user)
            print(f"[DEBUG] ОБНОВЛЁН is_superuser для {user.username} на {is_superuser}")
        else:
            print(f"[DEBUG] НЕ ОБНОВЛЁН: is_superuser={is_superuser}, user.is_superuser={user.is_superuser}")

        avatar_url = response.get('pic')
        if avatar_url:
            try:
                res = requests.get(avatar_url, timeout=5)
                if res.status_code == 200:
                    filename = os.path.basename(avatar_url.split('?')[0])
                    user.pic.save(filename, File(BytesIO(res.content)), save=True)
                    print('Должно было сохранить')
            except Exception as e:
                print(f'[ERROR] Не удалось скачать аватар: {e}')
        else:
            print('Ссылка не получена')

        self.strategy.storage.user.changed(user)

    def validate_state(self):
        pass
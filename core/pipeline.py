from social_core.exceptions import AuthException


def save_provider_id(backend, details, response, user=None, uid=None, *args, **kwargs):
    """
    Сохраняет provider_id из uid (или response) после создания пользователя.
    """
    if user and not user.provider_id:
        # uid уже извлечён social_core, он обычно равен ID пользователя у провайдера
        provider_user_id = uid
        if not provider_user_id:
            # fallback на response
            provider_user_id = response.get('id') or response.get('sub')
        if not provider_user_id:
            raise AuthException(backend, "Не удалось получить ID пользователя от провайдера")

        user.provider_id = provider_user_id
        user.save(update_fields=['provider_id'])

    return {'user': user}
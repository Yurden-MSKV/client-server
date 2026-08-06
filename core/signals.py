from django.db.models.signals import post_save
from django.dispatch import receiver
from social_django.models import UserSocialAuth


@receiver(post_save, sender=UserSocialAuth)
def sync_superuser_from_oauth(sender, instance, created, **kwargs):
    if instance.provider == 'myauthserver':
        is_superuser = instance.extra_data.get('is_superuser', False)
        user = instance.user

        if user.is_superuser != is_superuser:
            user.is_superuser = is_superuser
            user.save()
            print(f"[SIGNAL] Обновлён is_superuser для {user.username}: {is_superuser}")


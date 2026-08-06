from django.contrib.auth.models import AbstractUser
from django.db import models
from django.templatetags.static import static


def profile_pic_path(instance, filename):
    return f'profiles/{instance.id}/{filename}'

class User(AbstractUser):
    provider_id = models.PositiveIntegerField(
        unique=True,
        db_index=True,
        null=True,
        blank=True
    )
    email = models.EmailField()
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    bio = models.TextField(blank=True,
                           null=True,
                           verbose_name='О себе')
    pic = models.ImageField(upload_to=profile_pic_path,
                            null=True,
                            blank=True,
                            verbose_name='Аватарка')

    last_synced = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.username}"

    @property
    def avatar_url(self):
        if self.pic and hasattr(self.pic, "url"):
            return self.pic.url
        return static("images/default_avatar.png")
import uuid

from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    fio = models.CharField(verbose_name='ФИО', max_length=250, null=True, blank=True)
    phone = models.CharField(verbose_name='Телефон', max_length=250, null=True, blank=True)
    status = models.BooleanField(verbose_name='Статус', default=True)
    iin = models.CharField(verbose_name='ИИН', max_length=15, default='000000000000', null=True, blank=True)
    telegram = models.CharField(verbose_name='Telegram', max_length=250, null=True, blank=True)
    one_off = models.CharField(verbose_name='Одноразовый пароль', max_length=250, null=True, blank=True)
    profile_image = models.ImageField(upload_to='profile_images', null=True, blank=True, verbose_name='Аватарка')
    groups = models.ManyToManyField('auth.Group', related_name='users', related_query_name='user', blank=True)
    user_permissions = models.ManyToManyField('auth.Permission', related_name='users', related_query_name='user', blank=True)







        
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser
from django.contrib.auth.models import User
admin.site.unregister(User)
admin.site.site_header = 'Панель администратора'
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'fio', 'phone', 'status', 'iin', 'telegram', 'one_off', 'profile_image')


admin.site.register(CustomUser, CustomUserAdmin)


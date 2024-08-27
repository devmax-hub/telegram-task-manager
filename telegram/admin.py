from django.contrib import admin
from .models import *
from django.contrib.auth.models import Group, User
from django.utils.translation import gettext_lazy as _


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    # list_display = ('surname', 'name', 'middle_name', 'status', 'comment', 'strike', 'created_at', 'updated_at', 'level', 'position', 'account', 'iin', 'chat_id', 'phone', 'email', 'telegram', 'rating')
    list_display = ('surname', 'name', 'middle_name', 'status', 'comment', 'strike', 'created_at', 'updated_at', 'level', 'position', 'iin', 'chat_id', 'phone', 'email', 'telegram', 'rating')
    readonly_fields = ('chat_id',)

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at', 'updated_at', 'file', 'link')

@admin.register(EmployeeTask)
class EmployeeTaskAdmin(admin.ModelAdmin):
    list_display = ('employee', 'task', 'created_at', 'updated_at', 'status', 'deadline', 'priority', 'checked', 'rating')
    readonly_fields = ['employee']
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('employee', 'task', 'created_at', 'message', 'status')
    readonly_fields = ('employee', 'task', 'created_at', 'updated_at', 'message', 'status')

    def has_add_permission(self, request, obj=None):
        return False
    def has_change_permission(self, request, obj=None):
        return False

@admin.register(TaskHistory)
class TaskHistoryAdmin(admin.ModelAdmin):
    list_display = ('employee', 'task', 'created_at')
    readonly_fields = ('employee', 'task', 'created_at', 'updated_at')
    def has_add_permission(self, request, obj=None):
        return False
    def has_change_permission(self, request, obj=None):
        return False

@admin.register(Balance)
class BalanceAdmin(admin.ModelAdmin):
    list_display = ('employee', 'created_at', 'updated_at', 'balance') 

@admin.register(WithdrawDeposit)
class WithdrawDepositAdmin(admin.ModelAdmin):
    list_display = ('balance', 'amount', 'status', 'type', 'created_at', 'updated_at')

# @admin.register(CustomUser)
# class CustomUserAdmin(admin.ModelAdmin):
#     fieldsets = (
#         (None, {'fields': ('email', 'password')}),
#         (_('Personal info'), {'fields': ('first_name', 'last_name')}),
#         (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
#         (_('Important dates'), {'fields': ('last_login',)}),
#     )
#     add_fieldsets = (
#         (None, {
#             'classes': ('wide',),
#             'fields': ('email', 'first_name', 'last_name', 'password1', 'password2'),
#         }),
#     )
#     list_display = ('email', 'first_name', 'last_name', 'is_staff')
#     search_fields = ('email', 'first_name', 'last_name')
#     ordering = ('email',)
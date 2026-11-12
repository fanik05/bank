from django.contrib import admin

from .models import Account


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('account_number', 'owner', 'balance', 'created_at')
    readonly_fields = ('account_number', 'balance', 'created_at')

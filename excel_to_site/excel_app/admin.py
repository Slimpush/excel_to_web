from django.contrib import admin

from .models import AccountData, Accounts, UploadedFile


@admin.register(Accounts)
class AccountsAdmin(admin.ModelAdmin):
    list_display = ('account_number',)


@admin.register(AccountData)
class AccountDataAdmin(admin.ModelAdmin):
    list_display = ('account', 'incoming_active', 'incoming_passive',
                    'debit_turnover', 'credit_turnover', 'outgoing_active',
                    'outgoing_passive'
                    )


@admin.register(UploadedFile)
class UploadedFileAdmin(admin.ModelAdmin):
    list_display = ('file_name', 'upload_date')

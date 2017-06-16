from django.contrib import admin
from django.contrib.contenttypes import generic

from models import Transaction


class TransactionAdmin(admin.ModelAdmin):
    pass


class TransactionInlineAdmin(generic.GenericTabularInline):
    model = Transaction

    def has_add_permission(self, request):
        return False


admin.site.register(Transaction, TransactionAdmin)

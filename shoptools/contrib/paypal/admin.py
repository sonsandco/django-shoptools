from django.contrib.admin import SimpleListFilter
from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline

from .models import Transaction


class ContentTypeFilter(SimpleListFilter):
    title = 'purchase type'
    parameter_name = 'type'

    def lookups(self, request, model_admin):
        ctypes = Transaction.objects.values_list(
            'content_type__id', 'content_type__app_label',
            'content_type__model') \
            .order_by('content_type__id').distinct()
        return [(c[0], (u"%s: %s" % c[1:]).title()) for c in ctypes]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(content_type__id__exact=self.value())
        else:
            return queryset


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('amount', 'status', 'intent', 'content_object', 'created',)
    exclude = ('content_type', 'object_id')
    readonly_fields = ('amount', 'status', 'intent', 'content_object',
                       'created',)
    search_fields = ('secret', )
    list_filter = (ContentTypeFilter, )


class TransactionInlineAdmin(GenericTabularInline):
    model = Transaction
    readonly_fields = ('amount', 'status', 'intent', 'created')

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

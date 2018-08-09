from django.contrib import admin
from django.contrib.admin import SimpleListFilter

from .models import Email


class ContentTypeFilter(SimpleListFilter):
    title = 'related object'
    parameter_name = 'related_obj'

    def lookups(self, request, model_admin):
        ctypes = Email.objects.values_list(
            'related_obj_content_type__id',
            'related_obj_content_type__app_label',
            'related_obj_content_type__model') \
            .order_by('related_obj_content_type__id').distinct()
        return [(c[0], (u"%s: %s" % c[1:]).title()) for c in ctypes]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(content_type__id__exact=self.value())
        else:
            return queryset


class EmailAdmin(admin.ModelAdmin):
    related_obj_params = {}
    list_display = ('recipients', 'related_obj', 'email_type', 'status',
                    'status_updated', 'queued_until')
    list_filter = ('status', 'email_type', ContentTypeFilter)
    search_fields = ('recipients', 'text', 'html')
    readonly_fields = ('status', 'status_updated', 'queued_until',
                       'email_type', 'sent_from', 'subject', 'recipients',
                       'cc_to', 'bcc_to', 'reply_to', 'text', 'html',
                       'error_message')

admin.site.register(Email, EmailAdmin)

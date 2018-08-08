from django.contrib import admin
from django.contrib.contenttypes.models import ContentType

from .models import Email


class RelatedObjectFilter(admin.SimpleListFilter):
        def __init__(self, request, params, model, model_admin):
            self.separator = '-'
            self.title = 'Related Object'
            self.parameter_name = 'related_object'
            super(RelatedObjectFilter, self).__init__(
                request, params, model, model_admin)

        def lookups(self, request, model_admin):
            filter = 'related_obj_id' + '__isnull'
            qs = model_admin.model.objects.exclude(**{filter: True}) \
                .order_by('related_obj_content_type', 'related_obj_id') \
                .values_list('related_obj_content_type', 'related_obj_id') \
                .distinct()
            return [
                (
                    '{1}{0.separator}{2}'.format(
                        self, *content_type_and_obj_id_pair),
                    ContentType.objects
                               .get(id=content_type_and_obj_id_pair[0])
                               .model_class()
                               .objects.get(pk=content_type_and_obj_id_pair[1])
                               .__str__()
                )
                for content_type_and_obj_id_pair
                in qs
            ]

        def queryset(self, request, queryset):
            try:
                content_type_id, object_id = self.value().split(self.separator)
                return queryset.filter(**({
                    'related_obj_content_type': content_type_id,
                    'related_obj_id': object_id
                }))
            except:
                return queryset


class EmailAdmin(admin.ModelAdmin):
    related_obj_params = {}
    list_display = ('recipients', 'related_obj', 'email_type', 'status',
                    'status_updated', 'queued_until')
    list_filter = ('status', 'email_type', RelatedObjectFilter)
    search_fields = ('recipients', 'text', 'html')
    readonly_fields = ('status', 'status_updated', 'queued_until',
                       'email_type', 'sent_from', 'subject', 'recipients',
                       'cc_to', 'bcc_to', 'reply_to', 'text', 'html',
                       'error_message')

admin.site.register(Email, EmailAdmin)

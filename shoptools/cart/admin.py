from django.contrib import admin
from django import forms


def orderline_inline_factory(model_cls):
    class OrderLineForm(forms.ModelForm):
        # TODO options readonly field

        class Meta:
            model = model_cls
            exclude = []

    class OrderLineInline(admin.TabularInline):
        '''Base admin class for editing AbstractOrderLine subclasses inline.'''

        model = model_cls
        exclude = ('item_content_type', 'item_object_id', 'created')
        readonly_fields = ('quantity', 'description', 'total')
        # form = OrderLineForm

        def has_add_permission(self, request):
            return False

    return OrderLineInline

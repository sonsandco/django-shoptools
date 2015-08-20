from django.contrib.contenttypes.admin import GenericTabularInline
from django import forms

from cart.models import OrderLine


class OrderLineForm(forms.ModelForm):
    # TODO options readonly field

    class Meta:
        model = OrderLine
        exclude = []


class OrderLineInlineAdmin(GenericTabularInline):
    '''Base admin class for editing OrderLine instances inline.'''

    model = OrderLine
    ct_field = 'parent_content_type'
    ct_fk_field = 'parent_object_id'
    exclude = ('item_content_type', 'item_object_id', 'created')
    form = OrderLineForm

    def has_add_permission(self, request):
        return False

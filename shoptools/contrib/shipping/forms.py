from django import forms


class ShippingOptionSelectionForm(forms.Form):
    option_id = forms.ChoiceField(choices=(), label='Shipping')

    def __init__(self, *args, **kwargs):
        shipping_option_choices = kwargs.pop('shipping_option_choices')
        super(ShippingOptionSelectionForm, self).__init__(*args, **kwargs)
        self.fields['option_id'].choices = shipping_option_choices

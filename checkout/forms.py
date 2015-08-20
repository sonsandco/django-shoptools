from django import forms

from .models import Order


class OrderForm(forms.ModelForm):
    sanity_check = forms.CharField(widget=forms.HiddenInput, required=False)
    
    def clean(self):
        data = self.cleaned_data
        sanity_check = str(self.sanity_check) if self.sanity_check else None
        if sanity_check and str(data['sanity_check']) != sanity_check:
            err = u"Your cart appears to have changed. Please check and " \
                "confirm, then try again."
            raise forms.ValidationError(err)
        return data

    def __init__(self, *args, **kwargs):
        self.sanity_check = kwargs.pop('sanity_check', None)
        super(OrderForm, self).__init__(*args, **kwargs)
        self.initial['sanity_check'] = self.sanity_check

    class Meta:
        model = Order
        exclude = ('created', 'status', 'amount_paid', 'country')

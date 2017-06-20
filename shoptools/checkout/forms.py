from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Order, Address


class OrderForm(forms.ModelForm):
    require_unique_email = False

    sanity_check = forms.CharField(widget=forms.HiddenInput, required=False)

    def clean_email(self):
        email = self.cleaned_data['email']
        if self.require_unique_email and User.objects.filter(email=email):
            raise forms.ValidationError("That email is already in use")
        return email

    def clean(self):
        data = self.cleaned_data
        if str(data['sanity_check']) != str(self.sanity_check):
            err = "Your cart appears to have changed. Please check and " \
                "confirm, then try again."
            raise forms.ValidationError(err)
        return data

    def __init__(self, *args, **kwargs):
        self.sanity_check = kwargs.pop('sanity_check')
        super(OrderForm, self).__init__(*args, **kwargs)
        self.initial['sanity_check'] = self.sanity_check

    class Meta:
        model = Order
        exclude = ('created', 'status', 'amount_paid', 'user',
                   'estimated_delivery', )


class OrderMetaForm(forms.Form):
    """Fields which determine how an order is processed, but don't correlate
       to a model field. """

    save_details = forms.BooleanField(initial=False, required=False)
    billing_is_shipping = forms.BooleanField(initial=True, required=False)


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        exclude = ['order', 'address_type']

    def __init__(self, *args, **kwargs):
        country_choices = kwargs.pop('country_choices', None)
        super(AddressForm, self).__init__(*args, **kwargs)
        if country_choices is not None:
            self.fields['country'].choices = country_choices


class CheckoutUserForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        fields = []

    def save(self, name, email):
        user = super(CheckoutUserForm, self).save(commit=False)
        user.first_name = name.split(' ')[0]
        user.last_name = ' '.join(name.split(' ')[1:])
        user.email = email
        user.save()
        return user

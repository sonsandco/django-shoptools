from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from cart.cart import get_shipping_module
from .models import Order, GiftRecipient


def available_countries(cart):
    shipping_module = get_shipping_module()
    if shipping_module:
        countries = shipping_module.available_countries(cart)
        if countries is not None:
            return countries
    return None


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
        self.cart = kwargs.pop('cart')
        self.sanity_check = kwargs.pop('sanity_check')
        super(OrderForm, self).__init__(*args, **kwargs)
        self.initial['sanity_check'] = self.sanity_check
        countries = available_countries(self.cart)
        if countries is not None:
            self.fields['country'].choices = countries

    class Meta:
        model = Order
        exclude = ('created', 'status', 'amount_paid', 'user',
                   'estimated_delivery', )


class GiftRecipientForm(forms.ModelForm):
    class Meta:
        model = GiftRecipient
        exclude = ['order', ]

    def __init__(self, *args, **kwargs):
        super(GiftRecipientForm, self).__init__(*args, **kwargs)
        self.fields['name'].label = 'Recipient name'


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

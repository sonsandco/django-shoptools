from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Order, Address


class OrderForm(forms.ModelForm):
    require_unique_email = False

    def clean_email(self):
        email = self.cleaned_data['email']
        if self.require_unique_email and User.objects.filter(email=email):
            raise forms.ValidationError("That email is already in use")
        return email

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

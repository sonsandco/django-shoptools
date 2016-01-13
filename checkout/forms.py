from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Order, GiftRecipient, OrderReturn


class OrderForm(forms.ModelForm):
    require_unique_email = False

    sanity_check = forms.CharField(widget=forms.HiddenInput, required=False)

    def clean_email(self):
        email = self.cleaned_data['email']
        if self.require_unique_email and User.objects.filter(email=email):
            raise forms.ValidationError(u"That email is already in use")
        return email

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
        exclude = ('created', 'status', 'amount_paid', 'account',
                   'tracking_number', 'estimated_delivery', 'tracking_url')


class GiftRecipientForm(forms.ModelForm):
    class Meta:
        model = GiftRecipient
        exclude = ['order', ]


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


class ReturnForm(forms.ModelForm):
    def clean(self):
        data = self.cleaned_data
        if data['return_type'] == 'exchange' and not data['exchange_for']:
            self.add_error('exchange_for', 'This field is required')

    class Meta:
        model = OrderReturn
        exclude = ['order', 'status', ]

from django import forms
from django.utils.safestring import mark_safe

from .models import Customer


class RegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(), required=True)
    password2 = forms.CharField(widget=forms.PasswordInput(), required=True,
                                label='Reenter password')
    required_css_class = 'required'

    class Meta:
        model = Customer
        fields = ('email', 'password', 'password2', 'first_name', 'last_name',
                  'street', 'suburb', 'postcode', 'city', 'country', 'phone',
                  'delivery_instructions')
        widgets = {
            'delivery_instructions': forms.Textarea(attrs={'cols': 38, 'rows': 4}),
        }

    def clean(self):
        data = self.cleaned_data
        if data.get('password') != data.get('password2'):
            err = u"Your passwords did not match, please try again"
            raise forms.ValidationError(mark_safe(err))


class UpdateDetailsForm(forms.ModelForm):
    required_css_class = 'required'

    class Meta:
        model = Customer
        fields = ('first_name', 'last_name', 'street', 'suburb', 'postcode',
                  'city', 'country', 'phone', 'delivery_instructions')
        widgets = {
            'delivery_instructions': forms.Textarea(attrs={'cols': 38, 'rows': 4}),
        }

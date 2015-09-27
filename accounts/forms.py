from django import forms
from django.contrib.auth.models import User

from .models import Account


class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        exclude = ['user', ]


class UserForm(forms.ModelForm):
    email = forms.EmailField()

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.exclude(pk=self.instance.pk).filter(email=email):
            raise forms.ValidationError('That email is already in use')
        return email
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

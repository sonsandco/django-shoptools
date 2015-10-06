from django import forms
from django.contrib.auth.models import User

from .models import Account


class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        exclude = ['user', ]


class UserForm(forms.ModelForm):
    first_name = forms.CharField()
    last_name = forms.CharField()
    email = forms.EmailField()

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.exclude(pk=self.instance.pk).filter(email=email):
            raise forms.ValidationError('That email is already in use')
        return email

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']


class CreateUserForm(UserForm):
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(
        label="Confirm password", widget=forms.PasswordInput,
        help_text="Enter the same password again, for verification.")

    def clean(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            self.add_error('password1', "Your passwords didn't match")

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super(CreateUserForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.save()
        return user

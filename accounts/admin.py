from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django import forms

from .models import Account


class AccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'city', 'country')
    list_filter = ('city', 'country')
    search_fields = ('user__last_name', 'user__first_name', 'user__email',
                     'phone', 'address', 'country')
    # inlines = [OrderInline, ]
    readonly_fields = ('user', )

    # Allow superuser to edit readonly fields
    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            return ()
        else:
            return self.readonly_fields

admin.site.register(Account, AccountAdmin)


class AccountInline(admin.StackedInline):
    model = Account
    can_delete = False


class MyUserForm(UserAdmin.form):

    def clean_email(self):
        email = self.cleaned_data['email']
        if email and User.objects.filter(email=email) \
                         .exclude(pk=self.instance.pk).count():
            msg = "That email address is already in use"
            raise forms.ValidationError(msg)
        else:
            return email


class MyUserAdmin(UserAdmin):
    form = MyUserForm
    inlines = (AccountInline, )


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, MyUserAdmin)

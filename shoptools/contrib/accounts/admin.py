from datetime import date

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.http import HttpResponse
from django import forms

from .models import Account
from .export import generate_csv


class AccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'city', 'country')
    list_filter = ('city', 'country')
    search_fields = ('user__last_name', 'user__first_name', 'user__email',
                     'phone', 'address', 'country')
    # inlines = [OrderInline, ]
    readonly_fields = ('user', )
    actions = ('csv_export', )

    # Allow superuser to edit readonly fields
    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            return ()
        else:
            return self.readonly_fields

    def csv_export(self, request, queryset):
        filename = 'account_export_' + date.today().strftime('%Y%m%d')

        # response = HttpResponse()
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = \
            "attachment; filename=%s.csv" % filename

        generate_csv(queryset, response)
        return response


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

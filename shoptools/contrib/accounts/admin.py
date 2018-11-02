from datetime import date

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.http import HttpResponse

from .models import Account
from .export import generate_csv
from .forms import UserAdminChangeForm, UserAdminCreationForm


class AccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'city', 'country')
    list_filter = ('city', 'country')
    search_fields = ('user__last_name', 'user__first_name', 'user__email',
                     'phone', 'address', 'country')
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


class CustomUserAdmin(UserAdmin):
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups',
                   'date_joined', 'last_login')
    # Enforce unique email
    form = UserAdminChangeForm
    add_form = UserAdminCreationForm
    # add the email field in to the initial add_user form
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2')
        }),
    )
    inlines = (AccountInline, )


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

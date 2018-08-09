from django.contrib.auth.models import User
from django.core.exceptions import MultipleObjectsReturned


class EmailBackend(object):
    def authenticate(self, request=None, username=None, password=None):
        try:
            user = User.objects.get(email__iexact=username)
        except (User.DoesNotExist, MultipleObjectsReturned):
            pass
        else:
            if user.check_password(password):
                return user

        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

    supports_object_permissions = False
    supports_anonymous_user = False
    supports_inactive_user = False

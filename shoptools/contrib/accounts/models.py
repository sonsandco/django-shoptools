import uuid

from django.db import models
from django.contrib.auth.models import User
from django.dispatch import receiver

from shoptools.abstractions.models import AbstractAddress


class AccountManager(models.Manager):
    def for_user(self, user):
        if user.is_authenticated:
            try:
                return self.get(user=user)
            except Account.DoesNotExist:
                return Account(user=user)
        else:
            return Account()


class Account(AbstractAddress):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    objects = AccountManager()

    def as_dict(self):
        details = super(Account, self).as_dict()
        if self.user_id:
            details['name'] = self.user.get_full_name()
            details['email'] = self.user.email
        return details

    def __str__(self):
        return "%s %s" % (self.user.first_name, self.user.last_name)

    def name(self):
        return "%s %s" % (self.user.first_name, self.user.last_name)
    name.admin_order_field = 'user__last_name'

    def email(self):
        return self.user.email
    email.admin_order_field = 'user__email'


@receiver(models.signals.pre_save, sender=User)
def random_username(sender, instance, **kwargs):
    """Generate a random username on user save, since we don't use it at all.
    """

    if not instance.username:
        instance.username = uuid.uuid4().hex[:30]

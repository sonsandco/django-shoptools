import uuid

from django.db import models
from django.contrib.auth.models import User

from countries import COUNTRY_CHOICES
import chimp


class AccountManager(models.Manager):
    def for_user(self, user):
        try:
            return self.get(user=user)
        except Account.DoesNotExist:
            return Account(user=user)


class Account(models.Model):
    COMMON_FIELDS = ('street', 'postcode', 'city', 'state', 'country',
                     'receive_email', 'phone', )

    user = models.OneToOneField(User)
    street = models.CharField(u"Address", max_length=1023)
    postcode = models.CharField(max_length=10)
    city = models.CharField(max_length=255)
    state = models.CharField(max_length=255, blank=True, default='')
    country = models.CharField(max_length=2, choices=COUNTRY_CHOICES)
    phone = models.CharField(max_length=50, default='')
    receive_email = models.BooleanField(u"Receive our email news and offers",
                                        default=False)

    objects = AccountManager()

    def from_obj(self, obj):
        for f in self.COMMON_FIELDS:
            setattr(self, f, getattr(obj, f))

    def as_dict(self):
        details = [(f, getattr(self, f)) for f in self.COMMON_FIELDS]
        if self.user_id:
            details += [('name', self.user.get_full_name()),
                        ('email', self.user.email), ]
        return dict(details)

    def __str__(self):
        return "%s %s" % (self.user.first_name, self.user.last_name)

    def name(self):
        return "%s %s" % (self.user.first_name, self.user.last_name)
    name.admin_order_field = 'user__last_name'

    def email(self):
        return self.user.email
    email.admin_order_field = 'user__email'

    def save(self, *args, **kwargs):
        account_qs = Account.objects.filter(pk=self.pk)

        if self.receive_email:
            if not self.pk or account_qs.filter(receive_email=False) \
                                        .update(receive_email=True):
                chimp.subscribe(self.email(),
                                self.user.first_name.split(' ')[0])
        else:
            if not self.pk or account_qs.filter(receive_email=True) \
                                        .update(receive_email=False):
                chimp.unsubscribe(self.email())

        return super(Account, self).save(*args, **kwargs)


# generate a random username on save since it's not used
def random_username(sender, instance, **kwargs):
    if not instance.username:
        instance.username = uuid.uuid4().hex[:30]
models.signals.pre_save.connect(random_username, sender=User)

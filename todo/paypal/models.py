from datetime import datetime

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

from cart.models import make_uuid


class TransactionManager(models.Manager):
    def for_object(self, obj):
        ctype = ContentType.objects.get_for_model(obj)
        return self.get_query_set().filter(content_type=ctype,
                                           object_id=obj.id)


class Transaction(models.Model):
    PURCHASE = "Purchase"
    AUTH = "Auth"
    COMPLETE = "Complete"
    REFUND = "Refund"
    VALIDATE = "Validate"
    TYPE_CHOICES = [(s, s.title()) for s in
                    [PURCHASE, AUTH, COMPLETE, REFUND, VALIDATE]]

    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESSFUL = "successful"
    FAILED = "failed"
    STATUS_CHOICES = [(s, s.title()) for s in
                      [PENDING, PROCESSING, SUCCESSFUL, FAILED]]

    content_type = models.ForeignKey(ContentType,
                                     related_name='paypal_transactions')
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    created = models.DateTimeField(default=datetime.now)
    transaction_type = models.CharField(max_length=16, choices=TYPE_CHOICES,
                                        default=PURCHASE)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES,
                              default=PENDING)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True)

    secret = models.UUIDField(editable=False, default=make_uuid, db_index=True)
    result = models.TextField(blank=True)

    objects = TransactionManager()

    class Meta:
        ordering = ('-created', '-id')

    def _str__(self):
        return "%s %s of $%.2f on %s" % (self.get_status_display(),
                                         self.get_transaction_type_display().lower(),
                                         self.amount, str(self.created))

    def save(self, **kwargs):
        if self.content_object and not self.amount:
            self.amount = self.content_object.get_amount()

        return super(Transaction, self).save(**kwargs)

    @models.permalink
    def get_absolute_url(self):
        pass

    @models.permalink
    def get_success_url(self):
        return ('paypal.views.transaction_success', [self.secret])

    @models.permalink
    def get_failure_url(self):
        return ('paypal.views.transaction_failure', [self.secret])

    @property
    def merchant_reference(self):
        # Seems to have an undocumented 50 char limit
        return ("(#%d) %s" % (self.pk, str(self.content_object)))[:50]

    @property
    def transaction_id(self):
        """DPS has a stupid 16-char limit on TxnId. We use the last
        half (most random part) of the uuid with pk appended."""
        return ("%s/%d" % (self.secret, self.pk))[-16:]


## Two choices follow. BasicTransactionProtocol is the minimal subset
## required to get purchasing happening; FullTransactionProtocol
## supports notifications and recurring billing.

class BasicTransactionProtocol(object):
    """This is the minimal subset of the protocol required. Just
    implement 'amount'. This implementation will not support recurring
    payments, or success/failure notifications."""

    def get_amount(self):
        raise NotImplementedError()

    def is_recurring(self):
        return False


class FullTransactionProtocol(object):
    def get_amount(self):
        """Returns anything that can be cast to float via "%.2f"."""
        raise NotImplementedError()

    def is_recurring(self):
        """Returns boolean. If True, (set|get)_billing_token MUST also
        be implemented."""
        raise NotImplementedError()

    def set_billing_token(self, billing_token):
        """Store a billing token for recurring billing. Ignores return
        value."""
        raise NotImplementedError()

    def get_billing_token(self):
        """Returns recurring billing token or None."""
        raise NotImplementedError()

    def transaction_succeeded(self, transaction, interactive):
        """Called when a payment succeeds. Optional. May optionally return a
           success url to take the place of views.transaction_success."""
        pass

    def transaction_failed(self, transaction, interactive):
        """Called when a payment fails. Optional. May optionally return a
           success url to take the place of views.transaction_failure."""
        pass

from django.core.management.base import NoArgsCommand


class Command(NoArgsCommand):
    help = "Deletes all SavedCart database entries."

    def handle_noargs(self, **options):
        from cart.models import SavedCart
        SavedCart.objects.all().delete()

from django.contrib import admin

from cart.admin import orderline_inline_factory

from .models import Wishlist, WishlistLine


class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'created', 'items')
    inlines = [
        orderline_inline_factory(WishlistLine),
    ]

    def items(self, obj):
        return obj.wishlistline_set.count()


admin.site.register(Wishlist, WishlistAdmin)

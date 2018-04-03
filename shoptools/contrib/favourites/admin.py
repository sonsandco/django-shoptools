from django.contrib import admin

from .models import FavouritesList, FavouritesLine


class FavouritesLineInline(admin.TabularInline):
    model = FavouritesLine
    exclude = ('item_content_type', 'item_object_id', 'created', 'total',
               '_options')
    readonly_fields = ('quantity', 'description')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class FavouritesListAdmin(admin.ModelAdmin):
    list_display = ('user', 'created', 'items')
    readonly_fields = ('user', 'created', 'name')
    inlines = [FavouritesLineInline, ]
    save_on_top = True

    def items(self, obj):
        return obj.favouritesline_set.count()

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(FavouritesList, FavouritesListAdmin)

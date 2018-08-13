from django import forms


from .models import FavouritesList


class CreateFavouritesListForm(forms.ModelForm):
    class Meta:
        model = FavouritesList
        exclude = ['user', 'created']


class AddToFavouritesForm(forms.Form):
    favourites_list_pk = forms.ChoiceField(choices=(), label='Favourites')
    quantity = forms.IntegerField(initial=1)
    pk = forms.IntegerField(widget=forms.HiddenInput())
    ctype = forms.CharField(widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        favourites_list_choices = kwargs.pop('favourites_list_choices', None)
        item = kwargs.pop('item', None)
        assert favourites_list_choices is not None, \
            'AddToFavouritesForm must be passed a list of FavouritesList ids ' \
            'via the "favourites_list_choices" keyword argument.'
        assert item, \
            'AddToFavouritesForm must be passed an item via the "item" ' \
            'keyword argument.'
        initial = kwargs.pop('initial', {})
        initial.update(pk=item.pk)
        initial.update(ctype=item.ctype)
        kwargs.update(initial=initial)
        super(AddToFavouritesForm, self).__init__(*args, **kwargs)
        self.fields['favourites_list_pk'].choices = favourites_list_choices

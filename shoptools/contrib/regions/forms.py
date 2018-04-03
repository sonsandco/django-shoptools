from django import forms


class RegionSelectionForm(forms.Form):
    region_id = forms.ChoiceField(choices=(), label='Region')

    def __init__(self, *args, **kwargs):
        region_choices = kwargs.pop('region_choices')
        super(RegionSelectionForm, self).__init__(*args, **kwargs)
        self.fields['region_id'].choices = region_choices

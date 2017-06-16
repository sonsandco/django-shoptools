# -*- coding: utf-8 -*-
from .models import Country, Region, ShippingOption
from .api import validate_options, calculate_shipping_cost


class Shipping(dict):
    '''
        A dict which records available and selected shipping settings.
        {
            valid_regions: [(1, 'New Zealand'), (3, 'Australia'), (4, 'Asia')],
            invalid_regions: [],
            region_messages: [],
            region: 1,
            country: NZ,
            valid_options: [(1, 'Standard Shipping'), (2, 'Express Shipping')],
            invalid_options: [(3, 'Free Shipping')],
            option_messages: [],
            option: 1,
            cost: 10.0,
            currency: 'NZD'
        }

        Messages is intended for use when there are no valid_regions and / or
        no valid_options.

        Provides functions to verify that selected settings are valid, and
        falls back to default settings if they are not.
    '''

    def __init__(self, **kwargs):
        self.valid_regions = []
        self.invalid_regions = []
        self.region_messages = []
        self.region = None
        self.country = None
        self.valid_options = []
        self.invalid_options = []
        self.option_messages = []
        self.option = None
        self.cost = None
        self.currency = None
        self.wine_lines = []
        self.product_lines = []
        self.giftcard_lines = []
        return super(Shipping, self).__init__(**kwargs)

    def save_to(self, obj):
        '''
            Saves shipping details to obj, after checking those details are
            valid for obj. Returns a dict of the validated options.

            Since all sites will be getting shipping details far more than they
            are changing them, we do all the heavy lifting here, validating
            the selected options against obj, so that all requests to get
            shipping details can simply grab values out of the dict.
        '''
        country = self.get_country(obj)
        valid_regions, invalid_regions, region_messages = self.get_regions(obj)
        region = self.get_region(obj)
        valid_options, invalid_options, option_messages = self.get_options(obj)
        option = self.get_option(obj)
        cost = self.get_cost(obj)
        currency = self.get_currency(obj)

        validated_options = {
            'valid_regions': [(r.id, r.name, r.currency)
                              for r in valid_regions],
            'invalid_regions': [(r.id, r.name, r.currency)
                                for r in invalid_regions],
            'region_messages': region_messages,
            'region': region.id if region else None,
            'country': country.code if country else None,
            'valid_options': [(o.id, o.title.name, o.region.currency)
                              for o in valid_options],
            'invalid_options': [(o.id, o.title.name, o.region.currency)
                                for o in invalid_options],
            'option_messages': option_messages,
            'option': option.id if option else None,
            'cost': float(cost) if (cost or cost == 0) else None,
            'currency': currency
        }

        obj.set_shipping_options(validated_options)
        return validated_options

    def get_country(self, obj):
        if self.country:
            return self.country

        try:
            self.country = Country.objects.get(code=self.get('country'))
            return self.country
        except Country.DoesNotExist:
            pass

        self.region = Region.get_default()
        if self.region:
            self.country = self.region.get_default_country()

        return self.country

    def get_regions(self, obj):
        '''
            Returns a tuple of (valid_regions, invalid_regions, messages).

            Messages is intended for use when there are no valid_regions.
        '''
        # TODO: Realistically are we ever going to have invalid regions?
        if not (self.valid_regions and self.invalid_regions
                and self.region_messages):
            self.valid_regions, self.invalid_regions, \
                self.region_messages = (Region.objects.all(), [], [])
        return (self.valid_regions, self.invalid_regions, self.region_messages)

    def get_region(self, obj):
        '''
            Returns the selected region, after validating that it is one of the
            valid regions. If it isn't, falls back to the first valid region.
        '''
        if self.region:
            return self.region

        if not self.valid_regions:
            self.valid_regions = self.get_regions(obj)[0]

        if not self.country:
            self.country = self.get_country(obj)

        if self.country:
            self.region = self.country.region

            if self.region not in self.valid_regions:
                self.region = self.valid_regions.first()

        return self.region

    def get_options(self, obj):
        '''
            Returns a tuple of (valid_options, invalid_options, messages).

            Messages is intended for use when there are no valid_options.
        '''
        if self.valid_options or self.invalid_options or self.option_messages:
            return (self.valid_options, self.invalid_options,
                    self.option_messages)

        if not self.region:
            self.region = self.get_region(obj)

        options = ShippingOption.objects.filter(region=self.region)
        self.valid_options, self.invalid_options, self.option_messages = \
            validate_options(options, obj)

        return (self.valid_options, self.invalid_options, self.option_messages)

    def get_option(self, obj):
        '''
            Returns the selected region, after validating that it is one of the
            valid options. If it isn't, falls back to the first valid option.
        '''
        if not self.valid_options:
            self.valid_options = self.get_options(obj)[0]

        try:
            option = ShippingOption.objects.get(pk=self.get('option'))
            if option in self.valid_options:
                self.option = option
                return option
        except ShippingOption.DoesNotExist:
            pass

        self.option = self.valid_options.first()
        return self.option

    def get_cost(self, obj):
        '''
            Returns the shipping cost for the selected option, as a float.
        '''
        if self.cost or self.cost == 0:
            return self.cost

        if not self.option:
            self.option = self.get_option(obj)

        if not self.region:
            self.region = self.get_region(obj)

        self.cost = calculate_shipping_cost(self.region, self.option, obj)
        return self.cost

    def get_currency(self, obj):
        '''
            Returns the currency of the selected option.
        '''

        if not self.region:
            self.region = self.get_region(obj)

        if self.region:
            self.currency = self.region.currency
        return self.currency

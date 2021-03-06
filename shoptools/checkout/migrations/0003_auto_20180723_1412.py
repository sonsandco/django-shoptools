# Generated by Django 2.0.7 on 2018-07-23 14:12

from django.db import migrations, models
import django.db.models.deletion
import django_countries.fields


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('checkout', '0002_auto_20170720_1329'),
    ]

    operations = [
        migrations.CreateModel(
            name='Address',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('address', models.CharField(max_length=1023, verbose_name='Address')),
                ('city', models.CharField(max_length=255, verbose_name='Town / City')),
                ('postcode', models.CharField(max_length=100, verbose_name='Postcode')),
                ('state', models.CharField(blank=True, default='', max_length=255, verbose_name='State')),
                ('country', django_countries.fields.CountryField(max_length=2, verbose_name='Country')),
                ('phone', models.CharField(blank=True, default='', max_length=50, verbose_name='Phone')),
                ('address_type', models.CharField(choices=[('shipping', 'Shipping'), ('billing', 'Billing')], default='shipping', max_length=20)),
                ('name', models.CharField(default='', max_length=1023)),
                ('email', models.EmailField(blank=True, default='', max_length=254)),
            ],
            options={
                'verbose_name_plural': 'addresses',
            },
        ),
        migrations.RemoveField(
            model_name='giftrecipient',
            name='order',
        ),
        migrations.RemoveField(
            model_name='order',
            name='address',
        ),
        migrations.RemoveField(
            model_name='order',
            name='city',
        ),
        migrations.RemoveField(
            model_name='order',
            name='country',
        ),
        migrations.RemoveField(
            model_name='order',
            name='currency',
        ),
        migrations.RemoveField(
            model_name='order',
            name='email',
        ),
        migrations.RemoveField(
            model_name='order',
            name='name',
        ),
        migrations.RemoveField(
            model_name='order',
            name='phone',
        ),
        migrations.RemoveField(
            model_name='order',
            name='postcode',
        ),
        migrations.RemoveField(
            model_name='order',
            name='state',
        ),
        migrations.AddField(
            model_name='order',
            name='currency_code',
            field=models.CharField(default='NZD', editable=False, max_length=4),
        ),
        migrations.AddField(
            model_name='order',
            name='currency_symbol',
            field=models.CharField(default='$', editable=False, max_length=1),
        ),
        migrations.AddField(
            model_name='order',
            name='gift_message',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='order',
            name='success_page_viewed',
            field=models.BooleanField(default=False, editable=False),
        ),
        migrations.AddField(
            model_name='orderline',
            name='_options',
            field=models.TextField(blank=True, db_column='options', default=''),
        ),
        migrations.AlterField(
            model_name='order',
            name='_shipping_option',
            field=models.PositiveSmallIntegerField(blank=True, db_column='shipping_option', editable=False, null=True, verbose_name='shipping option'),
        ),
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.PositiveSmallIntegerField(choices=[(1, 'New'), (2, 'Payment Failed'), (3, 'Paid'), (4, 'Shipped')], default=1),
        ),
        migrations.AlterUniqueTogether(
            name='orderline',
            unique_together={('item_content_type', 'item_object_id', 'parent_object', '_options')},
        ),
        migrations.DeleteModel(
            name='GiftRecipient',
        ),
        migrations.AddField(
            model_name='address',
            name='order',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='addresses', to='checkout.Order'),
        ),
        migrations.AlterUniqueTogether(
            name='address',
            unique_together={('order', 'address_type')},
        ),
    ]

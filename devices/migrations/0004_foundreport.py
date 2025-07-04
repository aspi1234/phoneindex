# Generated by Django 5.2 on 2025-05-21 21:03

import devices.models
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('devices', '0003_theftreport_region_of_theft_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='FoundReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('case_id_provided', models.CharField(blank=True, help_text="If you found a Case ID on the device's lock screen or were given one.", max_length=30, null=True, verbose_name='Case ID (if known)')),
                ('imei_provided', models.CharField(blank=True, help_text='The 15-digit IMEI, if you can find it (*#06# or on device).', max_length=15, null=True, validators=[devices.models.validate_imei], verbose_name='IMEI (if known)')),
                ('device_description_provided', models.TextField(blank=True, help_text='e.g., Black iPhone, Samsung with blue case, small crack on screen.', null=True, verbose_name='Device Description (if Case ID/IMEI unknown)')),
                ('date_found', models.DateTimeField(verbose_name='Date and Time Found')),
                ('location_found', models.TextField(verbose_name='Location Where Found')),
                ('device_condition', models.CharField(choices=[('PERFECT', 'Perfect condition, like new'), ('GOOD', 'Good condition, minor wear'), ('FAIR', 'Fair condition, visible scratches/dents'), ('POOR', 'Poor condition, screen damaged or other issues'), ('NOT_WORKING', 'Not working / Unable to power on'), ('UNKNOWN', 'Condition unknown')], default='UNKNOWN', max_length=20, verbose_name='Condition of Device')),
                ('return_method_preference', models.CharField(choices=[('POLICE', 'Deliver to a local police station'), ('ANONYMOUS_CHAT', 'Arrange anonymous handover (via this platform)'), ('DIRECT_CONTACT', 'Willing to coordinate directly (share my contact info with owner)'), ('OTHER', 'Other (please specify in message)')], max_length=20, verbose_name='Preferred Return Method')),
                ('finder_message_to_owner', models.TextField(blank=True, null=True, verbose_name='Message to Owner (Optional)')),
                ('finder_name', models.CharField(blank=True, max_length=100, null=True, verbose_name='Your Name (Optional)')),
                ('finder_contact_email', models.EmailField(blank=True, max_length=254, null=True, verbose_name='Your Email (Optional)')),
                ('finder_contact_phone', models.CharField(blank=True, max_length=20, null=True, verbose_name='Your Phone Number (Optional)')),
                ('reported_at', models.DateTimeField(auto_now_add=True, verbose_name='Found Report Submitted At')),
                ('is_processed', models.BooleanField(default=False, help_text='Indicates if this report has been reviewed or matched.', verbose_name='Processed by System/Admin')),
                ('theft_report', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='found_reports', to='devices.theftreport')),
            ],
            options={
                'verbose_name': 'Found Device Report',
                'verbose_name_plural': 'Found Device Reports',
                'ordering': ['-reported_at'],
            },
        ),
    ]

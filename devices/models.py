from django.db import models, IntegrityError
from django.conf import settings # To refer to the CustomUser model
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import re # For basic IMEI validation
from django.utils import timezone # For date operations

# Basic IMEI validator (length and digits only)
def validate_imei_format(value):
    """
    Validates if the IMEI is exactly 15 digits.
    """
    if not re.match(r'^\d{15}$', value):
        raise ValidationError(
            _('%(value)s is not a valid IMEI format. It must be 15 digits.'),
            params={'value': value},
        )

def validate_imei_luhn(value):
    """
    Validates the IMEI using the Luhn algorithm (Mod 10 check).
    Assumes the value is already 15 digits, as checked by validate_imei_format.
    """
    # Convert string to list of integers
    digits = [int(d) for d in value]

    # Drop the last digit (checksum digit)
    checksum_digit = digits.pop()
    
    # Reverse the remaining digits
    reversed_digits = digits[::-1]

    total = 0
    for index, digit in enumerate(reversed_digits):
        if index % 2 == 0: # Double every second digit
            doubled_digit = digit * 2
            if doubled_digit > 9: # If doubled digit is 10 or more, sum its digits
                total += (doubled_digit % 10) + (doubled_digit // 10)
            else:
                total += doubled_digit
        else: # Add other digits as they are
            total += digit

    # Compare the calculated checksum with the actual checksum digit
    if (total + checksum_digit) % 10 != 0:
        raise ValidationError(
            _('The IMEI checksum is invalid. Please check the number.'),
        )

class RegisteredDevice(models.Model):
    STATUS_NORMAL = 'NORMAL'
    STATUS_STOLEN = 'STOLEN'
    STATUS_RECOVERED = 'RECOVERED'
    STATUS_FALSE_ALARM = 'FALSE_ALARM'

    STATUS_CHOICES = [
        (STATUS_NORMAL, _('Normal')),
        (STATUS_STOLEN, _('Reported Stolen')),
        (STATUS_RECOVERED, _('Recovered/Resolved')),
        (STATUS_FALSE_ALARM, _('False Alarm')),
    ]

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='registered_devices'
    )
    imei = models.CharField(
        _('IMEI Number'),
        max_length=15,
        unique=True,
        # Apply both validators: first format, then Luhn
        validators=[validate_imei_format, validate_imei_luhn],
        help_text=_('Enter the 15-digit IMEI number of your device. Dial *#06# to find it.')
    )
    make = models.CharField(_('Make/Brand'), max_length=100, help_text=_('e.g., Samsung, Apple, Google'))
    model_name = models.CharField(_('Model Name'), max_length=100, help_text=_('e.g., Galaxy S23, iPhone 15 Pro'))
    color = models.CharField(_('Color'), max_length=50)
    storage_capacity = models.CharField(
        _('Storage Capacity'), 
        max_length=20, 
        help_text=_('e.g., 128GB, 256GB, 1TB')
    )
    distinguishing_features = models.TextField(
        _('Distinguishing Features'), 
        blank=True, 
        null=True,
        help_text=_('e.g., Carbon fiber case, small scratch on bottom right corner')
    )
    registration_date = models.DateTimeField(_('Registration Date'), auto_now_add=True)
    last_updated = models.DateTimeField(_('Last Updated'), auto_now=True)
    
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_NORMAL
    )

    def __str__(self):
        return f"{self.make} {self.model_name} (IMEI: {self.imei}) - Owner: {self.owner.email}"

    class Meta:
        verbose_name = _('Registered Device')
        verbose_name_plural = _('Registered Devices')
        ordering = ['-registration_date']

# --- NEW THEFT REPORT MODEL ---
class TheftReport(models.Model):
    REPORT_STATUS_ACTIVE = 'ACTIVE'
    REPORT_STATUS_OWNER_RECOVERY = 'OWNER_RECOVERED'
    REPORT_STATUS_FINDER_RETURN = 'FINDER_RETURNED'
    REPORT_STATUS_FALSE_ALARM = 'RESOLVED_FALSE_ALARM'

    REPORT_STATUS_CHOICES = [
        (REPORT_STATUS_ACTIVE, _('Active Report')),
        (REPORT_STATUS_OWNER_RECOVERY, _('Resolved - Recovered by Owner')),
        (REPORT_STATUS_FINDER_RETURN, _('Resolved - Returned by Finder')),
        (REPORT_STATUS_FALSE_ALARM, _('Resolved - False Alarm')),
    ]

    REGION_CHOICES = [
        ('AD', _('Adamaoua')),
        ('CE', _('Center')),
        ('ES', _('East')),
        ('FN', _('Far North')),
        ('LT', _('Littoral')),
        ('NO', _('North')),
        ('NW', _('North-West')),
        ('OU', _('West')),
        ('SU', _('South')),
        ('SW', _('South-West')),
        ('UN', _('Unknown/Other')),
    ]

    device = models.OneToOneField(
        RegisteredDevice,
        on_delete=models.CASCADE,
        related_name='theft_report'
    )
    region_of_theft = models.CharField(
        _('Region of Theft'),
        max_length=2,
        choices=REGION_CHOICES,
        help_text=_('Select the region where the theft occurred.')
    )
    case_id = models.CharField(
        _('Case ID'),
        max_length=30,
        unique=True,
        editable=False
    )
    date_time_of_theft = models.DateTimeField(_('Date and Time of Theft'))
    is_time_approximate = models.BooleanField(_('Is Time Approximate?'), default=True)
    last_known_location = models.CharField(_('Last Known Location'), max_length=255)
    circumstances = models.TextField(_('Circumstances of Theft'))
    additional_details = models.TextField(_('Additional Details'), blank=True, null=True)
    
    reported_at = models.DateTimeField(_('Reported At'), auto_now_add=True)
    last_updated = models.DateTimeField(_('Report Last Updated'), auto_now=True)

    status = models.CharField(
        _('Report Status'),
        max_length=30,
        choices=REPORT_STATUS_CHOICES,
        default='ACTIVE'
    )

    def __str__(self):
        return f"Theft Report {self.case_id} for {self.device.imei}"

    def _generate_case_id(self):
        today = timezone.now().date()
        date_str = today.strftime('%Y%m%d')
        
        if not self.region_of_theft:
            raise ValueError("Region of theft must be set to generate a Case ID.")

        region_code = self.region_of_theft.upper()

        last_report_today_region = TheftReport.objects.filter(
            case_id__startswith=f'CR-{date_str}-{region_code}-'
        ).order_by('case_id').last()

        next_sequence = 1
        if last_report_today_region:
            try:
                last_sequence_str = last_report_today_region.case_id.split('-')[-1]
                next_sequence = int(last_sequence_str) + 1
            except (IndexError, ValueError):
                next_sequence = TheftReport.objects.filter(
                    reported_at__date=today, 
                    region_of_theft=self.region_of_theft
                ).count() + 1
        
        if next_sequence > 9999:
            raise ValidationError("Case ID sequence limit reached for today in this region.")

        sequence_str = f"{next_sequence:04d}"
        return f"CR-{date_str}-{region_code}-{sequence_str}"

    def save(self, *args, **kwargs):
        if not self.pk and not self.case_id: 
            if not self.region_of_theft:
                raise IntegrityError("Cannot save TheftReport: region_of_theft is required to generate a Case ID.")

            while True:
                potential_case_id = self._generate_case_id()
                if not TheftReport.objects.filter(case_id=potential_case_id).exists():
                    self.case_id = potential_case_id
                    break
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _('Theft Report')
        verbose_name_plural = _('Theft Reports')
        ordering = ['-reported_at']
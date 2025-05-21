from django.db import models,IntegrityError
from django.conf import settings # To refer to the CustomUser model
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import re # For basic IMEI validation
from django.utils import timezone # For date operations

# Basic IMEI validator (length and digits only - Luhn algorithm is more complex)
def validate_imei(value):
    if not re.match(r'^\d{15}$', value): # Checks if it's exactly 15 digits
        raise ValidationError(
            _('%(value)s is not a valid IMEI. It must be 15 digits.'),
            params={'value': value},
        )
    # A more advanced validation might include the Luhn algorithm check here.

class RegisteredDevice(models.Model):
    STATUS_NORMAL = 'NORMAL'
    STATUS_STOLEN = 'STOLEN'
    STATUS_RECOVERED = 'RECOVERED' # Or 'RESOLVED' as per user story for case resolution
    STATUS_FALSE_ALARM = 'FALSE_ALARM' # Added from user story context

    STATUS_CHOICES = [
        (STATUS_NORMAL, _('Normal')),
        (STATUS_STOLEN, _('Reported Stolen')),
        (STATUS_RECOVERED, _('Recovered/Resolved')),
        (STATUS_FALSE_ALARM, _('False Alarm')),
    ]

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, # Refers to your CustomUser model
        on_delete=models.CASCADE, # If user is deleted, their devices are also deleted
        related_name='registered_devices' # Allows access like user.registered_devices.all()
    )
    imei = models.CharField(
        _('IMEI Number'),
        max_length=15,
        unique=True, # IMEI must be unique across all devices
        validators=[validate_imei],
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
        null=True, # Allow it to be empty in the database
        help_text=_('e.g., Carbon fiber case, small scratch on bottom right corner')
    )
    registration_date = models.DateTimeField(_('Registration Date'), auto_now_add=True)
    last_updated = models.DateTimeField(_('Last Updated'), auto_now=True) # To track when status or details change
    
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
        ordering = ['-registration_date'] # Default ordering for queries

# --- NEW THEFT REPORT MODEL ---
class TheftReport(models.Model):
    REPORT_STATUS_ACTIVE = 'ACTIVE'
    REPORT_STATUS_OWNER_RECOVERY = 'OWNER_RECOVERED' # Device recovered by owner directly
    REPORT_STATUS_FINDER_RETURN = 'FINDER_RETURNED' # Device returned via finder process
    REPORT_STATUS_FALSE_ALARM = 'RESOLVED_FALSE_ALARM' # Report was a false alarm

    REPORT_STATUS_CHOICES = [
        (REPORT_STATUS_ACTIVE, _('Active Report')),
        (REPORT_STATUS_OWNER_RECOVERY, _('Resolved - Recovered by Owner')),
        (REPORT_STATUS_FINDER_RETURN, _('Resolved - Returned by Finder')),
        (REPORT_STATUS_FALSE_ALARM, _('Resolved - False Alarm')),
    ]

    # Link to the device that was stolen.
    # OneToOneField ensures a device can only have one *active* theft report.
    # If a device is stolen multiple times, you might need a ForeignKey and an 'is_active_report' flag,
    # or a different way to handle historical reports. For now, OneToOne for simplicity.
    # --- UPDATED REGION_CHOICES ---
    REGION_CHOICES = [
        ('AD', _('Adamaoua')),
        ('CE', _('Center')),        # Corrected from your 'Center' to 'Centre' for common French spelling, adjust if 'Center' is preferred.
        ('ES', _('East')),          # Est in French
        ('FN', _('Far North')),     # Extrême-Nord in French
        ('LT', _('Littoral')),
        ('NO', _('North')),         # Nord in French
        ('NW', _('North-West')),    # Nord-Ouest in French
        ('OU', _('West')),          # Ouest in French (OU is a good short code)
        ('SU', _('South')),         # Sud in French
        ('SW', _('South-West')),    # Sud-Ouest in French
        ('UN', _('Unknown/Other')), # Kept the 'Unknown' option, can be removed if not needed
    ]
    # --- END OF UPDATED REGION_CHOICES ---

    device = models.OneToOneField(
        RegisteredDevice,
        on_delete=models.CASCADE,
        related_name='theft_report'
    )
    # Add the new region_of_theft field
    region_of_theft = models.CharField(
        _('Region of Theft'),
        max_length=2, # Max length of your region codes (e.g., 'UNK', 'AD', 'NW')
        choices=REGION_CHOICES,
        # Decide if this field is mandatory. If so, remove blank=True, null=True.
        # For Case ID generation, it will be treated as required.
        # blank=False, null=False, # Making it required by default
        help_text=_('Select the region where the theft occurred.')
    )
    case_id = models.CharField(
        _('Case ID'),
        max_length=30, # e.g., CR-20231027-YDE-0001 (CR-YYYYMMDD-XXX-SSSS) -> 2 + 1 + 8 + 1 + 3 + 1 + 4 = 20. Let's use 25 for safety.
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
        choices=REPORT_STATUS_CHOICES, # Make sure REPORT_STATUS_CHOICES is defined
        default='ACTIVE' # Assuming REPORT_STATUS_ACTIVE is defined
    )

    def __str__(self):
        return f"Theft Report {self.case_id} for {self.device.imei}"

    def _generate_case_id(self):
        today = timezone.now().date()
        date_str = today.strftime('%Y%m%d')
        
        # Ensure region_of_theft is set. This should be guaranteed if the form requires it.
        if not self.region_of_theft:
            # This case should ideally not happen if the form enforces region selection.
            # Handle it gracefully, perhaps by defaulting to 'UNK' or raising an error earlier.
            # For now, let's assume it will be set. If it can be optional, the logic needs adjustment.
            raise ValueError("Region of theft must be set to generate a Case ID.")

        region_code = self.region_of_theft.upper() # Ensure region code is uppercase for consistency

        # Find the latest report for today AND this region to determine the next sequence number
        last_report_today_region = TheftReport.objects.filter(
            case_id__startswith=f'CR-{date_str}-{region_code}-'
        ).order_by('case_id').last()

        next_sequence = 1
        if last_report_today_region:
            try:
                last_sequence_str = last_report_today_region.case_id.split('-')[-1]
                next_sequence = int(last_sequence_str) + 1
            except (IndexError, ValueError):
                # Fallback: count reports for the day and region
                # This is less ideal as it doesn't guarantee a strict sequence if an ID was deleted or skipped
                next_sequence = TheftReport.objects.filter(
                    reported_at__date=today, 
                    region_of_theft=self.region_of_theft
                ).count() + 1
        
        if next_sequence > 9999:
            # Consider a more robust error or logging
            raise ValidationError("Case ID sequence limit reached for today in this region.")

        sequence_str = f"{next_sequence:04d}"
        return f"CR-{date_str}-{region_code}-{sequence_str}"

    def save(self, *args, **kwargs):
        if not self.pk and not self.case_id: 
            # The form should have populated region_of_theft by now
            if not self.region_of_theft:
                # This state should be prevented by form validation making region_of_theft required
                raise IntegrityError("Cannot save TheftReport: region_of_theft is required to generate a Case ID.")

            while True:
                potential_case_id = self._generate_case_id()
                if not TheftReport.objects.filter(case_id=potential_case_id).exists():
                    self.case_id = potential_case_id
                    break
                # If collision, _generate_case_id will try next sequence in its next call within the loop
                # (This implies _generate_case_id's logic for finding next_sequence needs to be robust to repeated calls
                # or the loop needs to increment something itself if _generate_case_id is deterministic given the same state)
                # The current _generate_case_id relies on what's in DB, so re-querying is fine.
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _('Theft Report')
        verbose_name_plural = _('Theft Reports')
        ordering = ['-reported_at']

# Ensure RegisteredDevice model is defined above or imported if in separate file
# Ensure REPORT_STATUS_CHOICES, REPORT_STATUS_ACTIVE are defined within TheftReport or globally.
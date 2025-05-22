from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, DetailView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from .models import RegisteredDevice, TheftReport
from .forms import DeviceRegistrationForm, TheftReportForm, IMEIVerificationForm
from django.db import transaction # For atomic operations
import logging # Import the logging module

# Get an instance of a logger
logger = logging.getLogger(__name__)

class RegisterDeviceView(LoginRequiredMixin, CreateView):
    model = RegisteredDevice
    form_class = DeviceRegistrationForm
    template_name = 'devices/register_device.html'
    success_url = reverse_lazy('devices:user_device_list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        messages.success(self.request, f"Device '{form.instance.make} {form.instance.model_name}' registered successfully!")
        logger.info(f"User {self.request.user.username} registered device: {form.instance.imei}")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Register New Device'
        return context

class UserDeviceListView(LoginRequiredMixin, ListView):
    model = RegisteredDevice
    template_name = 'devices/user_device_list.html'
    context_object_name = 'devices'
    paginate_by = 10

    def get_queryset(self):
        return RegisteredDevice.objects.filter(owner=self.request.user).order_by('-registration_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'My Registered Devices'
        if not context['devices'].exists():
            messages.info(self.request, "You haven't registered any devices yet. Register one now!")
        return context

# --- VIEW FOR REPORTING A DEVICE STOLEN ---
class ReportDeviceStolenView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = TheftReport
    form_class = TheftReportForm
    template_name = 'devices/report_stolen_form.html'

    def get_success_url(self):
        return reverse_lazy('devices:user_device_list')

    def test_func(self):
        # Check if the current user is the owner of the device they are trying to report
        # and if the device is in a 'NORMAL' status.
        device = self.get_device()
        is_owner = device.owner == self.request.user
        is_normal_status = device.status == RegisteredDevice.STATUS_NORMAL
        logger.debug(f"test_func for device {device.imei}: is_owner={is_owner}, is_normal_status={is_normal_status}")
        return is_owner and is_normal_status

    def handle_no_permission(self):
        messages.error(self.request, "You do not have permission to report this device or it's already reported.")
        logger.warning(f"Permission denied for user {self.request.user.username} attempting to report device {self.kwargs.get('device_pk')}.")
        if self.request.user.is_authenticated:
            return redirect(reverse_lazy('devices:user_device_list'))
        return redirect(reverse_lazy('home'))

    def get_device(self):
        device_pk = self.kwargs.get('device_pk')
        return get_object_or_404(RegisteredDevice, pk=device_pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['device'] = self.get_device()
        context['page_title'] = f"Report Stolen: {context['device'].make} {context['device'].model_name}"
        return context

    def form_valid(self, form):
        device_to_report = self.get_device()

        # This check is redundant due to test_func and dispatch, but acts as a final safeguard.
        # It's good for debugging to ensure the flow is as expected.
        if device_to_report.owner != self.request.user or device_to_report.status != RegisteredDevice.STATUS_NORMAL:
            messages.error(self.request, "This device cannot be reported stolen at this time (either you're not the owner or its status isn't 'Normal').")
            logger.warning(f"User {self.request.user.username} tried to report ineligible device {device_to_report.imei}. Owner check: {device_to_report.owner == self.request.user}, Status check: {device_to_report.status == RegisteredDevice.STATUS_NORMAL}")
            return redirect(self.get_success_url())

        try:
            with transaction.atomic():
                # 1. Save the TheftReport instance
                theft_report = form.save(commit=False)
                theft_report.device = device_to_report
                theft_report.save()
                logger.info(f"Theft report created for device {device_to_report.imei}. Case ID: {theft_report.case_id}")
                print(f"DEBUG: Theft report created with ID: {theft_report.case_id}") # For immediate console feedback

                # 2. Update the status of the RegisteredDevice
                print(f"DEBUG: Old device status before update: {device_to_report.status}") # Console debug
                logger.info(f"Attempting to change status for device {device_to_report.imei} from {device_to_report.status} to {RegisteredDevice.STATUS_STOLEN}")
                device_to_report.status = RegisteredDevice.STATUS_STOLEN
                device_to_report.save() # Persist the updated device status
                print(f"DEBUG: New device status after save(): {device_to_report.status}") # Console debug
                logger.info(f"Device {device_to_report.imei} status updated to {device_to_report.status}.")

            messages.success(self.request,
                             f"Device '{device_to_report.make} {device_to_report.model_name}' "
                             f"has been reported stolen. Case ID: {theft_report.case_id}")
            print("DEBUG: All save operations completed successfully. Redirecting...") # Console debug

        except Exception as e:
            # Log the full exception traceback for thorough debugging.
            logger.error(f"CRITICAL ERROR in ReportDeviceStolenView.form_valid for device {device_to_report.imei}: {e}", exc_info=True)
            print(f"CRITICAL ERROR IN FORM_VALID: {e}") # Console debug for immediate visibility
            import traceback
            traceback.print_exc() # Print full traceback to console

            messages.error(self.request, "An unexpected error occurred while reporting the device. Please try again.")
            # Important: return form_invalid(form) here would re-render the form with errors if any.
            # If the error is truly critical (database related), redirecting might be better UX.
            # Given that it's in an 'except' block, it means the save failed.
            return redirect(self.get_success_url())

        return redirect(self.get_success_url())

    def dispatch(self, request, *args, **kwargs):
        # This check prevents accessing the report form if a report already exists for the device.
        device = self.get_device()
        if hasattr(device, 'theft_report') and device.theft_report is not None:
            messages.warning(request, f"Device '{device.make} {device.model_name}' already has an active theft report (Case ID: {device.theft_report.case_id}).")
            logger.info(f"User {request.user.username} tried to access report form for already reported device {device.imei}.")
            return redirect(reverse_lazy('devices:user_device_list'))
        return super().dispatch(request, *args, **kwargs)

# --- VIEW FOR DISPLAYING THEFT REPORT DETAILS ---
class TheftReportDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = TheftReport
    template_name = 'devices/theft_report_detail.html'
    context_object_name = 'theft_report'

    def test_func(self):
        theft_report = self.get_object()
        is_owner = theft_report.device.owner == self.request.user
        is_staff = self.request.user.is_staff
        logger.debug(f"test_func for theft report {theft_report.case_id}: is_owner={is_owner}, is_staff={is_staff}")
        return is_owner or is_staff

    def handle_no_permission(self):
        messages.error(self.request, "You do not have permission to view this theft report.")
        logger.warning(f"Permission denied for user {self.request.user.username} attempting to view theft report {self.kwargs.get('pk')}.")
        if self.request.user.is_authenticated:
            return redirect(reverse_lazy('devices:user_device_list'))
        return redirect(reverse_lazy('home'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['device'] = self.object.device
        context['page_title'] = f"Theft Report Details: Case ID {self.object.case_id}"
        return context

# --- VIEW FOR PHONE VERIFICATION TOOL ---
class VerifyDeviceView(FormView):
    template_name = 'devices/verify_device.html'
    form_class = IMEIVerificationForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Verify Device IMEI'
        return context

    def form_valid(self, form):
        imei_to_check = form.cleaned_data['imei']
        context = self.get_context_data()
        context['submitted_imei'] = imei_to_check

        try:
            device = RegisteredDevice.objects.get(imei=imei_to_check)
            logger.info(f"IMEI {imei_to_check} found. Status: {device.status}")

            if device.status == RegisteredDevice.STATUS_STOLEN:
                context['verification_status'] = 'STOLEN'
                context['device_info'] = {
                    'make': device.make,
                    'model_name': device.model_name,
                    'color': device.color,
                    'storage_capacity': device.storage_capacity,
                }
                if hasattr(device, 'theft_report') and device.theft_report:
                    context['theft_report_info'] = {
                        'case_id': device.theft_report.case_id,
                        'date_reported': device.theft_report.reported_at,
                        'status': device.theft_report.get_status_display(),
                    }
                else:
                    context['theft_report_info'] = {
                        'status': 'Details Unavailable (Report missing)'
                    }

            elif device.status in [RegisteredDevice.STATUS_NORMAL,
                                   RegisteredDevice.STATUS_RECOVERED,
                                   RegisteredDevice.STATUS_FALSE_ALARM]:
                context['verification_status'] = 'CLEAN'
                context['message'] = "This device is registered in our system and is NOT currently reported as stolen."

            else:
                context['verification_status'] = 'CLEAN' # Defaulting unknown statuses to clean for public verification
                context['message'] = f"This device is registered with status: {device.get_status_display()}."


        except RegisteredDevice.DoesNotExist:
            context['verification_status'] = 'NOT_IN_OUR_REGISTRY'
            context['message'] = "This IMEI was not found in our device registry. This means it is not reported as stolen through our system."
            logger.info(f"IMEI {imei_to_check} not found in registry.")

        return self.render_to_response(context)

    def form_invalid(self, form):
        context = self.get_context_data()
        context['page_title'] = 'Verify Device IMEI'
        messages.error(self.request, "Invalid IMEI format. Please check the number and try again.")
        logger.warning(f"Invalid IMEI format submitted: {form.cleaned_data.get('imei', 'N/A')}")
        return self.render_to_response(context)
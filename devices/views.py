from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy,reverse
from django.views.generic import CreateView, ListView,DetailView,FormView,DeleteView 
from django.contrib.auth.mixins import LoginRequiredMixin,UserPassesTestMixin  # To protect views
from django.contrib import messages
from .models import RegisteredDevice,TheftReport
from .forms import DeviceRegistrationForm,TheftReportForm,IMEIVerificationForm,FoundReport,FoundDeviceForm 
from django.db import transaction # For atomic operations
from django.core.mail import send_mail # For sending email notifications
from django.conf import settings # To get DEFAULT_FROM_EMAIL
from django.template.loader import render_to_string # For email templates


class RegisterDeviceView(LoginRequiredMixin, CreateView):
    model = RegisteredDevice
    form_class = DeviceRegistrationForm
    template_name = 'devices/register_device.html' # We'll create this template next
    # Redirect to the list of user's devices after successful registration
    success_url = reverse_lazy('devices:user_device_list') # Assuming 'devices' namespace and 'user_device_list' URL name

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        # Set the owner of the device to the currently logged-in user.
        form.instance.owner = self.request.user
        messages.success(self.request, f"Device '{form.instance.make} {form.instance.model_name}' registered successfully!")
        return super().form_valid(form) # This will save the object and redirect

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Register New Device'
        return context

class UserDeviceListView(LoginRequiredMixin, ListView):
    model = RegisteredDevice
    template_name = 'devices/user_device_list.html' # We'll create this template next
    context_object_name = 'devices' # Name of the variable to use in the template for the list of devices
    paginate_by = 10 # Optional: if you want pagination

    def get_queryset(self):
        # Optimized queryset to fetch related theft_report and its linked found_reports
        # This helps avoid multiple database hits in the template.
        return RegisteredDevice.objects.filter(
            owner=self.request.user
        ).select_related(
            'theft_report' # Selects the one-to-one theft_report
        ).prefetch_related(
            'theft_report__found_reports' # Prefetches all found_reports for each theft_report
        ).order_by('-registration_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'My Registered Devices'
        if not context['devices'].exists():
            messages.info(self.request, "You haven't registered any devices yet. Register one now!")
        return context
    
# --- NEW VIEW FOR REPORTING A DEVICE STOLEN ---
class ReportDeviceStolenView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = TheftReport
    form_class = TheftReportForm
    template_name = 'devices/report_stolen_form.html' # We'll create this template
    # Success URL will redirect back to the user's device list
    
    def get_success_url(self):
        # After reporting, redirect to the list of devices
        return reverse_lazy('devices:user_device_list')

    def test_func(self):
        # Check if the current user is the owner of the device they are trying to report
        device = self.get_device()
        return device.owner == self.request.user and device.status == RegisteredDevice.STATUS_NORMAL

    def handle_no_permission(self):
        messages.error(self.request, "You do not have permission to report this device or it's already reported.")
        # Redirect to device list or home if they don't have permission
        if self.request.user.is_authenticated:
            return redirect(reverse_lazy('devices:user_device_list'))
        return redirect(reverse_lazy('home'))


    def get_device(self):
        # Helper method to get the RegisteredDevice instance
        device_pk = self.kwargs.get('device_pk')
        return get_object_or_404(RegisteredDevice, pk=device_pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['device'] = self.get_device()
        context['page_title'] = f"Report Stolen: {context['device'].make} {context['device'].model_name}"
        return context

    def form_valid(self, form):
        device_to_report = self.get_device()

        # Check again if user is owner and device is 'NORMAL' before proceeding
        if device_to_report.owner != self.request.user or device_to_report.status != RegisteredDevice.STATUS_NORMAL:
            messages.error(self.request, "This device cannot be reported stolen at this time.")
            return redirect(self.get_success_url()) # Or some other appropriate redirect

        try:
            with transaction.atomic(): # Ensure both operations succeed or fail together
                # 1. Save the TheftReport instance
                # The form's model is TheftReport, so form.instance is a TheftReport object
                theft_report = form.save(commit=False) # Don't save to DB yet
                theft_report.device = device_to_report # Link the report to the specific device
                # case_id will be generated by TheftReport's save() method
                theft_report.save() # Now save the TheftReport, generating case_id

                # 2. Update the status of the RegisteredDevice
                device_to_report.status = RegisteredDevice.STATUS_STOLEN
                device_to_report.save() # Save the updated device status

            messages.success(self.request, 
                             f"Device '{device_to_report.make} {device_to_report.model_name}' "
                             f"has been reported stolen. Case ID: {theft_report.case_id}")
        except Exception as e:
            # Log the exception e
            messages.error(self.request, "An error occurred while reporting the device. Please try again.")
            # Optionally, redirect to an error page or back to the form
            return self.form_invalid(form)
            
        return redirect(self.get_success_url())

    def dispatch(self, request, *args, **kwargs):
        # Additional check before even displaying the form
        # Check if a theft report already exists for this device
        device = self.get_device()
        if hasattr(device, 'theft_report') and device.theft_report is not None:
            messages.warning(request, f"Device '{device.make} {device.model_name}' already has an active theft report (Case ID: {device.theft_report.case_id}).")
            return redirect(reverse_lazy('devices:user_device_list'))
        return super().dispatch(request, *args, **kwargs)

# --- NEW VIEW FOR DISPLAYING THEFT REPORT DETAILS ---
class TheftReportDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = TheftReport
    template_name = 'devices/theft_report_detail.html'
    context_object_name = 'theft_report' # Name to use in the template for the TheftReport instance

    def test_func(self):
        # Check if the current user is the owner of the device associated with this theft report
        # Or if the user is a superuser/staff (admin)
        theft_report = self.get_object() # self.get_object() gets the TheftReport instance
        return theft_report.device.owner == self.request.user or self.request.user.is_staff

    def handle_no_permission(self):
        messages.error(self.request, "You do not have permission to view this theft report.")
        # Redirect to device list or home if they don't have permission
        if self.request.user.is_authenticated:
            return redirect(reverse_lazy('devices:user_device_list'))
        return redirect(reverse_lazy('home'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # The theft_report object is already in context['theft_report']
        # We can also add the associated device directly for convenience in the template
        context['device'] = self.object.device # self.object is the TheftReport instance
        context['page_title'] = f"Theft Report Details: Case ID {self.object.case_id}"
        return context
    # In TheftReportDetailView
    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     context['device'] = self.object.device 
    #     context['page_title'] = f"Theft Report Details: Case ID {self.object.case_id}"
    #     # Optional: Add found reports directly to context for clarity or pre-processing
    #     context['found_reports'] = self.object.found_reports_submitted.all() 
    #     return context

# --- NEW VIEW FOR PHONE VERIFICATION TOOL ---
class VerifyDeviceView(FormView):
    template_name = 'devices/verify_device.html' # We'll create this template next
    form_class = IMEIVerificationForm
    # No success_url needed directly as we re-render the same page with results

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Verify Device IMEI'
        # 'verification_result' will be added in form_valid or form_invalid
        return context

    def form_valid(self, form):
        # This method is called when the submitted form is valid (IMEI format is correct)
        imei_to_check = form.cleaned_data['imei']
        context = self.get_context_data() # Get existing context (includes the form)
        context['submitted_imei'] = imei_to_check # Pass submitted IMEI back to template

        try:
            device = RegisteredDevice.objects.get(imei=imei_to_check)
            
            if device.status == RegisteredDevice.STATUS_STOLEN:
                context['verification_status'] = 'STOLEN'
                context['device_info'] = {
                    'make': device.make,
                    'model_name': device.model_name,
                    'color': device.color,
                    'storage_capacity': device.storage_capacity,
                    # Add other non-PII general description fields if desired
                }
                if hasattr(device, 'theft_report') and device.theft_report:
                    context['theft_report_info'] = {
                        'case_id': device.theft_report.case_id,
                        'date_reported': device.theft_report.reported_at,
                        'status': device.theft_report.get_status_display(), # Human-readable status
                    }
                else:
                    # This case should ideally not happen if a device is STOLEN
                    # but its theft_report was somehow deleted or not created.
                    context['theft_report_info'] = { 
                        'status': 'Details Unavailable' 
                    }

            elif device.status in [RegisteredDevice.STATUS_NORMAL, 
                                   RegisteredDevice.STATUS_RECOVERED, 
                                   RegisteredDevice.STATUS_FALSE_ALARM]:
                context['verification_status'] = 'CLEAN'
                context['message'] = "This device is registered in our system and is NOT currently reported as stolen."
            
            else: # Other statuses, treat as clean for verification purposes for now
                context['verification_status'] = 'CLEAN'
                context['message'] = f"This device is registered with status: {device.get_status_display()}."


        except RegisteredDevice.DoesNotExist:
            context['verification_status'] = 'NOT_IN_OUR_REGISTRY'
            context['message'] = "This IMEI was not found in our device registry. This means it is not reported as stolen through our system."
            # For Sarah, this is effectively "CLEAN" in terms of being reported on our platform.

        # Re-render the same page with the form and the results in the context
        return self.render_to_response(context)

    def form_invalid(self, form):
        # This method is called if the form itself is invalid (e.g., IMEI format wrong)
        # The form with errors will be passed to the template automatically by FormView.
        context = self.get_context_data()
        context['page_title'] = 'Verify Device IMEI - Error' # Update title for error
        messages.error(self.request, "Invalid IMEI format. Please check the number and try again.")
        return self.render_to_response(context)

# --- NEW VIEW FOR SUBMITTING A FOUND DEVICE REPORT (PUBLIC) ---
class ReportFoundDeviceView(CreateView):
    model = FoundReport
    form_class = FoundDeviceForm
    template_name = 'devices/report_found_device.html'
    success_url = reverse_lazy('home') # Redirect to homepage after submission

    def get_initial(self):
        """
        Provides initial data for the form.
        This method is called by FormMixin (used by CreateView) when the form is initialized.
        It handles pre-filling data from URL query parameters on GET requests,
        and persists these pre-fill values using the session for subsequent POST requests
        if the form is invalid and needs to be re-rendered.
        """
        initial = super().get_initial() # Get any initial data from parent classes

        # Attempt to get 'case_id' and 'imei' from URL query parameters (e.g., /?case_id=X&imei=Y)
        case_id_from_get = self.request.GET.get('case_id')
        imei_from_get = self.request.GET.get('imei')
        
        prefilled_description = None # To store any generated description

        # --- Session Management for Pre-filled Data ---
        # On a GET request, we capture the pre-fill values from URL parameters
        # and store them in the session. This is so if a subsequent POST request
        # results in an invalid form (and the page re-renders), we can retrieve
        # these original pre-fill values to correctly re-initialize the form.
        if self.request.method == 'GET':
            # Clear any old pre-fill session data first
            self.request.session.pop('prefill_case_id', None)
            self.request.session.pop('prefill_imei', None)
            self.request.session.pop('prefill_description', None)

            if case_id_from_get:
                initial['case_id_provided'] = case_id_from_get
                self.request.session['prefill_case_id'] = case_id_from_get # Store in session
            if imei_from_get:
                initial['imei_provided'] = imei_from_get
                self.request.session['prefill_imei'] = imei_from_get # Store in session
        
        # On a POST request (meaning the form was submitted), if the form is invalid and
        # needs to be re-rendered, get_initial() is called again. We retrieve
        # the pre-fill values from the session to ensure disabled fields are correctly shown.
        elif self.request.method == 'POST':
            if 'prefill_case_id' in self.request.session:
                initial['case_id_provided'] = self.request.session['prefill_case_id']
            if 'prefill_imei' in self.request.session:
                initial['imei_provided'] = self.request.session['prefill_imei']
            # Also retrieve the pre-filled description if it was stored
            if 'prefill_description' in self.request.session:
                initial['device_description_provided'] = self.request.session['prefill_description']
        # --- End Session Management ---

        # --- Logic to Generate Pre-filled Description ---
        # This runs for both GET (to initially pre-fill) and POST (to re-populate initial for the form)
        current_case_id_for_desc = initial.get('case_id_provided')
        current_imei_for_desc = initial.get('imei_provided')

        if current_case_id_for_desc:
            try:
                theft_report = TheftReport.objects.select_related('device').get(case_id=current_case_id_for_desc)
                device = theft_report.device
                prefilled_description = f"Device linked to Case ID {current_case_id_for_desc}: {device.make} {device.model_name}, {device.color}."
                # If IMEI wasn't passed in URL but we found it via Case ID, add it to initial for the form
                if not current_imei_for_desc and device.imei:
                     initial['imei_provided'] = device.imei
                     # If this is a GET request, also store this newly found IMEI in session
                     if self.request.method == 'GET': 
                         self.request.session['prefill_imei'] = device.imei
            except TheftReport.DoesNotExist:
                prefilled_description = f"No active theft report found for Case ID {current_case_id_for_desc}. Please describe the device you found."
        
        # Check current_imei_for_desc (it might have been populated by the case_id logic above or from GET param)
        if current_imei_for_desc:
            if not prefilled_description: # Only generate description from IMEI if Case ID didn't already do it
                try:
                    device = RegisteredDevice.objects.get(imei=current_imei_for_desc)
                    prefilled_description = f"Device with IMEI {current_imei_for_desc}: {device.make} {device.model_name}, {device.color}."
                    # If device is stolen and has a report, and case_id wasn't initially provided, pre-fill it
                    if device.status == RegisteredDevice.STATUS_STOLEN and \
                       hasattr(device, 'theft_report') and device.theft_report and \
                       not initial.get('case_id_provided'): # Check if case_id is not already set in initial
                        initial['case_id_provided'] = device.theft_report.case_id
                        # If this is a GET request, also store this newly found Case ID in session
                        if self.request.method == 'GET': 
                            self.request.session['prefill_case_id'] = device.theft_report.case_id
                        # Update description to reflect that Case ID was found
                        prefilled_description = f"Device linked to Case ID {device.theft_report.case_id} (IMEI {current_imei_for_desc}): {device.make} {device.model_name}, {device.color}."
                except RegisteredDevice.DoesNotExist:
                    if not prefilled_description: # Only if no description was generated yet
                        prefilled_description = f"Device with IMEI {current_imei_for_desc} not found in our registry. Please describe the device you found."
        
        if prefilled_description:
            initial['device_description_provided'] = prefilled_description
            # If this is a GET request, store the generated description in session as well
            if self.request.method == 'GET':
                 self.request.session['prefill_description'] = prefilled_description
        
        return initial

    def form_valid(self, form):
        """
        This method is called when valid form data has been POSTed.
        """
        # Create FoundReport instance but don't save to DB yet,
        # as we need to link it to a TheftReport or RegisteredDevice if matched.
        found_report = form.save(commit=False)
        
        # The form's clean() method has already handled retrieving values for
        # case_id_provided, imei_provided, and device_description_provided from self.initial
        # if those fields were disabled, and put them into cleaned_data.
        case_id_from_form = form.cleaned_data.get('case_id_provided')
        imei_from_form = form.cleaned_data.get('imei_provided')
        
        matched_theft_report = None
        matched_device = None

        # Attempt to match with an existing TheftReport using the provided Case ID
        if case_id_from_form:
            try:
                # select_related is used to optimize DB query by fetching related objects in one go
                matched_theft_report = TheftReport.objects.select_related('device__owner').get(case_id=case_id_from_form)
                matched_device = matched_theft_report.device
            except TheftReport.DoesNotExist:
                pass # No report found for this Case ID, will proceed to check IMEI if provided
        
        # If no match by Case ID, or if Case ID wasn't provided, try by IMEI
        if not matched_theft_report and imei_from_form:
            try:
                device_by_imei = RegisteredDevice.objects.select_related('owner').get(imei=imei_from_form)
                matched_device = device_by_imei # We found a device
                # Check if this device has an active theft report associated with it
                if hasattr(device_by_imei, 'theft_report') and device_by_imei.theft_report:
                    matched_theft_report = device_by_imei.theft_report
            except RegisteredDevice.DoesNotExist:
                pass # No device found for this IMEI

        # Link the FoundReport to the matched TheftReport and/or RegisteredDevice
        if matched_theft_report:
            found_report.theft_report = matched_theft_report
        if matched_device:
            found_report.matched_device = matched_device # Store direct link to the device
        
        # Mark as processed if we found a device match in our system
        found_report.is_processed = bool(matched_device) 
        found_report.save() # Now save the FoundReport with any established links

        # --- Send notification to owner if a match was successful ---
        if matched_device and matched_device.owner:
            owner = matched_device.owner
            email_context = {
                'owner_name': owner.first_name or owner.email.split('@')[0],
                'device_make_model': f"{matched_device.make} {matched_device.model_name}",
                'case_id': matched_theft_report.case_id if matched_theft_report else "N/A (Check device details)",
                'date_found': found_report.date_found,
                'location_found': found_report.location_found,
                'device_condition': found_report.get_device_condition_display(), # Uses model's get_FOO_display
                'return_method_preference': found_report.get_return_method_preference_display(),
                'finder_message': found_report.finder_message_to_owner or "No message provided by finder.",
                'action_url': self.request.build_absolute_uri(
                    reverse('devices:user_device_list') # Direct owner to their list of devices
                ),
            }
            
            subject = f"Good News! Your device '{email_context['device_make_model']}' may have been found - Case {email_context['case_id']}"
            html_message = render_to_string('devices/emails/owner_found_device_notification.html', email_context)
            plain_message = render_to_string('devices/emails/owner_found_device_notification.txt', email_context)

            try:
                send_mail(
                    subject,
                    plain_message,
                    settings.DEFAULT_FROM_EMAIL, # From settings.py
                    [owner.email],
                    html_message=html_message,
                    fail_silently=False # Raise an error if email sending fails
                )
                # TODO (Future): Create an in-app Notification model instance here for the owner
            except Exception as e:
                # Log the email sending failure for admin review
                print(f"CRITICAL: Error sending 'found device' email to {owner.email} for case {found_report.pk}: {e}")
                # Inform the finder that their report is submitted, but also note the notification issue subtly
                messages.warning(self.request, 
                                 "Thank you for your report! It has been submitted. "
                                 "There was an issue sending an immediate notification to the owner, but our team will review.")
                # Don't redirect yet, let the main success message handle it or decide on specific error flow
                # For now, we'll let it fall through to the generic success message and redirect.
                # In a production system, you might want to handle this more gracefully or retry email.

        # Clear session prefill data on successful submission
        self.request.session.pop('prefill_case_id', None)
        self.request.session.pop('prefill_imei', None)
        self.request.session.pop('prefill_description', None)

        messages.success(self.request, 
                         "Thank you for your report! We have recorded the information. "
                         "If a match is found with a reported stolen device and we can notify the owner, we will do so.")
        return redirect(self.success_url)

    def form_invalid(self, form):
        """
        If the form is invalid on POST, re-render it with error messages.
        The `get_initial` method (called by `get_form`) will use session data to ensure
        pre-filled (and disabled) fields retain their values for the re-render.
        """
        # The `form` instance passed here already contains the POST data and errors.
        messages.error(self.request, "There were errors in your submission. Please check the fields highlighted below.")
        # `super().form_invalid(form)` will re-render the template with this form instance.
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        """
        Add extra context data for the template.
        """
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Report a Found Device'
        # If we wanted to show something specific based on GET params even before form submission:
        # context['initial_case_id'] = self.request.GET.get('case_id')
        # context['initial_imei'] = self.request.GET.get('imei')
        return context

# --- NEW VIEW FOR LISTING USER'S THEFT REPORTS ("MY CASES") ---
class UserTheftReportListView(LoginRequiredMixin, ListView):
    model = TheftReport
    template_name = 'devices/user_theft_report_list.html' # New template
    context_object_name = 'theft_reports'
    paginate_by = 10 # Optional: for pagination

    def get_queryset(self):
        # Filter TheftReport objects where the associated device's owner is the current user
        return TheftReport.objects.filter(device__owner=self.request.user).select_related('device').order_by('-reported_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'My Reported Cases'
        if not context['theft_reports'].exists() and not self.request.GET.get('page'): # Avoid message on subsequent pages of pagination
            messages.info(self.request, "You have not reported any devices stolen, or all your reported cases are resolved in a way that removes them from this list (pending logic).")
            # Note: The message above might need refinement based on how "resolved" cases are handled.
            # For now, it lists all theft reports linked to the user.
        return context

# --- NEW VIEW FOR OWNER TO SEE DETAILS OF A SPECIFIC FOUND REPORT ---
class FoundReportOwnerDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = FoundReport # This view is for the FoundReport model
    template_name = 'devices/found_report_owner_detail.html' # New template
    context_object_name = 'found_report' # Name to use in the template for the FoundReport instance

    def test_func(self):
        """
        Ensure the current user is the owner of the device associated with this found report.
        A FoundReport is linked to a TheftReport, which is linked to a RegisteredDevice, which has an owner.
        """
        found_report = self.get_object() # self.get_object() gets the FoundReport instance based on pk from URL
        
        # Check 1: Is the FoundReport linked to a TheftReport?
        if not found_report.theft_report:
            return False # Or handle this case differently if a FoundReport can exist meaningfully without a TheftReport link for the owner
            
        # Check 2: Does the TheftReport link to a device? (Should always be true due to model definition)
        if not found_report.theft_report.device:
            return False

        # Check 3: Is the current user the owner of that device?
        return found_report.theft_report.device.owner == self.request.user

    def handle_no_permission(self):
        """
        Called if test_func returns False.
        """
        messages.error(self.request, "You do not have permission to view these found report details.")
        # Redirect to a safe page, like their list of theft reports or home.
        if self.request.user.is_authenticated:
            return redirect(reverse_lazy('devices:user_theft_report_list')) # Redirect to their cases
        return redirect(reverse_lazy('home')) # Fallback for unusual scenarios

    def get_context_data(self, **kwargs):
        """
        Add additional context to the template.
        """
        context = super().get_context_data(**kwargs)
        found_report = self.object # self.object is the FoundReport instance
        
        context['page_title'] = f"Details for Found Report on Your Device"
        if found_report.theft_report and found_report.theft_report.device:
            context['page_title'] = f"Found Report for: {found_report.theft_report.device.make} {found_report.theft_report.device.model_name}"
        
        # Pass the associated RegisteredDevice and TheftReport for easy access in the template
        if found_report.theft_report:
            context['theft_report_instance'] = found_report.theft_report
            if found_report.theft_report.device:
                context['device_instance'] = found_report.theft_report.device
        
        # TODO (Future): If owner "accepts plan", mark this found_report as acknowledged somehow
        # e.g., found_report.owner_acknowledged = True; found_report.save()
        # This could be done in a separate view or a POST handler on this view.
        
        return context

# --- NEW VIEW FOR DELETING A REGISTERED DEVICE ---
class DeleteDeviceView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = RegisteredDevice
    template_name = 'devices/device_confirm_delete.html' # Confirmation template
    success_url = reverse_lazy('devices:user_device_list') # Redirect after successful deletion
    context_object_name = 'device' # To refer to the device in the confirmation template

    def test_func(self):
        # Ensure the current user is the owner of the device
        device = self.get_object() # self.get_object() gets the RegisteredDevice instance
        return device.owner == self.request.user

    def handle_no_permission(self):
        messages.error(self.request, "You do not have permission to delete this device.")
        return redirect(reverse_lazy('devices:user_device_list'))

    def form_valid(self, form):
        # Called when the POST request to delete is confirmed
        device_name = self.object.make + " " + self.object.model_name
        # The actual deletion is handled by super().form_valid(form)
        # which calls self.object.delete().
        # The on_delete=CASCADE settings in the models should handle deletion of related objects.
        response = super().form_valid(form)
        messages.success(self.request, f"Device '{device_name}' and all its associated reports have been successfully deleted.")
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f"Confirm Delete: {self.object.make} {self.object.model_name}"
        return context
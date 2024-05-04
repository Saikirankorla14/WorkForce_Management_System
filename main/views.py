from sched import scheduler
from django.db.models import Q, Max
from django.forms import model_to_dict
from django.http import HttpResponse, HttpResponseNotFound, JsonResponse
import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from main.services import handle_service_management_request
from main.utils.json_context import get_generic_context_with_extra
from .forms import ClockInOutForm, FeedbackForm, LeaveForm, PaymentForm, PaymentWorkerForm, RegisterForm, LoginForm, CustomUserUpdateForm, FarmForm, PersonForm, RegisterForm, FarmPhotoForm, SchedulerForm, ServiceForm, TaskForm
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.views import LogoutView
from django.urls import reverse_lazy, reverse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.generic.edit import FormView
from .models import Attendance, CustomUser, Farm, Feedback, Payment, Payment_Worker, Paypal_Payment, Person, FarmingDates, FarmingCosts, FarmProduce, Resource, FarmVisitRequest, Message, Reply, FarmVisitReport, Scheduler, Service, Task, Transactions
from .forms import FarmForm,  PersonForm, FarmingDatesForm, FarmingCostsForm,FarmProduceForm, ResourceForm, FarmVisitRequestForm, SearchForm, MessageForm, FarmVisitReportForm
from django.contrib.auth.models import Group
from django.utils import timezone as time_zone
import json
from django.db import IntegrityError
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import logging
logger = logging.getLogger(__name__)
from django.db import transaction
import datetime
from django.views.decorators.http import require_POST
from .models import ProcessedMessage
from django.utils.translation import gettext_lazy as _
import json
import paypalrestsdk
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors, utils
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph
from reportlab.lib.units import inch
from main.decorators import (
    require_ajax, require_staff_or_superuser, require_superuser, require_user_authenticated)
from main.forms import PersonalInformationForm, ServiceForm, StaffAppointmentInformationForm
from main.messages import appt_updated_successfully
from main.models import Appointment, DayOff, Worker, WorkingHours
from main.services import (
    create_new_appointment, create_staff_member_service, email_change_verification_service,
    fetch_user_appointments, handle_entity_management_request, handle_service_management_request,
    prepare_appointment_display_data, prepare_user_profile_data, save_appt_date_time, update_existing_appointment,
    update_personal_info_service)
from main.utils.db_helpers import (
    Service, get_day_off_by_id, get_staff_member_by_user_id, get_user_model,
    get_working_hours_by_id)
from main.utils.error_codes import ErrorCode
from main.utils.json_context import (
    convert_appointment_to_json, get_generic_context, get_generic_context_with_extra,
    json_response)
from main.utils.permissions import check_extensive_permissions, check_permissions, \
    has_permission_to_delete_appointment
from datetime import date, datetime, timedelta
import json
from django.core.mail import send_mail
from django.conf import settings
import pytz
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.forms import SetPasswordForm
from django.db.models import Q
from django.http import HttpResponseRedirect, HttpResponseServerError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.utils.translation import gettext as _
from paypalrestsdk import Payment
import requests
# from paypalrestsdk.exceptions import PayPalRESTException
from main.forms import AppointmentForm, AppointmentRequestForm
from main.logger_config import logger
from main.models import (
    Appointment, AppointmentRequest, AppointmentRescheduleHistory, Config, DayOff, EmailVerificationCode,
    PasswordResetToken, Service,
    Worker
)
from main.utils.db_helpers import (
    can_appointment_be_rescheduled, check_day_off_for_staff, create_and_save_appointment, create_new_user,
    create_payment_info_and_get_url, get_non_working_days_for_staff, get_user_by_email, get_user_model,
    get_website_name, get_weekday_num_from_date, is_working_day, staff_change_allowed_on_reschedule,
    username_in_user_model
)
from main.utils.email_ops import notify_admin_about_appointment, notify_admin_about_reschedule, \
    send_reschedule_confirmation_email, \
    send_thank_you_email
from main.utils.session import get_appointment_data_from_session, handle_existing_email
from main.utils.view_helpers import get_locale, get_timezone_txt
from .decorators import require_ajax
from .messages import passwd_error, passwd_set_successfully
from .services import fetch_user_appointments, get_appointments_and_slots, get_available_slots_for_staff, prepare_appointment_display_data
from .settings import (APPOINTMENT_PAYMENT_URL, APPOINTMENT_THANK_YOU_URL, APP_TIME_ZONE)
from .utils.date_time import convert_str_to_date, convert_str_to_time
from .utils.error_codes import ErrorCode
from .utils.json_context import convert_appointment_to_json, get_generic_context, get_generic_context_with_extra, handle_unauthorized_response, json_response
from django.contrib.auth.decorators import login_required, user_passes_test
CLIENT_MODEL = get_user_model()
paypalrestsdk.configure({
    "mode": "sandbox",  # Change to "live" in production
    "client_id": "AfuJfzHChbHucGFxQkML3GhosCN4xNhZR7wzqF8oWvgw9R6k6YcHOo3J1IsGCzYV1NP6Qig1ccnZQcCE",
    "client_secret": "EF9DrFKJz1m46-I9UOptVCV9HVmjNnyYwnreynjscMx5N9mmDJkaiLvI5J6jVfHDcK-b-k-tPzgKrEr0"
})

def is_farmer_or_field_agent_or_Admin_or_Workers(user):
    return user.groups.filter(name__in=['farmer', 'field_agent','Admin','Workers']).exists()

@user_passes_test(is_farmer_or_field_agent_or_Admin_or_Workers)
def index(request):
    if request.user.is_authenticated:
        # Redirect to appropriate view based on user group
        if 'farmer' in request.user.groups.values_list('name', flat=True):
            return redirect('farmer_home')
        elif 'field_agent' in request.user.groups.values_list('name', flat=True):
            return redirect('farmer_home')
        elif 'Admin' in request.user.groups.values_list('name', flat=True):
            return redirect('admin_view')
        elif 'Workers' in request.user.groups.values_list('name', flat=True):
            return redirect('worker_view')
    else:
        return redirect('login') 
      
@user_passes_test(lambda u: u.groups.filter(name__in=['farmer', 'field_agent']).exists())
@login_required(login_url="/login")
def farmer_home(request):
    user = request.user 
    farms = Farm.objects.filter(user=user)
    is_field_agent = user.groups.filter(name='field_agent').exists()
    farms_in_agent_district = Farm.objects.filter(Q(district=user.district)).order_by('-created')[:5]
    all_farms_in_agent_district = Farm.objects.filter(Q(district=user.district)).order_by('-created')

    farm_exists = Farm.objects.filter(user=user).exists()
    farm_queryset = Farm.objects.filter(user=user)

    latest_user_farms = Farm.objects.filter(user=user).order_by('-created')[:5]

    context = {
        'farm_exists': farm_exists,
        'farm_queryset': farm_queryset,
        'user': user,
        'farms': farms,
        'is_field_agent': is_field_agent,
        'farms_in_agent_district': farms_in_agent_district,
        'latest_user_farms': latest_user_farms,
        'all_farms_in_agent_district': all_farms_in_agent_district
    }
 
    return render(request, 'main/farmer_home.html', context)

@login_required(login_url="/login")
def manager_home(request):
    return render(request, 'main/manager_home.html')

def sign_up(request):
    msg = None
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'User created successfully. Please log in.')
            return redirect ('login')
        else:
            msg = 'form is invalid'
    else:
            form =  form = RegisterForm()
    return render(request, 'registration/custom_signup.html', {'form': form, 'msg': msg})

def login_view(request):
    form = LoginForm(request.POST or None)
    msg = None
    if request.method == 'POST':
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user is not None:
                if user.groups.filter(name='farmer').exists():
                    login(request, user)
                    return redirect('farmer_home')
                elif user.groups.filter(name='field_agent').exists():
                    login(request, user)
                    return redirect('farmer_home')
                elif user.groups.filter(name='manager_staff').exists():
                    login(request, user)
                    return redirect('manager_home')
                elif user.groups.filter(name='Workers').exists():
                    login(request, user)
                    return redirect('worker_view')
                elif user.groups.filter(name='Admin').exists():
                    login(request, user)
                    return redirect('admin_view')
                else:
                    msg = 'Account does not belong to a valid group. Please Check with the Site Admin'
            else:
                msg = 'Invalid username or password. Please try again.'
        else:
            msg = 'Error Validating Form'
    return render(request, 'registration/login.html', {'form': form, 'msg': msg})

@login_required(login_url="/login")
def custom_logout_view(request):
    logout(request)
    return redirect(reverse_lazy('login')) 

@user_passes_test(lambda u: u.groups.filter(name__in=['farmer', 'field_agent']).exists())
@login_required(login_url="/login")
def update_profile(request):
    user = request.user

    if request.method == 'POST':
        user_form = CustomUserUpdateForm(request.POST, request.FILES, instance=user)

        if user_form.is_valid():
            user_form.save()
            messages.success(request, 'Profile Updated Successfully!')
            return redirect('profile')
    else:
        user_form = CustomUserUpdateForm(instance=user)

    return render(request, 'main/update_profile.html', {'user_form': user_form, 'user': user})

@user_passes_test(lambda u: u.groups.filter(name__in=['farmer', 'field_agent']).exists())
@login_required(login_url="/login")
def profile(request):
    return render(request, 'main/profile.html')

@user_passes_test(lambda u: u.groups.filter(name__in=['farmer', 'field_agent']).exists())
@login_required(login_url="/login")
def add_person(request, farm_id):
    farm = get_object_or_404(Farm, id=farm_id)

    if request.method == 'POST':
        form = PersonForm(request.POST, request.FILES)
        if form.is_valid():
            person = form.save(commit=False)
            person.save()

            # Add the person to the appropriate relation based on the context (casual workers or staff)
            if form.cleaned_data.get('casual_labourer'):
                farm.farm_labourers.add(person)
            if form.cleaned_data.get('is_staff'):
                farm.staff_contacts.add(person)

            messages.success(request, 'Person created successfully!')
            return redirect('farm_workers', farm_id=farm_id)
    else:
        form = PersonForm()

    return render(request, 'main/add_person.html', {'form': form, 'farm': farm})

@user_passes_test(lambda u: u.groups.filter(name__in=['farmer', 'field_agent']).exists())
@login_required(login_url="/login")
def edit_person(request, farm_id, person_id):
    farm = get_object_or_404(Farm, id=farm_id)
    person = get_object_or_404(Person, id=person_id)

    if request.method == 'POST':
        form = PersonForm(request.POST, instance=person)
        if form.is_valid():
            form.save()
            messages.success(request, 'Person updated successfully!')
            return redirect('farm_details', farm_id=farm_id)
    else:
        form = PersonForm(instance=person)

    return render(request, 'main/edit_person.html', {'form': form, 'farm': farm, 'person': person})

@user_passes_test(lambda u: u.groups.filter(name__in=['farmer', 'field_agent']).exists())
@login_required(login_url="/login")
def delete_person(request, farm_id, person_id):
    farm = get_object_or_404(Farm, id=farm_id, user=request.user)
    person = get_object_or_404(Person, id=person_id)

    if request.method == 'POST':
        person.delete()
        messages.success(request, 'Farm Worker Deleted Successfully!')
        return JsonResponse({'success': True})

    return JsonResponse({'success': False})

@user_passes_test(lambda u: u.groups.filter(name__in=['farmer']).exists())
@login_required(login_url="/login")
def add_farm(request):
    if request.method == 'POST':
        form = FarmForm(request.POST, user=request.user)
        if form.is_valid():
            # Save the form data to create a new farm
            new_farm = form.save()
            messages.success(request, 'Farm created successfully')
            return redirect('farmer_home')  # Redirect to farm detail view
    else:
        form = FarmForm(user=request.user)

    return render(request, 'main/add_farm.html', {'form': form})

@user_passes_test(lambda u: u.groups.filter(name__in=['Admin']).exists())
@login_required(login_url="/login")
def admin_view(request):
    return render(request, 'main/admin_view.html')

@user_passes_test(lambda u: u.groups.filter(name__in=['Workers']).exists())
@login_required(login_url="/login")
def worker_view(request):
    return render(request, 'main/worker_view.html')

@user_passes_test(lambda u: u.groups.filter(name__in=['farmer']).exists())
@login_required(login_url="/login")
def edit_farm(request, farm_id):
    farm = get_object_or_404(Farm, id=farm_id, user=request.user)

    if request.method == 'POST':
        form = FarmForm(request.POST, request.FILES, instance=farm, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Farm Details updated successfully!')
            return redirect('farm_details', farm_id)
    else:
        form = FarmForm(instance=farm, user=request.user)

    return render(request, 'main/edit_farm.html', {'form': form, 'farm': farm})

@user_passes_test(lambda u: u.groups.filter(name__in=['farmer', 'field_agent']).exists())
@login_required(login_url="/login")
def farm_details(request, farm_id):
    user = request.user
    farm = get_object_or_404(Farm, id=farm_id)
    is_field_agent = user.groups.filter(name='field_agent').exists()
    

    # Process farm visit form submission
    if request.method == 'POST':
        form = FarmVisitRequestForm(request.POST)

        if form.is_valid():
            visit = form.save(commit=False)
            visit.requester = user
            visit.farm = farm
            visit.save()
            messages.success(request, 'Farm visit request submitted successfully!')
            return redirect('farm_details', farm_id=farm_id)
    else:
        form = FarmVisitRequestForm()

    farm_visit_requests = FarmVisitRequest.objects.filter(farm=farm)

    context = {
        'farm': farm,
        'farm_id': farm_id,
        'is_field_agent': is_field_agent,
        'farm_visit_requests': farm_visit_requests,
        'form': form,
    }

    return render(request, 'main/farm_details.html', context)

@user_passes_test(lambda u: u.groups.filter(name__in=['farmer', 'field_agent']).exists())
@login_required(login_url="/login")
def add_farm_dates(request, farm_id):
    farm = get_object_or_404(Farm, id=farm_id)

    if request.method == 'POST':
        form = FarmingDatesForm(request.POST)
        if form.is_valid():
            farming_dates = form.save(commit=False)
            farming_dates.farm = farm
            farming_dates.save()
            messages.success(request, 'Farming Dates Submitted Successfully!')
            return redirect('farm_activities', farm_id)
    else:
        form = FarmingDatesForm()

    return render(request, 'main/add_farm_dates.html', {'farm': farm, 'form': form, 'farm_id': farm_id})

@user_passes_test(lambda u: u.groups.filter(name__in=['farmer', 'field_agent']).exists())
@login_required(login_url="/login")
def update_farm_dates(request, farm_id, farming_dates_id):
    farm = get_object_or_404(Farm, id=farm_id, user=request.user)
    farming_dates = get_object_or_404(FarmingDates, id=farming_dates_id, farm=farm)

    if request.method == 'POST':
        form = FarmingDatesForm(request.POST, instance=farming_dates)
        if form.is_valid():
            form.save()
            messages.success(request, 'Farming Dates Updated Successfully!')
            return redirect('farm_activities', farm_id=farm_id)
    else:
        form = FarmingDatesForm(instance=farming_dates)

    return render(request, 'main/update_farm_dates.html', {'farm': farm, 'form': form, 'farm_id': farm_id, 'farming_dates_id': farming_dates_id})

@user_passes_test(lambda u: u.groups.filter(name__in=['farmer', 'field_agent']).exists())
@login_required(login_url="/login")
def add_farm_costs(request, farm_id):
    farm = get_object_or_404(Farm, id=farm_id)

    if request.method == 'POST':
        form = FarmingCostsForm(request.POST)
        if form.is_valid():
            farming_costs = form.save(commit=False)
            farming_costs.farm = farm
            farming_costs.save()
            messages.success(request, 'Farm Costs Submitted Successfully!')
            return redirect('farm_activities', farm_id=farm_id)
    else:
        form = FarmingCostsForm()

    return render(request, 'main/add_farm_costs.html', {'farm': farm, 'form': form, 'farm_id': farm_id})

@user_passes_test(lambda u: u.groups.filter(name__in=['farmer', 'field_agent']).exists())
@login_required(login_url="/login")
def update_farm_costs(request, farm_id, farming_costs_id):
    farm = get_object_or_404(Farm, id=farm_id, user=request.user)
    farming_costs = get_object_or_404(FarmingCosts, id=farming_costs_id, farm=farm)

    if request.method == 'POST':
        form = FarmingCostsForm(request.POST, instance=farming_costs)
        if form.is_valid():
            form.save()
            messages.success(request, 'Farming Costs Updated Successfully!')
            return redirect('farm_activities', farm_id=farm_id)
    else:
        form = FarmingCostsForm(instance=farming_costs)

    return render(request, 'main/update_farm_costs.html', {'farm': farm, 'form': form, 'farm_id': farm_id, 'farming_costs_id': farming_costs_id})

@user_passes_test(lambda u: u.groups.filter(name__in=['farmer', 'field_agent']).exists())
@login_required(login_url="/login")
def add_farm_produce(request, farm_id):
    farm = get_object_or_404(Farm, id=farm_id)

    if request.method == 'POST':
        form = FarmProduceForm(request.POST)
        if form.is_valid():
            farm_produce = form.save(commit=False)
            farm_produce.farm = farm
            farm_produce.save()
            messages.success(request, 'Farm Produce Submitted Successfully!')
            return redirect('farm_activities', farm_id=farm_id)
    else:
        form = FarmProduceForm()

    return render(request, 'main/add_farm_produce.html', {'farm': farm, 'form': form,'farm_id': farm_id})

@user_passes_test(lambda u: u.groups.filter(name__in=['farmer', 'field_agent']).exists())
@login_required(login_url="/login")
def update_farm_produce(request, farm_id, farm_produce_id):
    farm = get_object_or_404(Farm, id=farm_id, user=request.user)
    farm_produce = get_object_or_404(FarmProduce, id=farm_produce_id, farm=farm)

    if request.method == 'POST':
        form = FarmProduceForm(request.POST, instance=farm_produce)
        if form.is_valid():
            form.save()
            messages.success(request, 'Farming Produce Updated Successfully!')
            return redirect('farm_activities', farm_id=farm_id)
    else:
        form = FarmProduceForm(instance=farm_produce)

    return render(request, 'main/update_farm_produce.html', {'farm': farm, 'form': form, 'farm_id': farm_id, 'farm_produce_id': farm_produce_id})

@user_passes_test(lambda u: u.groups.filter(name__in=['farmer', 'field_agent']).exists())
@login_required(login_url="/login")
def view_more_farm_dates(request, farm_id):
    # Retrieve all farm dates for the given farm
    all_farm_dates = FarmingDates.objects.filter(farm_id=farm_id).order_by('-created')

    # Exclude the first 3 farm dates
    additional_farm_dates = all_farm_dates[3:]

    context = {
        'additional_farm_dates': additional_farm_dates,
        'farm_id': farm_id,
    }

    return render(request, 'main/view_more_farm_dates.html', context)

@user_passes_test(lambda u: u.groups.filter(name__in=['farmer', 'field_agent']).exists())
@login_required(login_url="/login")
def view_more_farm_costs(request, farm_id):
    # Retrieve all farm dates for the given farm
    all_farm_dates = FarmingCosts.objects.filter(farm_id=farm_id).order_by('-created')

    # Exclude the first 3 farm dates
    additional_farm_dates = all_farm_dates[3:]

    context = {
        'additional_farm_costs': additional_farm_dates,
        'farm_id': farm_id,
    }

    return render(request, 'main/view_more_farm_costs.html', context)

@user_passes_test(lambda u: u.groups.filter(name__in=['farmer', 'field_agent']).exists())
@login_required(login_url="/login")
def view_more_farm_produce(request, farm_id):
    # Retrieve all farm dates for the given farm
    all_farm_dates = FarmProduce.objects.filter(farm_id=farm_id)

    # Exclude the first 3 farm dates
    additional_farm_dates = all_farm_dates[3:]

    context = {
        'additional_farm_produce': additional_farm_dates,
        'farm_id': farm_id,
    }

    return render(request, 'main/view_more_farm_produce.html', context)

@user_passes_test(lambda u: u.groups.filter(name__in=['farmer', 'field_agent']).exists())
@login_required(login_url="/login")
def view_more_farm_staff(request, farm_id):
    # Retrieve all farm staff for the given farm
    farm = get_object_or_404(Farm, id=farm_id)
    staff_members = farm.staff_contacts.all()

    user = request.user
    is_field_agent = user.groups.filter(name='field_agent').exists()

    # Exclude the first 2 staff
    additional_farm_staff = staff_members[2:]

    context = {
        'additional_farm_staff': additional_farm_staff,
        'farm_id': farm_id,
        'is_field_agent': is_field_agent
    }

    return render(request, 'main/view_more_farm_staff.html', context)

@user_passes_test(lambda u: u.groups.filter(name__in=['farmer', 'field_agent']).exists())
@login_required(login_url="/login")
def view_more_farm_labourers(request, farm_id):
    # Retrieve all farm staff for the given farm
    farm = get_object_or_404(Farm, id=farm_id)
    farm_labourers = farm.farm_labourers.all()

    user = request.user
    is_field_agent = user.groups.filter(name='field_agent').exists()

    # Exclude the first 2 staff
    additional_farm_labourers = farm_labourers[2:]

    context = {
        'additional_farm_labourers': additional_farm_labourers,
        'farm_id': farm_id,
        'is_field_agent': is_field_agent
    }

    return render(request, 'main/view_more_farm_labourers.html', context)

@user_passes_test(lambda u: u.groups.filter(name__in=['farmer', 'field_agent']).exists())
@login_required(login_url="/login")
def create_resource(request, farm_id):
    farm = get_object_or_404(Farm, id=farm_id)

    if request.method == 'POST':
        form = ResourceForm(request.POST)
        if form.is_valid():
            resource = form.save(commit=False)
            resource.save()
            farm.resources_supplied.add(resource)
            messages.success(request, 'Resource Submitted Successfully!')
            # Redirect to a success page or display a success message
            return redirect('farm_resources', farm_id=farm_id)
    else:
        form = ResourceForm()

    return render(request, 'main/add_resources.html', {'form': form, 'farm_id':farm_id})

@user_passes_test(lambda u: u.groups.filter(name__in=['farmer', 'field_agent']).exists())
def farm_resources(request, farm_id):
    farm = get_object_or_404(Farm, id=farm_id)
    resources = farm.resources_supplied.order_by('-created')

    return render(request, 'main/farm_resources.html', {'farm': farm, 'resources': resources})

@user_passes_test(lambda u: u.groups.filter(name__in=['farmer', 'field_agent']).exists())
@login_required(login_url="/login")
def farm_workers(request, farm_id):
    farm = get_object_or_404(Farm, id=farm_id) # Retrieve all workers for this farm
    user = request.user
    is_field_agent = user.groups.filter(name='field_agent').exists()
    farm_labourer_exist = farm.farm_labourers.exists()
    farm_staff_exist = farm.staff_contacts.exists()
    farm_labourer_queryset = farm.farm_labourers.order_by('-created')
    farm_staff_queryset = farm.staff_contacts.order_by('-created')
    
    context = {
        'farm': farm,
        'farm_id': farm_id,
        'farm_labourer_exist': farm_labourer_exist,
        'farm_staff_exist': farm_staff_exist,
        'farm_labourer_queryset': farm_labourer_queryset,
        'farm_staff_queryset': farm_staff_queryset,
        'is_field_agent': is_field_agent,
    }

    return render(request, 'main/farm_workers.html', context)

@login_required(login_url="/login")
def scheduler(request, farm_id):
    farm = get_object_or_404(Farm, id=farm_id)
    farm_labourer_queryset = farm.farm_labourers.order_by('-created')
    
    if request.method == 'POST':
        
        form = SchedulerForm(request.POST)
        if form.is_valid(): 
            
            # Save the form data to the Scheduler model
            
            worker_name_id = request.POST['worker_name']
            form.save()
            request.session['worker_name_id'] = worker_name_id
            return redirect(reverse('workers_data', kwargs={'farm_id': farm_id, 'worker_name_id': worker_name_id}))
    else:
        form = SchedulerForm(initial={'worker_name': farm_labourer_queryset.first()})

    context = {
        'farm': farm,
        'farm_id': farm_id,
        'form': form,
    }

    return render(request, 'main/scheduler.html', context)

@user_passes_test(lambda u: u.groups.filter(name__in=['farmer', 'field_agent']).exists())
@login_required(login_url="/login")
def workers_data(request, farm_id,worker_name_id):
    farm = get_object_or_404(Farm, id=farm_id) # Retrieve all workers for this farm
    user = request.user
    is_field_agent = user.groups.filter(name='field_agent').exists()
    farm_labourer_exist = farm.farm_labourers.exists()
    farm_staff_exist = farm.staff_contacts.exists()
    farm_labourer_queryset = farm.farm_labourers.order_by('-created')
    farm_staff_queryset = farm.staff_contacts.order_by('-created')
    casual_labourers = Person.objects.filter(casual_labourer=True)
    print(casual_labourers)
    # scheduler = Scheduler.objects.filter(worker_name_id=worker_name_id).first()
    scheduler = Scheduler.objects.filter(worker_name_id=worker_name_id).last()
    print(scheduler)
    # Get the worker name from the scheduler object
    worker_name = scheduler.worker_name
    startdate = scheduler.start_date
    enddate=scheduler.end_date
    task=scheduler.task
    worker_data=[]
    worker_data.append(worker_name)
    
    print("worker_data",worker_data)
    # print(f"worker_name: '{worker_name}'")
    # for person in casual_labourers:
    #     print(f"person.name: '{person.name}'")
    #     if str(person.name).strip().replace(' ', '') == str(worker_name).strip().replace(' ', ''):
    #         print(person)
    #         workers.append(worker_name)
    #         break
    # else:
    #     print("No matching casual labourer found")
    # print("workers",workers)
    # schedule_details=[worker_name,startdate,enddate,task]
    context = {
        'farm': farm,
        'farm_id': farm_id,
        'farm_labourer_exist': farm_labourer_exist,
        'farm_staff_exist': farm_staff_exist,
        'farm_labourer_queryset': farm_labourer_queryset,
        'farm_staff_queryset': farm_staff_queryset,
        'is_field_agent': is_field_agent,
        'worker_data':worker_data,
        'startdate':startdate,
        'enddate':enddate,
        'task':task,
        'workers' : worker_data
        }

    return render(request, 'main/workers_data.html', context)

@user_passes_test(lambda u: u.groups.filter(name__in=['farmer', 'field_agent']).exists())
@login_required(login_url="/login")
def farm_activities(request, farm_id):
    user = request.user
    is_field_agent = user.groups.filter(name='field_agent').exists()
    farm = get_object_or_404(Farm, id=farm_id)
    all_farms_in_agent_district = Farm.objects.filter(Q(district=user.district)).order_by('-created')

    # Check if farming dates, farming costs, and farm produce, workers exist for the farm
    farming_dates_exist = FarmingDates.objects.filter(farm=farm).exists()
    farming_costs_exist = FarmingCosts.objects.filter(farm=farm).exists()
    farm_produce_exist = FarmProduce.objects.filter(farm=farm).exists()
   
    
    farming_dates_queryset = FarmingDates.objects.filter(farm=farm).order_by('-created')
    farming_costs_queryset = FarmingCosts.objects.filter(farm=farm).order_by('-created')
    farm_produce_queryset = FarmProduce.objects.filter(farm=farm).order_by('-created')

    context = {
        'farm': farm,
        'farm_id': farm_id,
        'farming_dates_exist': farming_dates_exist,
        'farming_costs_exist': farming_costs_exist,
        'farm_produce_exist': farm_produce_exist,
        'farming_dates_queryset': farming_dates_queryset,
        'farming_costs_queryset': farming_costs_queryset,
        'farm_produce_queryset': farm_produce_queryset,
        'is_field_agent': is_field_agent,
        'all_farms_in_agent_district': all_farms_in_agent_district
    }

    return render(request, 'main/farm_activities.html', context)

@login_required(login_url="/login")
def farm_photos(request, farm_id):
    farm = get_object_or_404(Farm, id=farm_id)
    media_path = 'media/farm_photos/'
    image_names = [filename for filename in os.listdir(media_path) if os.path.isfile(os.path.join(media_path, filename))]
  
    if request.method == 'POST':
        form = FarmPhotoForm(request.POST, request.FILES)

        if form.is_valid():
            photo = form.save(commit=False)
            photo.farm = farm
            photo.uploaded_by = request.user 
            photo.save()
            messages.success(request, 'Farm photo uploaded successfully!')
            return redirect('farm_photos', farm_id=farm_id)
    else:
        form = FarmPhotoForm()

    context = {
        'farm': farm,
        'farm_id': farm_id,
        'form': form,
        'image_names': image_names,
        'media_path': media_path
    }

    return render(request, 'main/farm_photos.html', context)

def get_image_names(request):
    media_path = 'media/farm_photos/'
    image_names = [filename for filename in os.listdir(media_path) if os.path.isfile(os.path.join(media_path, filename))]
    

    return JsonResponse({'image_names': image_names})

@user_passes_test(lambda u: u.groups.filter(name__in=['farmer', 'field_agent']).exists())
@login_required(login_url="/login")
def view_more_farms(request):
    user = request.user
    is_field_agent = user.groups.filter(name='field_agent').exists()

    # Retrieve all farm dates for the given farm
    all_user_farms = Farm.objects.filter(user=user).order_by('-created')
    all_farms_in_agent_district = Farm.objects.filter(Q(district=user.district)).order_by('-created')

    # Exclude the first 5 farms
    additional_user_farms = all_user_farms[5:]
    additional_agent_farms = all_farms_in_agent_district[5:]

    context = {
        'additional_user_farms': additional_user_farms,
        'additional_agent_farms': additional_agent_farms,
        'is_field_agent': is_field_agent
    }

    return render(request, 'main/view_more_farms.html', context)

@user_passes_test(lambda u: u.groups.filter(name__in=['farmer', 'field_agent']).exists())
@login_required(login_url="/login")
def search_view(request):
    search_form = SearchForm(request.GET)
    results = []
    user = request.user
   
    if search_form.is_valid():
        
        query = search_form.cleaned_data['query']
        
        if user.groups.filter(name='field_agent').exists():
            # If the user is only in the field_agent group, search in farms in their district
            results = Farm.objects.filter(Q(district=user.district), name__icontains=query)
        elif user.groups.filter(name='farmer').exists():
            # If the user is only in the farmer group, search only in their farms
            results = Farm.objects.filter(user=user, name__icontains=query)
        elif user.groups.filter(name__in=['farmer', 'field_agent']).exists():
            # If the user is in both groups, prioritize the field_agent filter
            results = Farm.objects.filter(Q(district=user.district), name__icontains=query)

    return render(request, 'main/farmer_home.html', {'search_form': search_form, 'results': results})

@user_passes_test(lambda u: u.groups.filter(name__in=['field_agent']).exists())
@login_required(login_url="/login")
def delete_farm(request, farm_id):
    farm = get_object_or_404(Farm, id=farm_id)
  
    if request.method == 'POST':
        farm.delete()
        messages.success(request, 'Farm Deleted Successfully!')
        return JsonResponse({'success': True})

    return JsonResponse({'success': False})




@login_required(login_url="/login")
def create_farm_visit_report(request, farm_visit_request_id):
    farm_visit_request = get_object_or_404(FarmVisitRequest, id=farm_visit_request_id)
    existing_report = FarmVisitReport.objects.filter(farm_visit_request=farm_visit_request).first()

    if request.method == 'POST':
        form = FarmVisitReportForm(request.POST, instance=existing_report)
        try:
            if form.is_valid():
                farm_visit_report = form.save(commit=False)
                farm_visit_report.farm_visit_request = farm_visit_request
                farm_visit_report.save()
                messages.success(request, 'Farm Report submitted successfully!')
                
                return redirect('farm_details', farm_id=farm_visit_request.farm.id)
        except IntegrityError:
            # Handle the case where the report already exists
            messages.warning(request, 'Farm Report already submitted!')
            return redirect('farm_details', farm_id=farm_visit_request.farm.id)
    else:
        # If there's an existing report, populate the form with its data
        form = FarmVisitReportForm(instance=existing_report)

    return render(request, 'main/farm_visit_report.html', {'form': form, 'farm_visit_request': farm_visit_request})



# @login_required(login_url="/login")
def get_current_user(request):
    user = {
        'id': request.user.id,
        'username': request.user.username,
        'email': request.user.email,
        'groups': list(request.user.groups.values_list('name', flat=True)),
       
    }
    return JsonResponse({'user': user})



@login_required(login_url="/login")
def training(request):

    return render(request, 'main/training.html') 


def payment_create(request):
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('payment_list')
    else:
        form = PaymentForm()
    return render(request, 'main/payment_create.html', {'form': form})

def payment_update(request, pk):
    payment = Payment.objects.get(pk=pk)
    if request.method == 'POST':
        form = PaymentForm(request.POST, instance=payment)
        if form.is_valid():
            form.save()
            return redirect('payment_list')
    else:
        form = PaymentForm(instance=payment)
    return render(request, 'main/payment_update.html', {'form': form})

def payment_list(request):
    payments = Payment.objects.all()
    return render(request, 'main/payment_list.html', {'payments': payments})

@user_passes_test(lambda u: u.groups.filter(name__in=['farmer', 'field_agent']).exists())
@login_required(login_url="/login")
def dashboard(request):
    return render(request, 'main/dashboard.html')

@user_passes_test(lambda u: u.groups.filter(name__in=['farmer']).exists())
@login_required(login_url="/login")
def leave_feedback(request):
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.user = request.user
            feedback.save()
            return redirect('farmer_home')  # Replace with appropriate redirect
        else:
            print(form.errors)  # Print validation errors
    else:
        form = FeedbackForm()
    return render(request, 'main/feedback.html', {'form': form})

@user_passes_test(lambda u: u.groups.filter(name__in=['Admin']).exists())
@login_required(login_url="/login")
def add_or_update_service(request, service_id=None, view=0):
    if request.method == 'POST':
        service, is_valid, error_message = handle_service_management_request(request.POST, request.FILES, service_id)
        if is_valid:
            messages.success(request, "Service saved successfully!")
            return redirect('appointment:add_service')
        else:
            messages.error(request, error_message)

    extra_context = {
        "btn_text": _("Save"),
        "page_title": _("Add Service"),
    }
    if service_id:
        service = get_object_or_404(Service, pk=service_id)
        form = ServiceForm(instance=service)
        if view != 1:
            extra_context['btn_text'] = _("Update")
            extra_context['page_title'] = _("Update Service")
        else:
            for field in form.fields.values():
                field.disabled = True
            extra_context['btn_text'] = None
            extra_context['page_title'] = _("View Service")
            extra_context['service'] = service
    else:
        form = ServiceForm()
    extra_context['form'] = form
    context = get_generic_context_with_extra(request=request, extra=extra_context)
    return render(request, 'main/manage_service.html', context=context)

@user_passes_test(lambda u: u.groups.filter(name__in=['Admin','farmer']).exists())
@login_required(login_url="/login")
def get_user_appointments(request, response_type='html'):
    appointments = fetch_user_appointments(request.user)
    appointments_json = convert_appointment_to_json(request, appointments)

    if response_type == 'json':
        return json_response("Successfully fetched appointments.", custom_data={'appointments': appointments_json},
                             safe=False)

    # Render the HTML template
    extra_context = {
        'appointments': json.dumps(appointments_json),
    }
    context = get_generic_context_with_extra(request=request, extra=extra_context)
    # if appointment is empty and user doesn't have a staff-member instance, put a message
    if not appointments and not Worker.objects.filter(user=request.user).exists() and request.user.is_staff:
        messages.error(request, _("User doesn't have a staff member instance. Please contact the administrator."))
    return render(request, 'administration/staff_index.html', context)


@user_passes_test(lambda u: u.groups.filter(name__in=['Admin','farmer']).exists())
@login_required(login_url="/login")
def display_appointment(request, appointment_id):
    appointment, page_title, error_message, status_code = prepare_appointment_display_data(request.user, appointment_id)

    if error_message:
        context = get_generic_context(request=request)
        return render(request, 'error_pages/404_not_found.html', context=context, status=status_code)
    # If everything is okay, render the HTML template.
    extra_context = {
        'appointment': appointment,
        'page_title': page_title,
    }
    context = get_generic_context_with_extra(request=request, extra=extra_context)
    return render(request, 'administration/display_appointment.html', context)


@user_passes_test(lambda u: u.groups.filter(name__in=['Admin','farmer']).exists())
@login_required(login_url="/login")
def user_profile(request, staff_user_id=None):
    data = prepare_user_profile_data(request.user, staff_user_id)
    error = data.get('error')
    status_code = data.get('status_code', 400)
    context = get_generic_context_with_extra(request=request, extra=data['extra_context'])
    error_template = 'error_pages/403_forbidden.html' if status_code == 403 else 'error_pages/404_not_found.html'
    template = data['template'] if not error else error_template
    return render(request, template, context)


###############################################################


@user_passes_test(lambda u: u.groups.filter(name__in=['Admin']).exists())
@login_required(login_url="/login")
def add_day_off(request, staff_user_id=None, response_type='html'):
    staff_user_id = staff_user_id or request.user.pk
    if not check_permissions(staff_user_id, request.user):
        message = _("You can only add your own days off")
        return handle_unauthorized_response(request, message, response_type)

    staff_user_id = staff_user_id if staff_user_id else request.user.pk
    staff_member = get_staff_member_by_user_id(user_id=staff_user_id)
    return handle_entity_management_request(request, staff_member, entity_type='day_off')


@user_passes_test(lambda u: u.groups.filter(name__in=['Admin']).exists())
@login_required(login_url="/login")
def update_day_off(request, day_off_id, staff_user_id=None, response_type='html'):
    day_off = get_day_off_by_id(day_off_id)
    if not day_off:
        if response_type == 'json':
            return json_response("Day off does not exist.", status=404, success=False,
                                 error_code=ErrorCode.DAY_OFF_NOT_FOUND)
        else:
            context = get_generic_context(request=request)
            return render(request, 'error_pages/404_not_found.html', context=context, status=404)
    staff_user_id = staff_user_id or request.user.pk
    if not check_extensive_permissions(staff_user_id, request.user, day_off):
        message = _("You can only update your own days off.")
        return handle_unauthorized_response(request, message, response_type)
    staff_member = get_staff_member_by_user_id(user_id=staff_user_id)
    return handle_entity_management_request(request, staff_member, entity_type='day_off', instance=day_off)


@user_passes_test(lambda u: u.groups.filter(name__in=['Admin']).exists())
@login_required(login_url="/login")
def delete_day_off(request, day_off_id, staff_user_id=None):
    day_off = get_object_or_404(DayOff, pk=day_off_id)
    if not check_extensive_permissions(staff_user_id, request.user, day_off):
        message = _("You can only delete your own days off.")
        return handle_unauthorized_response(request, message, 'html')
    day_off.delete()
    if staff_user_id:
        return redirect('user_profile', staff_user_id=staff_user_id)
    return redirect('user_profile')


###############################################################


@user_passes_test(lambda u: u.groups.filter(name__in=['Admin']).exists())
@login_required(login_url="/login")
def add_working_hours(request, staff_user_id=None, response_type='html'):
    staff_user_id = staff_user_id or request.user.pk
    if not check_permissions(staff_user_id, request.user):
        message = _("You can only add your own working hours.")
        return handle_unauthorized_response(request, message, response_type)
    staff_user_id = staff_user_id if staff_user_id else request.user.pk
    staff_member = get_staff_member_by_user_id(user_id=staff_user_id)
    return handle_entity_management_request(request=request, staff_member=staff_member, staff_user_id=staff_user_id,
                                            entity_type='working_hours')


@user_passes_test(lambda u: u.groups.filter(name__in=['Admin']).exists())
@login_required(login_url="/login")
def update_working_hours(request, working_hours_id, staff_user_id=None, response_type='html'):
    working_hours = get_working_hours_by_id(working_hours_id)
    if not working_hours:
        if response_type == 'json':
            return json_response("Working hours does not exist.", status=404, success=False,
                                 error_code=ErrorCode.WORKING_HOURS_NOT_FOUND)
        else:
            context = get_generic_context(request=request)
            return render(request, 'error_pages/404_not_found.html', context=context)

    staff_user_id = staff_user_id or request.user.pk
    if not check_extensive_permissions(staff_user_id, request.user, working_hours):
        message = _("You can only update your own working hours.")
        return handle_unauthorized_response(request, message, response_type)
    staff_member = get_object_or_404(Worker, user_id=staff_user_id or request.user.id)
    return handle_entity_management_request(request=request, staff_member=staff_member, add=False,
                                            instance_id=working_hours_id, staff_user_id=staff_user_id,
                                            entity_type='working_hours', instance=working_hours)


@user_passes_test(lambda u: u.groups.filter(name__in=['Admin']).exists())
@login_required(login_url="/login")
def delete_working_hours(request, working_hours_id, staff_user_id=None):
    working_hours = get_object_or_404(WorkingHours, pk=working_hours_id)
    staff_member = working_hours.staff_member
    if not check_extensive_permissions(staff_user_id, request.user, working_hours):
        message = _("You can only delete your own working hours.")
        return handle_unauthorized_response(request, message, 'html')
    # update weekend hours if necessary
    staff_member.update_upon_working_hours_deletion(working_hours.day_of_week)

    working_hours.delete()

    if staff_user_id:
        return redirect('user_profile', staff_user_id=staff_user_id)
    return redirect('user_profile')


###############################################################


@user_passes_test(lambda u: u.groups.filter(name__in=['Admin']).exists())
@login_required(login_url="/login")
def add_or_update_staff_info(request, user_id=None):
    user = request.user

    # Only allow superusers or the authenticated user to edit his staff info
    if not check_permissions(staff_user_id=user_id, user=user):
        return json_response(_("Not authorized."), status=403, success=False, error_code=ErrorCode.NOT_AUTHORIZED)

    target_user = get_user_model().objects.get(pk=user_id) if user_id else user

    staff_member, created = Worker.objects.get_or_create(user=target_user)

    if request.method == 'POST':
        form = StaffAppointmentInformationForm(request.POST, instance=staff_member)
        if form.is_valid():
            form.save()
            if user_id:
                return redirect('user_profile', staff_user_id=user_id)
            return redirect('user_profile')
    else:
        form = StaffAppointmentInformationForm(instance=staff_member)

    context = get_generic_context_with_extra(request=request, extra={'form': form})
    return render(request, 'administration/manage_staff_member.html', context)


@user_passes_test(lambda u: u.groups.filter(name__in=['Admin']).exists())
@login_required(login_url="/login")
def fetch_service_list_for_staff(request):
    appointment_id = request.GET.get('appointmentId')
    if appointment_id:
        # Fetch services for a specific appointment (edit mode)
        if request.user.is_superuser:
            appointment = Appointment.objects.get(id=appointment_id)
            staff_member = appointment.get_staff_member()
        else:
            staff_member = Worker.objects.get(user=request.user)
            # Ensure the staff member is associated with this appointment
            if not Appointment.objects.filter(id=appointment_id,
                                              appointment_request__staff_member=staff_member).exists():
                return json_response(_("You do not have permission to access this appointment."), status_code=403)
    else:
        # Fetch all services for the staff member (create mode)
        try:
            staff_member = Worker.objects.get(user=request.user)
        except Worker.DoesNotExist:
            return json_response(_("You're not a staff member. Can't perform this action !"), status=400, success=False)

    services = list(staff_member.get_services_offered().values('id', 'name'))
    if len(services) == 0:
        return json_response(_("No services offered by this staff member."), status=404, success=False,
                             error_code=ErrorCode.SERVICE_NOT_FOUND)
    return json_response(_("Successfully fetched services."), custom_data={'services_offered': services})


@user_passes_test(lambda u: u.groups.filter(name__in=['Admin']).exists())
@login_required(login_url="/login")
def update_appt_min_info(request):
    data = json.loads(request.body)
    is_creating = data.get('isCreating', False)

    if is_creating:
        # Logic for creating a new appointment
        return create_new_appointment(data, request)
    else:
        # Logic for updating an existing appointment
        return update_existing_appointment(data, request)


@user_passes_test(lambda u: u.groups.filter(name__in=['Admin']).exists())
@login_required(login_url="/login")
def validate_appointment_date(request):
    data = json.loads(request.body)
    start_time_str = data.get("start_time")
    appt_date_str = data.get("date")
    appointment_id = data.get("appointment_id")

    # Convert the string date and time to Python datetime objects
    start_time_obj = datetime.datetime.fromisoformat(start_time_str)
    appt_date = datetime.datetime.strptime(appt_date_str, "%Y-%m-%d").date()

    # Get the staff member for the appointment
    appt = Appointment.objects.get(id=appointment_id)
    staff_member = appt.appointment_request.staff_member

    # Check if the appointment's date and time are valid
    weekday: str = appt_date.strftime("%A")
    is_valid, message = Appointment.is_valid_date(appt_date, start_time_obj, staff_member, appointment_id, weekday)
    if not is_valid:
        return json_response(message, status=403, success=False, error_code=ErrorCode.INVALID_DATE)
    return json_response(_("Appointment date and time are valid."))


@user_passes_test(lambda u: u.groups.filter(name__in=['Admin']).exists())
@login_required(login_url="/login")
def update_appt_date_time(request):
    data = json.loads(request.body)

    # Extracting the data
    start_time = data.get("start_time")
    appt_date = data.get("date")
    appointment_id = data.get("appointment_id")

    # save the data
    try:
        appt = save_appt_date_time(start_time, appt_date, appointment_id, request)
    except Appointment.DoesNotExist:
        return json_response(_("Appointment does not exist."), status=404, success=False,
                             error_code=ErrorCode.APPOINTMENT_NOT_FOUND)
    except ValidationError as e:
        return json_response(e.message, status=400, success=False)
    return json_response(appt_updated_successfully, custom_data={'appt': appt.id})


@user_passes_test(lambda u: u.groups.filter(name__in=['Admin']).exists())
@login_required(login_url="/login")
def update_personal_info(request, staff_user_id=None):
    # only superuser or the staff member itself can update the personal info
    if not check_permissions(staff_user_id=staff_user_id, user=request.user) or (
            not staff_user_id and not request.user.is_superuser):
        return json_response(_("Not authorized."), status=403, success=False, error_code=ErrorCode.NOT_AUTHORIZED)

    if request.method == 'POST':
        user, is_valid, error_message = update_personal_info_service(staff_user_id, request.POST, request.user)
        if is_valid:
            return redirect('user_profile')
        else:
            messages.error(request, error_message)
            return redirect('update_personal_info')

    if staff_user_id:
        user = get_user_model().objects.get(pk=staff_user_id)
    else:
        user = request.user

    form = PersonalInformationForm(initial={
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email,
    }, user=user)

    context = get_generic_context_with_extra(request=request, extra={'form': form, 'btn_text': _("Update")})
    return render(request, 'administration/manage_staff_personal_info.html', context)


@user_passes_test(lambda u: u.groups.filter(name__in=['Admin','farmer']).exists())
@login_required(login_url="/login")
def email_change_verification_code(request):
    context = get_generic_context(request=request)

    if request.method == 'POST':
        code = request.POST.get('code')
        email = request.session.get('email')
        old_email = request.session.get('old_email')

        is_verified = email_change_verification_service(code, email, old_email)
        if is_verified:
            messages.success(request, _("Email updated successfully!"))
            return redirect('user_profile')
        else:
            messages.error(request, _("The verification code provided is incorrect. Please try again."))
            return render(request, 'administration/email_change_verification_code.html', context=context)

    return render(request, 'administration/email_change_verification_code.html', context=context)


###############################################################


@user_passes_test(lambda u: u.groups.filter(name__in=['Admin']).exists())
@login_required(login_url="/login")
def create_new_staff_member(request):
    if request.method == 'POST':
        user, is_valid, error_message = create_staff_member_service(request.POST)
        if is_valid:
            return redirect('user_profile', staff_user_id=user.pk)
        else:
            messages.error(request, error_message)
            return redirect('add_staff_member_personal_info')

    form = PersonalInformationForm()
    context = get_generic_context_with_extra(request=request, extra={'form': form, 'btn_text': _("Create")})
    return render(request, 'administration/manage_staff_personal_info.html', context=context)


@user_passes_test(lambda u: u.groups.filter(name__in=['Admin']).exists())
@login_required(login_url="/login")
def make_superuser_staff_member(request):
    user = request.user
    # Worker.objects.create(user=user)
    return redirect('user_profile')


@user_passes_test(lambda u: u.groups.filter(name__in=['Admin']).exists())
@login_required(login_url="/login")
def remove_superuser_staff_member(request):
    user = request.user
    Worker.objects.filter(user=user).delete()
    return redirect('user_profile')


###############################################################
# Services

@user_passes_test(lambda u: u.groups.filter(name__in=['Admin']).exists())
@login_required(login_url="/login")
def add_or_update_service(request, service_id=None, view=0):
    if request.method == 'POST':
        service, is_valid, error_message = handle_service_management_request(request.POST, request.FILES, service_id)
        if is_valid:
            messages.success(request, "Service saved successfully!")
            return redirect('add_service')
        else:
            messages.error(request, error_message)

    extra_context = {
        "btn_text": _("Save"),
        "page_title": _("Add Service"),
    }
    if service_id:
        service = get_object_or_404(Service, pk=service_id)
        form = ServiceForm(instance=service)
        if view != 1:
            extra_context['btn_text'] = _("Update")
            extra_context['page_title'] = _("Update Service")
        else:
            for field in form.fields.values():
                field.disabled = True
            extra_context['btn_text'] = None
            extra_context['page_title'] = _("View Service")
            extra_context['service'] = service
    else:
        form = ServiceForm()
    extra_context['form'] = form
    context = get_generic_context_with_extra(request=request, extra=extra_context)
    return render(request, 'administration/manage_service.html', context=context)

@user_passes_test(lambda u: u.groups.filter(name__in=['Admin']).exists())
@login_required(login_url="/login")
def delete_service(request, service_id):
    service = get_object_or_404(Service, pk=service_id)
    service.delete()
    messages.success(request, _("Service deleted successfully!"))
    return redirect('admin_view')


###############################################################
# Remove staff member
@user_passes_test(lambda u: u.groups.filter(name__in=['Admin']).exists())
@login_required(login_url="/login")
def remove_staff_member(request, staff_user_id):
    staff_member = get_object_or_404(Worker, user_id=staff_user_id)
    staff_member.delete()
    user = get_user_model().objects.get(pk=staff_user_id)
    if not user.is_superuser and user.is_staff:
        user.is_staff = False
        user.save()
    messages.success(request, _("Staff member deleted successfully!"))
    return redirect('user_profile')


@user_passes_test(lambda u: u.groups.filter(name__in=['Admin']).exists())
@login_required(login_url="/login")
def get_service_list(request, response_type='html'):
    services = Service.objects.all()
    if response_type == 'json':
        service_data = []
        for service in services:
            service_data.append({
                'id': service.id,
                'name': service.name,
                'description': service.description,
                'duration': service.get_duration(),
                'price': service.get_price_text(),
                'down_payment': service.get_down_payment_text(),
                'image': service.get_image_url(),
                'background_color': service.background_color
            })
        return json_response("Successfully fetched services.", custom_data={'services': service_data}, safe=False)
    context = get_generic_context_with_extra(request=request, extra={'services': services})
    return render(request, 'administration/service_list.html', context=context)


@user_passes_test(lambda u: u.groups.filter(name__in=['Admin']).exists())
@login_required(login_url="/login")
def delete_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, pk=appointment_id)
    if not has_permission_to_delete_appointment(request.user, appointment):
        message = _("You can only delete your own appointments.")
        return handle_unauthorized_response(request, message, 'html')
    appointment.delete()
    messages.success(request, _("Appointment deleted successfully!"))
    return redirect('get_user_appointments')


@user_passes_test(lambda u: u.groups.filter(name__in=['Admin']).exists())
@login_required(login_url="/login")
def delete_appointment_ajax(request):
    data = json.loads(request.body)
    appointment_id = data.get("appointment_id")
    appointment = get_object_or_404(Appointment, pk=appointment_id)
    if not has_permission_to_delete_appointment(request.user, appointment):
        message = _("You can only delete your own appointments.")
        return json_response(message, status=403, success=False, error_code=ErrorCode.NOT_AUTHORIZED)
    appointment.delete()
    return json_response(_("Appointment deleted successfully."))


@user_passes_test(lambda u: u.groups.filter(name__in=['Admin']).exists())
@login_required(login_url="/login")
def is_user_staff_admin(request):
    user = request.user
    try:
        Worker.objects.get(user=user)
        return json_response(_("User is a staff member."), custom_data={'is_staff_admin': True})
    except Worker.DoesNotExist:
        return json_response(_("User is not a staff member."), custom_data={'is_staff_admin': False})

@user_passes_test(lambda u: u.groups.filter(name__in=['Admin','farmer', 'field_agent']).exists())
@require_ajax
def get_available_slots_ajax(request):
    """This view function handles AJAX requests to get available slots for a selected date.

    :param request: The request instance.
    :return: A JSON response containing available slots, selected date, an error flag, and an optional error message.
    """
    selected_date = convert_str_to_date(request.GET.get('selected_date'))
    staff_id = request.GET.get('staff_id')

    if selected_date < date.today():
        custom_data = {'error': True, 'available_slots': [], 'date_chosen': ''}
        message = _('Date is in the past')
        return json_response(message=message, custom_data=custom_data, success=False,
                             error_code=ErrorCode.PAST_DATE)

    date_chosen = selected_date.strftime("%a, %B %d, %Y")
    custom_data = {'date_chosen': date_chosen}

    # If no staff_id provided, return an empty list of slots
    if not staff_id or staff_id == 'none':
        custom_data['available_slots'] = []
        custom_data['error'] = False
        message = _('No staff member selected')
        return json_response(message=message, custom_data=custom_data, success=False,
                             error_code=ErrorCode.STAFF_ID_REQUIRED, status=403)

    sm = get_object_or_404(Worker, pk=staff_id)
    custom_data['staff_member'] = sm.get_staff_member_name()
    days_off_exist = check_day_off_for_staff(staff_member=sm, date=selected_date)
    if days_off_exist:
        message = _("Day off. Please select another date!")
        custom_data['available_slots'] = []
        return json_response(message=message, custom_data=custom_data, success=False, error_code=ErrorCode.INVALID_DATE)
    # if selected_date is not a working day for the staff, return an empty list of slots and 'message' is Day Off
    weekday_num = get_weekday_num_from_date(selected_date)
    is_working_day_ = is_working_day(staff_member=sm, day=weekday_num)
    if not is_working_day_:
        message = _("Not a working day for {staff_member}. Please select another date!").format(
            staff_member=sm.get_staff_member_first_name())
        custom_data['available_slots'] = []
        return json_response(message=message, custom_data=custom_data, success=False, error_code=ErrorCode.INVALID_DATE)
    available_slots = get_available_slots_for_staff(selected_date, sm)

    # Check if the selected_date is today and filter out past slots
    if selected_date == date.today():
        # Get the current time in EDT timezone
        current_time_edt = datetime.now(pytz.timezone(APP_TIME_ZONE)).time()
        available_slots = [slot for slot in available_slots if convert_str_to_time(slot) > current_time_edt]

    custom_data['available_slots'] = available_slots
    if len(available_slots) == 0:
        custom_data['error'] = True
        message = _('No availability')
        return json_response(message=message, custom_data=custom_data, success=False, error_code=ErrorCode.INVALID_DATE)
    custom_data['error'] = False
    return json_response(message='Successfully retrieved available slots', custom_data=custom_data, success=True)


@require_ajax
def get_next_available_date_ajax(request, service_id):
    """This view function handles AJAX requests to get the next available date for a service.

    :param request: The request instance.
    :param service_id: The ID of the service.
    :return: A JSON response containing the next available date.
    """
    staff_id = request.GET.get('staff_id')

    # If staff_id is not provided, you should handle it accordingly.
    if staff_id and staff_id != 'none':
        staff_member = get_object_or_404(Worker, pk=staff_id)
        service = get_object_or_404(Service, pk=service_id)

        # Fetch the days off for the staff
        days_off = DayOff.objects.filter(staff_member=staff_member).filter(
            Q(start_date__lte=date.today(), end_date__gte=date.today()) |
            Q(start_date__gte=date.today())
        )

        current_date = date.today()
        next_available_date = None
        day_offset = 0

        while next_available_date is None:
            potential_date = current_date + timedelta(days=day_offset)

            # Check if the potential date is a day off for the staff
            is_day_off = any([day_off.start_date <= potential_date <= day_off.end_date for day_off in days_off])
            # Check if the potential date is a working day for the staff
            weekday_num = get_weekday_num_from_date(potential_date)
            is_working_day_ = is_working_day(staff_member=staff_member, day=weekday_num)

            if not is_day_off and is_working_day_:
                x, available_slots = get_appointments_and_slots(potential_date, service)
                if available_slots:
                    next_available_date = potential_date

            day_offset += 1
        message = _('Successfully retrieved next available date')
        data = {'next_available_date': next_available_date.isoformat()}
        return json_response(message=message, custom_data=data, success=True)
    else:
        data = {'error': True}
        message = _('No staff member selected')
        return json_response(message=message, custom_data=data, success=False, error_code=ErrorCode.STAFF_ID_REQUIRED)

@user_passes_test(lambda u: u.groups.filter(name__in=['Admin']).exists())
@login_required(login_url="/login")
def get_non_working_days_ajax(request):
    staff_id = request.GET.get('staff_id')
    error = False
    message = _('Successfully retrieved non-working days')

    if not staff_id or staff_id == 'none':
        message = _('No staff member selected')
        error_code = ErrorCode.STAFF_ID_REQUIRED
        error = True
    else:
        non_working_days = get_non_working_days_for_staff(staff_id)
        custom_data = {"non_working_days": non_working_days}
        return json_response(message=message, custom_data=custom_data, success=not error)

    custom_data = {'error': error}
    return json_response(message=message, custom_data=custom_data, success=not error, error_code=error_code)

@user_passes_test(lambda u: u.groups.filter(name__in=['Admin','farmer', 'field_agent']).exists())
@login_required(login_url="/login")
def appointment_request(request, service_id=None, staff_member_id=None):
    """This view function handles requests to book an appointment for a service.

    :param request: The request instance.
    :param service_id: The ID of the service.
    :param staff_member_id: The ID of the staff member.
    :return: The rendered HTML page.
    """

    service = None
    staff_member = None
    all_staff_members = None
    available_slots = []
    config = Config.objects.first()
    label = config.app_offered_by_label if config else _("Offered by")

    if service_id:
        service = get_object_or_404(Service, pk=service_id)
        all_staff_members = Worker.objects.filter(services_offered=service)

        # If only one staff member for a service, choose them by default and fetch their slots.
        if all_staff_members.count() == 1:
            staff_member = all_staff_members.first()
            x, available_slots = get_appointments_and_slots(date.today(), service)

    # If a specific staff member is selected, fetch their slots.
    if staff_member_id:
        staff_member = get_object_or_404(Worker, pk=staff_member_id)
        y, available_slots = get_appointments_and_slots(date.today(), service)

    page_title = f"{service.name} - {get_website_name()}"
    page_description = _("Book an appointment for {s} at {wn}.").format(s=service.name, wn=get_website_name())

    date_chosen = date.today().strftime("%a, %B %d, %Y")
    extra_context = {
        'service': service,
        'staff_member': staff_member,
        'all_staff_members': all_staff_members,
        'page_title': page_title,
        'page_description': page_description,
        'available_slots': available_slots,
        'date_chosen': date_chosen,
        'locale': get_locale(),
        'timezoneTxt': get_timezone_txt(),
        'label': label
    }
    context = get_generic_context_with_extra(request, extra_context, admin=False)
    return render(request, 'appointment/appointments.html', context=context)

@user_passes_test(lambda u: u.groups.filter(name__in=['Admin','farmer']).exists())
@login_required(login_url="/login")
def appointment_request_submit(request):
    """This view function handles the submission of the appointment request form.

    :param request: The request instance.
    :return: The rendered HTML page.
    """
    if request.method == 'POST':
        form = AppointmentRequestForm(request.POST)
        if form.is_valid():
            # Use form.cleaned_data to get the cleaned and validated data
            staff_member = form.cleaned_data['staff_member']

            staff_exists = Worker.objects.filter(id=staff_member.id).exists()
            if not staff_exists:
                messages.error(request, _("Selected staff member does not exist."))
            else:
                logger.info(
                    f"date_f {form.cleaned_data['date']} start_time {form.cleaned_data['start_time']} end_time "
                    f"{form.cleaned_data['end_time']} service {form.cleaned_data['service']} staff {staff_member}")
                ar = form.save()
                request.session[f'appointment_completed_{ar.id_request}'] = False
                # Redirect the user to the account creation page
                return redirect('appointment_client_information', appointment_request_id=ar.id,
                                id_request=ar.id_request)
        else:
            # Handle the case if the form is not valid
            messages.error(request, _('There was an error in your submission. Please check the form and try again.'))
    else:
        form = AppointmentRequestForm()

    context = get_generic_context_with_extra(request, {'form': form}, admin=False)
    return render(request, 'appointment/appointments.html', context=context)

@user_passes_test(lambda u: u.groups.filter(name__in=['Admin','farmer']).exists())
@login_required(login_url="/login")
def redirect_to_payment_or_thank_you_page(appointment):
    """This function redirects to the payment page or the thank-you page based on the configuration.

    :param appointment: The Appointment instance.
    :return: The redirect response.
    """
    if APPOINTMENT_PAYMENT_URL is not None and APPOINTMENT_PAYMENT_URL != '':
        payment_url = create_payment_info_and_get_url(appointment)
        return HttpResponseRedirect(payment_url)
    elif APPOINTMENT_THANK_YOU_URL is not None and APPOINTMENT_THANK_YOU_URL != '':
        thank_you_url = reverse(APPOINTMENT_THANK_YOU_URL, kwargs={'appointment_id': appointment.id})
        return HttpResponseRedirect(thank_you_url)
    else:
        # Redirect to your default thank you page and pass the appointment object ID
        return HttpResponseRedirect(
            reverse('default_thank_you', kwargs={'appointment_id': appointment.id})
        )

@user_passes_test(lambda u: u.groups.filter(name__in=['Admin','farmer']).exists())
@login_required(login_url="/login")
def create_appointment(request, appointment_request_obj, client_data, appointment_data):
    """This function creates a new appointment and redirects to the payment page or the thank-you page.

    :param request: The request instance.
    :param appointment_request_obj: The AppointmentRequest instance.
    :param client_data: The client data.
    :param appointment_data: The appointment data.
    :return: The redirect response.
    """
    appointment = create_and_save_appointment(appointment_request_obj, client_data, appointment_data, request)
    notify_admin_about_appointment(appointment, appointment.client.first_name)
    return redirect_to_payment_or_thank_you_page(appointment)

@user_passes_test(lambda u: u.groups.filter(name__in=['Admin','farmer']).exists())
@login_required(login_url="/login")
def get_client_data_from_post(request):
    """This function retrieves client data from the POST request.

    :param request: The request instance.
    :return: The client data.
    """
    return {
        'name': request.POST.get('name'),
        'email': request.POST.get('email'),
    }

@user_passes_test(lambda u: u.groups.filter(name__in=['Admin','farmer']).exists())
@login_required(login_url="/login")
def get_appointment_data_from_post_request(request):
    """This function retrieves appointment data from the POST request.

    :param request: The request instance.
    :return: The appointment data.
    """
    return {
        'phone': request.POST.get('phone'),
        'want_reminder': request.POST.get('want_reminder') == 'on',
        'address': request.POST.get('address'),
        'additional_info': request.POST.get('additional_info'),
    }

@user_passes_test(lambda u: u.groups.filter(name__in=['Admin','farmer']).exists())
@login_required(login_url="/login")
def appointment_client_information(request, appointment_request_id, id_request):
    """This view function handles client information submission for an appointment.

    :param request: The request instance.
    :param appointment_request_id: The ID of the appointment request.
    :param id_request: The unique ID of the appointment request.
    :return: The rendered HTML page.
    """
    ar = get_object_or_404(AppointmentRequest, pk=appointment_request_id)
    if request.session.get(f'appointment_submitted_{id_request}', False):
        context = get_generic_context_with_extra(request, {'service_id': ar.service_id}, admin=False)
        return render(request, 'error_pages/304_already_submitted.html', context=context)

    if request.method == 'POST':
        appointment_form = AppointmentForm(request.POST)

        if appointment_form.is_valid():
            appointment_data = appointment_form.cleaned_data
            client_data = get_client_data_from_post(request)
            payment_type = request.POST.get('payment_type')
            ar.payment_type = payment_type
            ar.save()

            # Check if email is already in the database
            is_email_in_db = CLIENT_MODEL.objects.filter(email__exact=client_data['email']).exists()
            if is_email_in_db:
                return handle_existing_email(request, client_data, appointment_data, appointment_request_id, id_request)

            logger.info(f"Creating a new user with the given information {client_data}")
            user = create_new_user(client_data)
            messages.success(request, _("An account was created for you."))

            # Create a new appointment
            response = create_appointment(request, ar, client_data, appointment_data)
            request.session.setdefault(f'appointment_submitted_{id_request}', True)
            return response
    else:
        appointment_form = AppointmentForm()

    extra_context = {
        'ar': ar,
        'APPOINTMENT_PAYMENT_URL': APPOINTMENT_PAYMENT_URL,
        'form': appointment_form,
        'service_name': ar.service.name,
    }
    context = get_generic_context_with_extra(request, extra_context, admin=False)
    return render(request, 'appointment/appointment_client_information.html', context=context)

@user_passes_test(lambda u: u.groups.filter(name__in=['Admin','farmer']).exists())
@login_required(login_url="/login")
def verify_user_and_login(request, user, code):
    """This function verifies the user's email and logs the user in.

    :param request: The request instance.
    :param user: The User instance.
    :param code: The verification code.
    """
    if user and EmailVerificationCode.objects.filter(user=user, code=code).exists():
        logger.info(f"Email verified successfully for user {user}")
        login(request, user)
        messages.success(request, _("Email verified successfully."))
        return True
    else:
        messages.error(request, _("Invalid verification code."))
        return False

@user_passes_test(lambda u: u.groups.filter(name__in=['Admin','farmer']).exists())
@login_required(login_url="/login")
def enter_verification_code(request, appointment_request_id, id_request):
    """This view function handles the submission of the email verification code.

    :param request: The request instance.
    :param appointment_request_id: The ID of the appointment request.
    :param id_request: The unique ID of the appointment request.
    :return: The rendered HTML page.
    """
    if request.method == 'POST':
        email = request.session.get('email')
        code = request.POST.get('code')
        user = get_user_by_email(email)

        if verify_user_and_login(request, user, code):
            appointment_request_object = AppointmentRequest.objects.get(pk=appointment_request_id)
            appointment_data = get_appointment_data_from_session(request)
            response = create_appointment(request=request, appointment_request_obj=appointment_request_object,
                                          client_data={'email': email}, appointment_data=appointment_data)
            appointment = Appointment.objects.get(appointment_request=appointment_request_object)
            appointment_details = {
                'Service': appointment.get_service_name(),
                'Appointment Date': appointment.get_appointment_date(),
                'Appointment Time': appointment.appointment_request.start_time,
                'Duration': appointment.get_service_duration()
            }
            send_thank_you_email(ar=appointment_request_object, user=user, email=email,
                                 appointment_details=appointment_details, request=request)
            return response
        else:
            messages.error(request, _("Invalid verification code."))

    # base_template = request.session.get('BASE_TEMPLATE', '')
    # if base_template == '':
    #     base_template = APPOINTMENT_BASE_TEMPLATE
    extra_context = {
        'appointment_request_id': appointment_request_id,
        'id_request': id_request,
    }
    context = get_generic_context_with_extra(request, extra_context, admin=False)
    return render(request, 'appointment/enter_verification_code.html', context)

@user_passes_test(lambda u: u.groups.filter(name__in=['Admin','farmer']).exists())
@login_required(login_url="/login")
def default_thank_you(request, appointment_id):
    """This view function handles the default thank you page.

    :param request: The request instance.
    :param appointment_id: The ID of the appointment.
    :return: The rendered HTML page.
    """
    appointment = get_object_or_404(Appointment, pk=appointment_id)
    ar = appointment.appointment_request
    email = appointment.client.email
    appointment_details = {
        _('Service'): appointment.get_service_name(),
        _('Appointment Date'): appointment.get_appointment_date(),
        _('Appointment Time'): appointment.appointment_request.start_time,
        _('Duration'): appointment.get_service_duration()
    }
    account_details = {
        _('Email address'): email,
    }
    if username_in_user_model():
        account_details[_('Username')] = appointment.client.username
    send_thank_you_email(ar=ar, user=appointment.client, email=email, appointment_details=appointment_details,
                         account_details=account_details, request=request)
    extra_context = {
        'appointment': appointment,
    }
    context = get_generic_context_with_extra(request, extra_context, admin=False)
    return render(request, 'appointment/default_thank_you.html', context=context)

@user_passes_test(lambda u: u.groups.filter(name__in=['Admin','farmer']).exists())
@login_required(login_url="/login")
def set_passwd(request, uidb64, token):
    extra = {
        'page_title': _("Error"),
        'page_message': passwd_error,
        'page_description': _("Please try resetting your password again or contact support for help."),
    }
    context_ = get_generic_context_with_extra(request, extra, admin=False)
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = get_user_model().objects.get(pk=uid)
        token_verification = PasswordResetToken.verify_token(user, token)
        if token_verification is not None:
            if request.method == 'POST':
                form = SetPasswordForm(user, request.POST)
                if form.is_valid():
                    form.save()
                    messages.success(request, _("Password reset successfully."))
                    # Invalidate the token after successful password reset
                    token_verification.mark_as_verified()
                    extra = {
                        'page_title': _("Password Reset Successful"),
                        'page_message': passwd_set_successfully,
                        'page_description': _("You can now use your new password to log in.")
                    }
                    context = get_generic_context_with_extra(request, extra, admin=False)
                    return render(request, 'appointment/thank_you.html', context=context)
            else:
                form = SetPasswordForm(user)  # Display empty form for GET request
        else:
            messages.error(request, passwd_error)
            return render(request, 'appointment/thank_you.html', context=context_)
    except (TypeError, ValueError, OverflowError, get_user_model().DoesNotExist):
        messages.error(request, _("The password reset link is invalid or has expired."))
        return render(request, 'appointment/thank_you.html', context=context_)

    context_.update({'form': form})
    return render(request, 'appointment/set_password.html', context_)

@user_passes_test(lambda u: u.groups.filter(name__in=['Admin','farmer']).exists())
@login_required(login_url="/login")
def prepare_reschedule_appointment(request, id_request):
    ar = get_object_or_404(AppointmentRequest, id_request=id_request)

    if not can_appointment_be_rescheduled(ar):
        url = reverse('appointment_request', kwargs={'service_id': ar.service.id})
        context = get_generic_context_with_extra(request, {'url': url, }, admin=False)
        logger.error(f"Appointment with id_request {id_request} cannot be rescheduled")
        return render(request, 'error_pages/403_forbidden_rescheduling.html', context=context, status=403)

    service = ar.service
    selected_sm = ar.staff_member
    config = Config.objects.first()
    label = config.app_offered_by_label if config else _("Offered by")
    # if staff change allowed, filter all staff offering the service otherwise, filter only the selected staff member
    staff_filter_criteria = {'id': ar.staff_member.id} if not staff_change_allowed_on_reschedule() else {
        'services_offered': ar.service}
    all_staff_members = Worker.objects.filter(**staff_filter_criteria)
    available_slots = get_available_slots_for_staff(ar.date, selected_sm)
    page_title = _("Rescheduling appointment for {s}").format(s=service.name)
    page_description = _("Reschedule your appointment for {s} at {wn}.").format(s=service.name, wn=get_website_name())
    date_chosen = ar.date.strftime("%a, %B %d, %Y")

    extra_context = {
        'service': service,
        'staff_member': selected_sm,
        'all_staff_members': all_staff_members,
        'page_title': page_title,
        'page_description': page_description,
        'available_slots': available_slots,
        'date_chosen': date_chosen,
        'locale': get_locale(),
        'timezoneTxt': get_timezone_txt(),
        'label': label,
        'rescheduled_date': ar.date.strftime("%Y-%m-%d"),
        'page_header': page_title,
        'ar_id_request': ar.id_request,
    }
    context = get_generic_context_with_extra(request, extra_context, admin=False)
    return render(request, 'appointment/appointments.html', context=context)

@user_passes_test(lambda u: u.groups.filter(name__in=['Admin','farmer']).exists())
@login_required(login_url="/login")
def reschedule_appointment_submit(request):
    if request.method == 'POST':
        form = AppointmentRequestForm(request.POST)
        # get form values:
        ar_id_request = request.POST.get('appointment_request_id')
        ar = get_object_or_404(AppointmentRequest, id_request=ar_id_request)
        date_str = request.POST.get('date')
        date_ = convert_str_to_date(date_str)
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        sm_id = request.POST.get('staff_member')
        staff_member = get_object_or_404(Worker, id=sm_id)
        reason_for_rescheduling = request.POST.get('reason_for_rescheduling')
        if form.is_valid():
            arh = AppointmentRescheduleHistory.objects.create(
                appointment_request=ar,
                date=date_,
                start_time=start_time,
                end_time=end_time,
                staff_member=staff_member,
                reason_for_rescheduling=reason_for_rescheduling
            )
            messages.success(request, _("Appointment rescheduled successfully"))
            context = get_generic_context_with_extra(request, {}, admin=False)
            client_first_name = Appointment.objects.get(appointment_request=ar).client.first_name
            email = Appointment.objects.get(appointment_request=ar).client.email
            send_reschedule_confirmation_email(request=request, reschedule_history=arh, first_name=client_first_name,
                                               email=email, appointment_request=ar)
            return render(request, 'appointment/rescheduling_thank_you.html', context=context)
        else:
            messages.error(request, _("There was an error in your submission. Please check the form and try again."))
    else:
        form = AppointmentRequestForm()
    context = get_generic_context_with_extra(request, {'form': form}, admin=False)
    return render(request, 'appointment/appointments.html', context=context)

@user_passes_test(lambda u: u.groups.filter(name__in=['Admin','farmer']).exists())
@login_required(login_url="/login")
def confirm_reschedule(request, id_request):
    reschedule_history = get_object_or_404(AppointmentRescheduleHistory, id_request=id_request)

    if reschedule_history.reschedule_status != 'pending' or not reschedule_history.still_valid():
        error_message = _("O-o-oh! This link is no longer valid.") if not reschedule_history.still_valid() else _(
            "O-o-oh! Can't find the pending reschedule request.")
        context = get_generic_context_with_extra(request, {"error_message": error_message}, admin=False)
        return render(request, 'error_pages/404_not_found.html', status=404, context=context)

    ar = reschedule_history.appointment_request

    # Store previous details for logging or other purposes
    previous_details = {
        'date': ar.date,
        'start_time': ar.start_time,
        'end_time': ar.end_time,
        'staff_member': ar.staff_member,
    }

    # Update AppointmentRequest with new details
    ar.date = reschedule_history.date
    ar.start_time = reschedule_history.start_time
    ar.end_time = reschedule_history.end_time
    ar.staff_member = reschedule_history.staff_member
    ar.save(update_fields=['date', 'start_time', 'end_time', 'staff_member'])

    reschedule_history.date = previous_details['date']
    reschedule_history.start_time = previous_details['start_time']
    reschedule_history.end_time = previous_details['end_time']
    reschedule_history.staff_member = previous_details['staff_member']
    reschedule_history.reschedule_status = 'confirmed'
    reschedule_history.save(update_fields=['date', 'start_time', 'end_time', 'staff_member', 'reschedule_status'])

    messages.success(request, _("Appointment rescheduled successfully"))
    # notify admin and the concerned staff admin about client's rescheduling
    client_name = Appointment.objects.get(appointment_request=ar).client.get_full_name()
    notify_admin_about_reschedule(reschedule_history, ar, client_name)
    return redirect('appointment:default_thank_you', appointment_id=ar.appointment.id)

@user_passes_test(lambda u: u.groups.filter(name__in=['farmer']).exists())
@login_required(login_url="/login")
def get_service_client_list(request, response_type='html'):
    services = Service.objects.all()
    if response_type == 'json':
        service_data = []
        for service in services:
            service_data.append({
                'id': service.id,
                'name': service.name,
                'description': service.description,
                'duration': service.get_duration(),
                'price': service.get_price_text(),
                'down_payment': service.get_down_payment_text(),
                'image': service.get_image_url(),
                'background_color': service.background_color
            })
        return json_response("Successfully fetched services.", custom_data={'services': service_data}, safe=False)
    context = get_generic_context_with_extra(request=request, extra={'services': services})
    return render(request, 'appointment/service_client_list.html', context=context)

@user_passes_test(lambda u: u.groups.filter(name__in=['Admin','farmer']).exists())
@login_required(login_url="/login")
def payment_process(request, service_price):
    
    
    
    last_transaction = Transactions.objects.last()

        # Calculate new transaction ID
    if last_transaction:
        new_transaction_id = last_transaction.transaction_id + 1
    else:
        new_transaction_id = 1
        
        # Save payment details to the database
    Transactions.objects.create(transaction_id=new_transaction_id, amount=int(service_price / 110))
    # Calculate service price (assuming service_price is in INR)
    service_price_in_usd = service_price / 110
    
    # Pass service price to the template context
    context = {
        'service_price': service_price_in_usd,
    }
    
    # Render the payment page with the payment details passed to the context
    return render(request, 'appointment/payment_process.html', context)

def payment_success(request):

    for key in list(request.session.keys()):

        if key == 'session_key':

            del request.session[key]

    subject = 'Payment Success Notification'
    message = 'Your received a payment!'
    recipient_email = 'korlasaikiran8@gmail.com'  # Update with recipient's email address

    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [recipient_email])

    return render(request, 'appointment/payment_success.html')







def payment_failed(request):

    return render(request, 'appointment/payment_failed.html')

def transaction_history(request):
     # PayPal API endpoint
    api_endpoint = 'https://api.paypal.com/v2/payments/captures'

    # Make a GET request to retrieve transactions
    headers = {
        'Authorization': f'Bearer {settings.PAYPAL_ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }
    try:
        response = requests.get(api_endpoint, headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors
        transactions = response.json().get('transactions', [])
    except requests.RequestException as e:
        # Log the error or handle it as needed
        return HttpResponseServerError("Failed to retrieve transactions from PayPal.")
    
    return render(request, 'transaction_history.html', {'transactions': transactions})

@user_passes_test(lambda u: u.groups.filter(name__in=['farmer']).exists())
@login_required(login_url="/login")
def calendar_view(request):
    # Normalize username before filtering appointments
    normalized_username = request.user.username.lower()

    # Filter appointments for the logged-in user
    user_appointments = Appointment.objects.filter(client__username__iexact=normalized_username)
    
    # Pass appointment data to the template
    appointments_data = []
    for appointment in user_appointments:
        appointments_data.append({
            'title': f"{appointment.client.get_full_name()} - {appointment.appointment_request.service.name}",
            'start': appointment.appointment_request.date.isoformat(),  # Example: Get date from AppointmentRequest
            'end': appointment.appointment_request.end_time.isoformat(),  # Example: Get end time from AppointmentRequest
            # Access additional fields from the Appointment or AppointmentRequest models as needed
            'additional_info': appointment.additional_info,
            'paid': appointment.paid,
            'amount_to_pay': appointment.amount_to_pay,
            # Add more fields as needed
        })

    context = {'appointments_data': appointments_data}
    
    # Render the template with appointment data
    return render(request, 'main/calendar_view.html', context)

@user_passes_test(lambda u: u.groups.filter(name__in=['Admin']).exists())
@login_required(login_url="/login")
def refund_view(request):
    if request.method == 'POST':
        transaction_id = request.POST.get('transaction_id')

        try:
            sale = paypalrestsdk.Sale.find(transaction_id)
            if sale:
                refund = sale.refund()
                if refund.success():
                    return HttpResponse("Refund successful")
                else:
                    return HttpResponse("Refund failed: " + refund.error.message)
            else:
                return HttpResponse("Sale not found with given transaction ID")
        except paypalrestsdk.exceptions.PayPalConnectionError as e:
            return HttpResponse("Error connecting to PayPal: " + str(e))
        except Exception as e:
            return HttpResponse("An error occurred: " + str(e))
    else:
        return render(request, 'main/refund.html')

@user_passes_test(lambda u: u.groups.filter(name__in=['Workers']).exists())
@login_required(login_url="/login")   
def calendar_staff_view(request):
    # Fetch appointments from the AppointmentRequest model
    appointment_requests = AppointmentRequest.objects.all()

    # Prepare appointment data for rendering in the template
    appointments_data = []
    for appointment_request in appointment_requests:
        appointments_data.append({
            'title': appointment_request.service.name,  # Title is the service name
            'start': appointment_request.date.strftime('%Y-%m-%d') + 'T' + appointment_request.start_time.strftime('%H:%M:%S'),
            'end': appointment_request.date.strftime('%Y-%m-%d') + 'T' + appointment_request.end_time.strftime('%H:%M:%S'),
            # Include additional fields as needed
        })

    context = {'appointments_data': appointments_data}
    
    # Render the template with appointment data
    return render(request, 'main/calendar_staff_view.html', context)

@user_passes_test(lambda u: u.groups.filter(name__in=['Workers']).exists())
@login_required(login_url="/login") 
def task_list(request):
    tasks = Task.objects.all()
    return render(request, 'main/task_list.html', {'tasks': tasks})

def create_task(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('task_list')
    else:
        form = TaskForm()
    return render(request, 'main/create_task.html', {'form': form})

def view_task(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    return render(request, 'main/view_task.html', {'task': task})

def update_task(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            return redirect('task_list')
    else:
        form = TaskForm(instance=task)
    return render(request, 'main/update_task.html', {'form': form})

def delete_task(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    if request.method == 'POST':
        task.delete()
        return redirect('task_list')
    return render(request, 'main/delete_task.html', {'task': task})

@user_passes_test(lambda u: u.groups.filter(name__in=['Workers']).exists())
@login_required(login_url="/login") 
def apply_leave(request):
    if request.method == 'POST':
        form = LeaveForm(request.POST)
        if form.is_valid():
            form.save()
            # Redirect to a success page or homepage
            return redirect('worker_view')
    else:
        form = LeaveForm()
    return render(request, 'main/apply_leave.html', {'form': form})


@user_passes_test(lambda u: u.groups.filter(name__in=['Admin']).exists())
@login_required(login_url="/login") 
def transaction_list(request):
    transactions = Transactions.objects.all()
    return render(request, 'main/transaction_list.html', {'transactions': transactions})

@user_passes_test(lambda u: u.groups.filter(name__in=['Admin']).exists())
@login_required(login_url="/login")
def refund_transaction(request, transaction_id):
    # Retrieve transaction details based on the transaction_id
    transaction = Transactions.objects.get(transaction_id=transaction_id)
    
    context = {
        'service_price': transaction.amount
    }
    
    # Render the payment page with the payment details passed to the context
    return render(request, 'appointment/payment_process.html', context)

@user_passes_test(lambda u: u.groups.filter(name__in=['Workers']).exists())
@login_required(login_url="/login")
def mark_clock_in_out(request):
    if request.method == 'POST':
        form = ClockInOutForm(request.POST)
        if form.is_valid():
            attendance = form.save(commit=False)
            # Retrieve the Worker instance associated with the current user
            try:
                worker = request.user.worker_profile
            except Worker.DoesNotExist:
                # Handle the case where the user doesn't have a Worker profile
                # You can redirect them to a page to set up their profile or handle it based on your requirement
                pass
            else:
                attendance.worker = worker
                attendance.date = datetime.now().date()
                attendance.save()
                return redirect('worker_view')
    else:
        form = ClockInOutForm()
    return render(request, 'main/clock_in_out.html', {'form': form})

@user_passes_test(lambda u: u.groups.filter(name__in=['Admin']).exists())
@login_required(login_url="/login") 
def attendance_list(request):
    # Retrieve all attendance records
    attendance_records = Attendance.objects.all()
    
    # Create a list to store attendance data with worker names
    attendance_data = []
    
    # Iterate over each attendance record
    for record in attendance_records:
        # Access the worker's name through the ForeignKey relationship
        worker_name = record.worker.get_staff_member_name()  # Assuming 'get_staff_member_name()' is a method in Worker model
        
        # Append attendance data with worker name to the list
        attendance_data.append({
            'worker_name': worker_name,
            'date': record.date,
            'clock_in': record.clock_in,
            'clock_out': record.clock_out,
            # Include other attendance data as needed
        })
    
    return render(request, 'main/attendance_list.html', {'attendance_data': attendance_data})

@user_passes_test(lambda u: u.groups.filter(name__in=['Admin']).exists())
@login_required(login_url="/login")
def create_worker_payment(request, staff_user_id):
    # Ensure staff_user_id is provided and valid
    worker = get_object_or_404(Worker, id=staff_user_id)
    
    if request.method == 'POST':
        form = PaymentWorkerForm(request.POST)
        if form.is_valid():
            print("Form is valid")  # Debugging: Check if the form is valid
            payment = form.save(commit=False)
            payment.worker = worker
            payment.date = date.today()  # Use date.today() to set the current date
            payment.save()
            print("Payment saved:", payment)  # Debugging: Check if the payment is saved successfully
            return redirect('admin_view')  # Redirect to the admin_view URL after saving the payment
        else:
            print("Form errors:", form.errors)  # Debugging: Print form errors if the form is invalid
    else:
        form = PaymentWorkerForm(initial={'worker': worker})
    
    return render(request, 'main/create_payment.html', {'form': form})

@user_passes_test(lambda u: u.groups.filter(name__in=['Admin']).exists())
@login_required(login_url="/login")
def pay_worker(request, staff_user_id):
    worker = get_object_or_404(Worker, id=staff_user_id)
    payment = Payment_Worker.objects.filter(worker=worker).first()
    if payment:
        context = {'service_price': payment.amount}  # Pass staff_user_id to the context
        return render(request, 'appointment/payment_process.html', context)
    else:
        # Handle the case where no payment is found for the worker
        # For example, you could return a 404 response or render an appropriate template
        return HttpResponseNotFound("Payment not found for this worker")

@user_passes_test(lambda u: u.groups.filter(name__in=['Admin']).exists())
@login_required(login_url="/login") 
def payment_details(request):
    payments = Payment_Worker.objects.all()
    return render(request, 'main/payment_details.html', {'payments': payments})

@user_passes_test(lambda u: u.groups.filter(name__in=['Admin']).exists())
@login_required(login_url="/login") 
def feedback_details(request):
    feedbacks = Feedback.objects.all()
    for feedback in feedbacks:
        user = CustomUser.objects.get(id=feedback.user_id)
        feedback.user_name = user.username  # Add user name to each feedback object
    return render(request, 'main/feedback_details.html', {'feedbacks': feedbacks})

def generate_report(request, timeframe):
    # Get client name from request user
    current_date = datetime.now().strftime('%Y-%m-%d')
    client_name = request.user.username.lower()

    # Define start and end dates based on the selected timeframe
    if timeframe == 'daily':
        start_date = datetime.now().date()
        end_date = start_date + timedelta(days=1)
    elif timeframe == 'weekly':
        start_date = datetime.now().date() - timedelta(days=datetime.now().weekday())
        end_date = start_date + timedelta(weeks=1)
    elif timeframe == 'monthly':
        start_date = datetime(datetime.now().year, datetime.now().month, 1).date()
        end_date = start_date.replace(day=1, month=start_date.month+1)
    elif timeframe == 'yearly':
        start_date = datetime(datetime.now().year, 1, 1).date()
        end_date = start_date.replace(year=start_date.year+1)

    # Get appointments of the logged-in client within the selected timeframe
    client_appointments = Appointment.objects.filter(client__username__iexact=client_name,
                                                     created_at__date__gte=start_date,
                                                     created_at__date__lt=end_date)

    # Filter paid appointments
    paid_appointments = client_appointments.filter(paid=True)

    # Calculate total payment
    total_payment = sum(appointment.amount_to_pay for appointment in paid_appointments)

    # Get client details from the first paid appointment
    first_paid_appointment = paid_appointments.first()
    if first_paid_appointment:
        client_address = first_paid_appointment.address
        client_phone = str(first_paid_appointment.phone)  # Convert PhoneNumber object to string
    else:
        client_address = ""
        client_phone = ""

    # Create a response object
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="appointment_report.pdf"'

    # Create a PDF document
    doc = SimpleDocTemplate(response, pagesize=letter)
    elements = []

    # Define the styles
    styles = getSampleStyleSheet()
    normal_style = styles["Normal"]
    bold_style = styles["Heading2"]
    title_style = ParagraphStyle(
        name='TitleStyle',
        fontSize=16,
        textColor=colors.black,
        alignment=1,
        backColor=colors.lightblue,  # Set the background color
        spaceAfter=10,  # Add space after the paragraph
        width=doc.width
    )
    normal_style = ParagraphStyle(
        name='NormalStyle',
        fontSize=12,
        textColor=colors.black,
        alignment=2,  # Left alignment
        spaceAfter=5  # Add space after the paragraph
    )
    # Add title with center alignment and background color
    title_text = f"Services Report ({timeframe.capitalize()})"
    title_table = Table([[title_text]], colWidths=[doc.width])
    title_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.lightblue),  # Background color
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),  # Text color
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  # Center alignment
        ('FONTSIZE', (0, 0), (-1, -1), 14),
    ]))

    elements.append(title_table)

    # Add space between title and client details
    elements.append(Spacer(1, 20))

    # Add client details with light gray background
    client_details_info = [
        ("Date:", current_date),
        ("Client:", client_name),
        ("Client Address:", client_address),
        ("Client Phone:", client_phone)
    ]
    client_details_table = Table(client_details_info, colWidths=[100, 200])
    client_details_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),  # Background color
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),  # Vertical alignment to top
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),  # Left alignment
        ('LEFTPADDING', (0, 0), (-1, -1), 20),  # Left padding
    ]))
    elements.append(client_details_table)

    # Add space between client details and table
    elements.append(Spacer(1, 50))

    # Add services table with larger cell padding and background color for header
    services_info = [
        ["Service", "Worker", "Appointment Date", "Start Time", "End Time",  "Price"]
    ]
    for appointment in paid_appointments:
        services_info.append([
            appointment.get_service_name(),
            appointment.get_staff_member_name(),
            appointment.created_at.strftime('%Y-%m-%d'),
            appointment.created_at.strftime('%H:%M'),
            appointment.created_at.strftime('%H:%M'),
            "${:.2f}".format(appointment.amount_to_pay)
        ])
    services_table = Table(services_info, colWidths=[120, 110, 90, 70, 60, 100])
    services_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),  # Background color for header
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),  # Larger cell padding
    ]))
    elements.append(services_table)

    # Add total payment to the right
    total_payment_text = "Total Payment: ${:.2f}".format(total_payment)
    total_payment_paragraph = Paragraph(total_payment_text, normal_style)
    
    elements.append(total_payment_paragraph)

    # Build the PDF document
    doc.build(elements)

    return response

@user_passes_test(lambda u: u.groups.filter(name__in=['farmer']).exists())
@login_required(login_url="/login") 
def generate(request):
    return render(request, 'main/report.html')

def send_service_details(request):
    if request.method == 'POST':
        appointment_id = request.POST.get('appointment_id')
        print("Received appointment ID:", appointment_id) 
        appointment = Appointment.objects.get(pk=appointment_id)
        worker_email = 'arj831758@gmail.com'
        
        service_details = {
            'service_name': appointment.get_service_name(),
            'start_time': appointment.get_start_time(),
            'end_time': appointment.get_end_time(),
            'client_name': appointment.get_client_name(),
            'client_address': appointment.address,
            'client_phone' : appointment.phone,
            'worker_name' : appointment.get_staff_member_name().capitalize()
            # Add more service details as needed
        }
        send_service_details_email(worker_email, service_details)
        return HttpResponse('Email sent successfully')

    appointments = Appointment.objects.all()
    return render(request, 'main/send_service_details.html', {'appointments': appointments})

def send_service_details_email(worker_email, service_details):
    # Render email template
    context = {'service_details': service_details}
    html_message = render_to_string('main/email.html', context)
    plain_message = strip_tags(html_message)
    # Send email
    send_mail(
        'Confirmation of Appointment and Service Details',
        plain_message,
        settings.EMAIL_HOST_USER,
        [worker_email],
        html_message=html_message,
    )

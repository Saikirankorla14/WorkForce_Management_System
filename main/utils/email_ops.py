# email_ops.py
# Path: appointment/utils/email_ops.py

"""
Author: Saikiran 
Since: 1.1.0
"""

import datetime

from django.conf import settings
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import gettext as _

from main import messages as email_messages
from main.email_sender import notify_admin, send_email
from main.models import AppointmentRequest, EmailVerificationCode, PasswordResetToken
from main.settings import APPOINTMENT_PAYMENT_URL
from main.utils.date_time import convert_24_hour_time_to_12_hour_time
from main.utils.db_helpers import get_absolute_url_, get_website_name


def get_thank_you_message(ar: AppointmentRequest) -> str:
    """
    Get the appropriate email message based on the appointment request.

    If the payment URL is not set (APPOINTMENT_PAYMENT_URL is None), it returns the thank_you_no_payment message.
    If the appointment request accepts down payment, it returns the thank_you_payment_plus_down message.
    Otherwise, it returns the thank_you_payment message.

    :param ar: The appointment request.
    :return: The appropriate email message.
    """
    if APPOINTMENT_PAYMENT_URL is None:
        message = email_messages.thank_you_no_payment
    elif ar.accepts_down_payment():
        message = email_messages.thank_you_payment_plus_down
    else:
        message = email_messages.thank_you_payment
    return message


def send_thank_you_email(ar: AppointmentRequest, user, request, email: str, appointment_details=None,
                         account_details=None):
    """Send a thank-you email to the client for booking an appointment.

    :param ar: The appointment request associated with the booking.
    :param user: The user who booked the appointment.
    :param email: The email address of the client.
    :param appointment_details: Additional details about the appointment (default None).
    :param account_details: Additional details about the account (default None).
    :param request: The request object.
    :return: None
    """
    # Month and year like "J A N 2 0 2 1"
    month_year = ar.date.strftime("%b %Y").upper()
    day = ar.date.strftime("%d")
    token = PasswordResetToken.create_token(user=user, expiration_minutes=2880)  # 2 days expiration
    ui_db64 = urlsafe_base64_encode(force_bytes(user.pk))
    relative_set_passwd_link = reverse('appointment:set_passwd', args=[ui_db64, token.token])
    set_passwd_link = get_absolute_url_(relative_set_passwd_link, request=request)

    relative_reschedule_url = reverse('appointment:prepare_reschedule_appointment', args=[ar.get_id_request()])
    reschedule_link = get_absolute_url_(relative_reschedule_url, request)

    message = _("To enhance your experience, we have created a personalized account for you. It will allow "
                "you to manage your appointments, view service details, and make any necessary adjustments with ease.")

    email_context = {
        'first_name': user.first_name,
        'message_1': get_thank_you_message(ar),
        'current_year': datetime.datetime.now().year,
        'company': get_website_name(),
        'more_details': appointment_details,
        'account_details': account_details,
        'message_2': message if account_details is not None else None,
        'month_year': month_year,
        'day': day,
        'activation_link': set_passwd_link,
        'main_title': _("Appointment successfully scheduled"),
        'reschedule_link': reschedule_link,
    }
    send_email(
        recipient_list=[email], subject=_("Thank you for booking us."),
        template_url='email_sender/thank_you_email.html', context=email_context
    )


def notify_admin_about_appointment(appointment, client_name: str):
    """Notify the admin and the staff member about a new appointment request."""
    email_context = {
        'client_name': client_name,
        'appointment': appointment
    }

    subject = _("New Appointment Request for ") + client_name
    staff_member = appointment.get_staff_member()
    # Assuming notify_admin and send_email are previously defined functions
    notify_admin(subject=subject, template_url='email_sender/admin_new_appointment_email.html', context=email_context)
    if staff_member.user.email not in settings.ADMINS:
        send_email(recipient_list=[staff_member.user.email], subject=subject,
                   template_url='email_sender/admin_new_appointment_email.html', context=email_context)


def send_verification_email(user, email: str):
    """
    Send an email with a verification code to the user for email verification.

    Generates a verification code using the EmailVerificationCode model and sends it to the user's email.

    :param user: The user to verify the email address.
    :param email: The email address of the user.
    :return: None
    """
    code = EmailVerificationCode.generate_code(user=user)
    message = _("Your verification code is {code}.").format(code=code)
    send_email(recipient_list=[email], subject=_("Email Verification"), message=message)


def send_reschedule_confirmation_email(request, reschedule_history, appointment_request, first_name: str, email: str):
    """Send a rescheduling confirmation email to the client."""
    # Generate a URL for the confirmation action
    relative_confirmation_link = reverse('appointment:confirm_reschedule', args=[reschedule_history.id_request])
    confirmation_link = get_absolute_url_(relative_confirmation_link, request)

    # Email context
    email_context = {
        'is_confirmation': True,
        'first_name': first_name,
        'old_date': appointment_request.date.strftime("%A, %d %B %Y"),
        'reschedule_date': reschedule_history.date.strftime("%A, %d %B %Y"),
        'old_start_time': convert_24_hour_time_to_12_hour_time(appointment_request.start_time),
        'start_time': convert_24_hour_time_to_12_hour_time(reschedule_history.start_time),
        'old_end_time': convert_24_hour_time_to_12_hour_time(appointment_request.end_time),
        'end_time': convert_24_hour_time_to_12_hour_time(reschedule_history.end_time),
        'confirmation_link': confirmation_link,
        'company': get_website_name(),
    }

    subject = _("Confirm Your Appointment Rescheduling")
    send_email(
        recipient_list=[email], subject=subject,
        template_url='email_sender/reschedule_email.html', context=email_context
    )


def notify_admin_about_reschedule(reschedule_history, appointment_request, client_name: str):
    """Notify the admin and the staff member about a rescheduled appointment request."""
    # Assuming you have a way to fetch these additional details
    service_name = appointment_request.service.name
    reason_for_rescheduling = reschedule_history.reason_for_rescheduling

    email_context = {
        'is_confirmation': False,
        'client_name': client_name,
        'service_name': service_name,
        'reason_for_rescheduling': reason_for_rescheduling,
        'old_date': appointment_request.date.strftime("%A, %d %B %Y"),
        'reschedule_date': reschedule_history.date.strftime("%A, %d %B %Y"),
        'old_start_time': convert_24_hour_time_to_12_hour_time(appointment_request.start_time),
        'start_time': convert_24_hour_time_to_12_hour_time(reschedule_history.start_time),
        'old_end_time': convert_24_hour_time_to_12_hour_time(appointment_request.end_time),
        'end_time': convert_24_hour_time_to_12_hour_time(reschedule_history.end_time),
        'company': get_website_name(),
    }

    subject = _("Reschedule Request for ") + client_name
    staff_member = appointment_request.staff_member
    # Assuming notify_admin and send_email are previously defined functions
    notify_admin(subject=subject, template_url='email_sender/reschedule_email.html', context=email_context)
    if staff_member.user.email not in settings.ADMINS:
        send_email(recipient_list=[staff_member.user.email], subject=subject,
                   template_url='email_sender/reschedule_email.html', context=email_context)
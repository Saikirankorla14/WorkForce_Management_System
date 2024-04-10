from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.index, name='home'),
    path('index', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.custom_logout_view, name='logout'),
    path('sign-up/', views.sign_up, name='custom_signup'),
    path('farmer_home/', views.farmer_home, name='farmer_home'),
    path('add-service/', views.add_or_update_service, name='add_service'),
    path('admin_view/', views.admin_view, name='admin_view'),
    path('worker-view/', views.worker_view, name='worker_view'),
    path('manager_home/', views.manager_home, name='manager_home'),
    path('update_profile/', views.update_profile, name='update_profile'),
    path('profile/', views.profile, name='profile'),
    path('add_farm/', views.add_farm, name='add_farm'),
    path('edit_farm/<int:farm_id>/', views.edit_farm, name='edit_farm'),
    path('farm_details/<int:farm_id>/', views.farm_details, name='farm_details'),
    path('add_person/<int:farm_id>/farm_workers', views.add_person, name='add_person'),
    path('edit_person/<int:farm_id>/<int:person_id>/', views.edit_person, name='edit_person'),
    path('farm/<int:farm_id>/add_farm_dates/', views.add_farm_dates, name='add_farm_dates'),
    path('farm/<int:farm_id>/update_farm_dates/<int:farming_dates_id>/', views.update_farm_dates, name='update_farm_dates'),
    path('farm/<int:farm_id>/add_farm_costs/', views.add_farm_costs, name='add_farm_costs'),
    path('farm/<int:farm_id>/update_farm_costs/<int:farming_costs_id>/', views.update_farm_costs, name='update_farm_costs'),
    path('farm/<int:farm_id>/add_farm_produce/', views.add_farm_produce, name='add_farm_produce'), 
    path('farm/<int:farm_id>/update_farm_produce/<int:farm_produce_id>/', views.update_farm_produce, name='update_farm_produce'),
    path('view_more_farms/', views.view_more_farms, name='view_more_farms'),
    path('<int:farm_id>/view_more_farm_dates/', views.view_more_farm_dates, name='view_more_farm_dates'),
    path('<int:farm_id>/view_more_farm_costs/', views.view_more_farm_costs, name='view_more_farm_costs'),
    path('<int:farm_id>/view_more_farm_produce/', views.view_more_farm_produce, name='view_more_farm_produce'),
    path('<int:farm_id>/view_more_farm_staff/', views.view_more_farm_staff, name='view_more_farm_staff'),
    path('<int:farm_id>/view_more_farm_labourers/', views.view_more_farm_labourers, name='view_more_farm_labourers'),
    path('farm/<int:farm_id>/delete_person/<int:person_id>/', views.delete_person, name='delete_person'),
    path('farm_details/<int:farm_id>/create_resource/', views.create_resource, name='create_resource'),
    path('farm_resources/<int:farm_id>/', views.farm_resources, name='farm_resources'),
    path('farm_workers/<int:farm_id>/', views.farm_workers, name='farm_workers'),
    path('scheduler/<int:farm_id>/', views.scheduler, name='scheduler'),
    path('workers_data/<int:farm_id>/<int:worker_name_id>/', views.workers_data, name='workers_data'),
    path('farm_activities/<int:farm_id>/', views.farm_activities, name='farm_activities'),
    path('farm/<int:farm_id>/farm_photos/', views.farm_photos, name='farm_photos'),
    path('get_image_names/', views.get_image_names, name='get_image_names'),
    path('search/', views.search_view, name='search_view'),
    path('farm/<int:farm_id>/delete_farm/', views.delete_farm, name='delete_farm'),
    path('get_current_user/', views.get_current_user, name='get_current_user'),
    path('farm_visit_report/create/<int:farm_visit_request_id>/', views.create_farm_visit_report, name='create_farm_visit_report'),
    path('annadatha/training/', views.training, name='training'),
    # Password Reset urls
    path('password_reset', auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html'), name='password_reset'),
    path('reset_password_sent', auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset_password_complete', auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'),
 # Include media URLs
    path('payment/create/', views.payment_create, name='payment_create'),
    path('payment/update/<int:pk>/', views.payment_update, name='payment_update'),
    path('payment/list/', views.payment_list, name='payment_list'),
    path('feedback/', views.leave_feedback, name='feedback'),
    path('appointments/<str:response_type>/', views.get_user_appointments, name='get_user_event_type'),
    path('appointments/', views.get_user_appointments, name='get_user_appointments'),

    # create a new staff member and make/remove superuser staff member
    path('staff-member-personal-info/', views.create_new_staff_member, name='add_staff_member_personal_info'),
    path('update-staff-member/<int:user_id>/', views.add_or_update_staff_info, name='update_staff_other_info'),
    path('add-staff-member/', views.add_or_update_staff_info, name='add_staff_other_info'),
    path('make-superuser-staff-member/', views.make_superuser_staff_member, name='make_superuser_staff_member'),
    path('remove-superuser-staff-member/', views.remove_superuser_staff_member, name='remove_superuser_staff_member'),

    # remove staff member
    path('remove-staff-member/<int:staff_user_id>/', views.remove_staff_member, name='remove_staff_member'),

    # add, update, remove services
    path('add-service/', views.add_or_update_service, name='add_service'),
    path('update-service/<int:service_id>/', views.add_or_update_service, name='update_service'),
    path('delete-service/<int:service_id>/', views.delete_service, name='delete_service'),
    path('service-list/', views.get_service_list, name='get_service_list'),
    path('service-list/<str:response_type>/', views.get_service_list, name='get_service_list_type'),
    path('view-service/<int:service_id>/<int:view>/', views.add_or_update_service, name='view_service'),

    # display details for one event
    path('display-appointment/<int:appointment_id>/', views.display_appointment, name='display_appointment'),

    # complete profile
    path('user-profile/<int:staff_user_id>/', views.user_profile, name='user_profile'),
    path('user-profile/', views.user_profile, name='user_profile'),
    path('update-user-info/<int:staff_user_id>/', views.update_personal_info, name='update_user_info'),
    path('update-user-info/', views.update_personal_info, name='update_user_info'),

    # add, update, delete day off with staff_user_id
    path('add-day-off/<int:staff_user_id>/', views.add_day_off, name='add_day_off'),
    path('update-day-off/<int:day_off_id>/<int:staff_user_id>/', views.update_day_off, name='update_day_off_id'),
    path('delete-day-off/<int:day_off_id>/<int:staff_user_id>/', views.delete_day_off, name='delete_day_off_id'),

    # add, update, delete day off without staff_user_id
    path('update-day-off/<int:day_off_id>/', views.update_day_off, name='update_day_off'),
    path('delete-day-off/<int:day_off_id>/', views.delete_day_off, name='delete_day_off'),

    # add, update, delete working hours with staff_user_id
    path('update-working-hours/<int:working_hours_id>/<int:staff_user_id>/', views.update_working_hours,
         name='update_working_hours_id'),
    path('add-working-hours/<int:staff_user_id>/', views.add_working_hours, name='add_working_hours_id'),
    path('delete-working-hours/<int:working_hours_id>/<int:staff_user_id>/', views.delete_working_hours,
         name='delete_working_hours_id'),

    # add, update, delete working hours without staff_user_id
    path('update-working-hours/<int:working_hours_id>/', views.update_working_hours, name='update_working_hours'),
    path('add-working-hours/', views.add_working_hours, name='add_working_hours'),
    path('delete-working-hours/<int:working_hours_id>/', views.delete_working_hours, name='delete_working_hours'),

    # delete appointment
    path('delete-appointment/<int:appointment_id>/', views.delete_appointment, name='delete_appointment'),
     path('available_slots/', views.get_available_slots_ajax, name='available_slots_ajax'),
    path('request_next_available_slot/<int:service_id>/', views.get_next_available_date_ajax,
         name='request_next_available_slot'),
    path('request_staff_info/', views.get_non_working_days_ajax, name='get_non_working_days_ajax'),
    path('fetch_service_list_for_staff/', views.fetch_service_list_for_staff, name='fetch_service_list_for_staff'),
    path('update_appt_min_info/', views.update_appt_min_info, name="update_appt_min_info"),
    path('update_appt_date_time/', views.update_appt_date_time, name="update_appt_date_time"),
    path('validate_appointment_date/', views.validate_appointment_date, name="validate_appointment_date"),
    # delete appointment ajax
    path('delete_appointment/', views.delete_appointment_ajax, name="delete_appointment_ajax"),
    path('is_user_staff_admin/', views.is_user_staff_admin, name="is_user_staff_admin"),
     path('request/<int:service_id>/', views.appointment_request, name='appointment_request'),
    path('request-submit/', views.appointment_request_submit, name='appointment_request_submit'),
    path('appointment/<str:id_request>/reschedule/', views.prepare_reschedule_appointment,
         name='prepare_reschedule_appointment'),
    path('appointment-reschedule-submit/', views.reschedule_appointment_submit, name='reschedule_appointment_submit'),
    path('confirm-reschedule/<str:id_request>/', views.confirm_reschedule, name='confirm_reschedule'),
    path('client-info/<int:appointment_request_id>/<str:id_request>/', views.appointment_client_information,
         name='appointment_client_information'),
    path('verification-code/<int:appointment_request_id>/<str:id_request>/', views.enter_verification_code,
         name='enter_verification_code'),
    path('verification-code/', views.email_change_verification_code, name='email_change_verification_code'),
    path('thank-you/<int:appointment_id>/', views.default_thank_you, name='default_thank_you'),
    path('verify/<uidb64>/<str:token>/', views.set_passwd, name='set_passwd'),
    path('service-client-list/', views.get_service_client_list, name='get_service_client_list'),
    path('payment-process/<int:service_price>', views.payment_process, name='payment_process'),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('payment-failed/', views.payment_failed, name='payment_failed'),
    path('calendar-view/', views.calendar_view, name='calendar_view'),
    path('calendar-staff-view/', views.calendar_staff_view, name='calendar_staff_view'),
    path('refund/', views.refund_view, name='refund'),
    path('tasks/', views.task_list, name='task_list'),
    path('task/create/', views.create_task, name='create_task'),
    path('task/<int:task_id>/', views.view_task, name='view_task'),
    path('task/<int:task_id>/update/', views.update_task, name='update_task'),
    path('task/<int:task_id>/delete/', views.delete_task, name='delete_task'),
    path('apply-leave/', views.apply_leave, name='apply_leave'),
    path('transactions/', views.transaction_list, name='transaction_list'),
    path('refund-transaction/<int:transaction_id>', views.refund_transaction, name='refund_transaction'),
    path('attendance/', views.mark_clock_in_out, name='attendance'),
    path('attendance-list/', views.attendance_list, name='attendance_list'),
    path('worker-payment/<int:staff_user_id>/', views.create_worker_payment, name='worker_payment'),
    path('pay-worker/<int:staff_user_id>/', views.pay_worker, name='pay_worker'),
    path('payment-details/', views.payment_details, name='payment_details'),
    path('feedback-details/', views.feedback_details, name='feedback_details'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
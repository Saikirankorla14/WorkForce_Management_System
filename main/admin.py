from django.contrib import admin
from django import forms

from .models import Appointment, AppointmentRequest, AppointmentRescheduleHistory, Config, CustomUser, DayOff, EmailVerificationCode, PasswordResetToken, Payment, Person, Farm, Crop, Resource, FarmingDates,FarmingCosts, FarmProduce, FarmVisitRequest, Message, FarmVisitReport, Reply , Service, Worker, WorkingHours
from django.contrib.auth.admin import UserAdmin
from django.contrib import admin
from datetime import date
from django.utils.translation import gettext_lazy as _

admin.site.register(Crop)

# Customize Admin App

admin.site.site_header = 'Workforce Management System'
admin.site.site_title = 'Workforce Management System'
admin.site.index_title = 'Workforce Management System'


class CreatedDateFilter(admin.SimpleListFilter):
    title = _('Created Date')
    parameter_name = 'created_date'

    def lookups(self, request, model_admin):
        return (
            ('today', _('Today')),
            ('this_week', _('This week')),
            ('this_month', _('This month')),
            ('this_year', _('This year')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'today':
            return queryset.filter(created__date=date.today())
        elif self.value() == 'this_week':
            return queryset.filter(created__week=date.today().isocalendar()[1], created__year=date.today().year)
        elif self.value() == 'this_month':
            return queryset.filter(created__month=date.today().month, created__year=date.today().year)
        elif self.value() == 'this_year':
            return queryset.filter(created__year=date.today().year)


class CreatedDateFilterAdminMixin(admin.ModelAdmin):
    list_filter = (CreatedDateFilter,)

class CreatedDateAndGroupsFilter(admin.SimpleListFilter):
    title = 'Date Joined and Groups'
    parameter_name = 'created_date_and_groups'

    def lookups(self, request, model_admin):
        return (
            ('today', 'Today'),
            ('this_week', 'This week'),
            ('this_month', 'This month'),
            ('this_year', 'This year'),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == 'today':
            queryset = queryset.filter(date_joined__date=date.today())
        elif value == 'this_week':
            queryset = queryset.filter(date_joined__week=date.today().isocalendar()[1], date_joined__year=date.today().year)
        elif value == 'this_month':
            queryset = queryset.filter(date_joined__month=date.today().month, date_joined__year=date.today().year)
        elif value == 'this_year':
            queryset = queryset.filter(date_joined__year=date.today().year)

        # Handle the groups filter
        groups_value = request.GET.get('groups', None)
        if groups_value:
            queryset = queryset.filter(groups__id=groups_value)

        return queryset

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active')
    list_filter = (CreatedDateAndGroupsFilter, 'groups')

# Register your CustomUserAdmin
admin.site.register(CustomUser, CustomUserAdmin)

@admin.register(Farm)
class FarmAdmin(CreatedDateFilterAdminMixin):
    pass

@admin.register(Person)
class PersonAdmin(CreatedDateFilterAdminMixin):
    pass

@admin.register(FarmingDates)
class FarmingDatesAdmin(CreatedDateFilterAdminMixin):
    pass

@admin.register(FarmingCosts)
class FarmingCostsAdmin(CreatedDateFilterAdminMixin):
    pass

@admin.register(FarmProduce)
class FarmProduceAdmin(CreatedDateFilterAdminMixin):
    pass

@admin.register(Resource)
class ResourceAdmin(CreatedDateFilterAdminMixin):
    pass

@admin.register(FarmVisitRequest)
class FarmVisitRequestAdmin(CreatedDateFilterAdminMixin):
    pass

@admin.register(FarmVisitReport)
class FarmVisitReportAdmin(CreatedDateFilterAdminMixin):
    pass

@admin.register(Payment)
class PaymentAdmin(CreatedDateFilterAdminMixin):
    pass


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'duration', 'price', 'created_at', 'updated_at',)
    search_fields = ('name',)
    list_filter = ('duration',)


@admin.register(AppointmentRequest)
class AppointmentRequestAdmin(admin.ModelAdmin):
    list_display = ('date', 'start_time', 'end_time', 'service', 'created_at', 'updated_at',)
    search_fields = ('date', 'service__name',)
    list_filter = ('date', 'service',)


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('client', 'appointment_request', 'created_at', 'updated_at',)
    search_fields = ('appointment_request__service__name',)
    list_filter = ('client', 'appointment_request__service',)


@admin.register(EmailVerificationCode)
class EmailVerificationCodeAdmin(admin.ModelAdmin):
    list_display = ('user', 'code')


@admin.register(Config)
class ConfigAdmin(admin.ModelAdmin):
    list_display = (
        'slot_duration', 'lead_time', 'finish_time', 'appointment_buffer_time', 'website_name', 'app_offered_by_label')


# Define a custom ModelForm for Worker
class WorkerForm(forms.ModelForm):
    class Meta:
        model = Worker
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


@admin.register(Worker)
class WorkerAdmin(admin.ModelAdmin):
    form = WorkerForm
    list_display = (
        'get_staff_member_name', 'get_slot_duration', 'lead_time', 'finish_time', 'work_on_saturday', 'work_on_sunday')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    list_filter = ('work_on_saturday', 'work_on_sunday', 'lead_time', 'finish_time')


@admin.register(DayOff)
class DayOffAdmin(admin.ModelAdmin):
    list_display = ('staff_member', 'start_date', 'end_date', 'description')
    search_fields = ('description',)
    list_filter = ('start_date', 'end_date')


@admin.register(WorkingHours)
class WorkingHoursAdmin(admin.ModelAdmin):
    list_display = ('staff_member', 'day_of_week', 'start_time', 'end_time')
    search_fields = ('day_of_week',)
    list_filter = ('day_of_week', 'start_time', 'end_time')


@admin.register(AppointmentRescheduleHistory)
class AppointmentRescheduleHistoryAdmin(admin.ModelAdmin):
    list_display = (
        'appointment_request', 'date', 'start_time',
        'end_time', 'staff_member', 'reason_for_rescheduling', 'created_at'
    )
    search_fields = (
        'appointment_request__id_request', 'staff_member__user__first_name',
        'staff_member__user__last_name', 'reason_for_rescheduling'
    )
    list_filter = ('appointment_request__service', 'date', 'created_at')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'token', 'expires_at', 'status')
    search_fields = ('user__email', 'token')
    list_filter = ('status', 'expires_at')
    date_hierarchy = 'expires_at'
    ordering = ('-expires_at',)


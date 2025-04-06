from django.contrib import admin
from .models import AccessToken, Profile, Shareholder, ErrorLog

class ShareholderInline(admin.TabularInline):
    model = Shareholder
    extra = 0

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['unique_identifier', 'person_type', 'get_name', 'mobile', 'created_at']
    list_filter = ['person_type', 'created_at']
    search_fields = ['unique_identifier', 'first_name', 'last_name', 'company_name', 'mobile']
    inlines = [ShareholderInline]
    
    def get_name(self, obj):
        if obj.person_type == 'IranianPrivatePerson':
            return f"{obj.first_name} {obj.last_name}"
        else:
            return obj.company_name
    get_name.short_description = 'Name'

@admin.register(AccessToken)
class AccessTokenAdmin(admin.ModelAdmin):
    list_display = ['token', 'token_end_time', 'created_at']
    readonly_fields = ['token', 'token_end_time', 'created_at']

@admin.register(ErrorLog)
class ErrorLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'error_data']
    readonly_fields = ['timestamp', 'error_data']
    list_filter = ['timestamp']
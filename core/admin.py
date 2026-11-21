from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Profile


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name = 'Профиль'
    verbose_name_plural = 'Профиль'


class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)
    list_select_related = ('profile',)


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'avatar')
    search_fields = ('user__username', 'user__email')
    list_filter = ('user__is_active', 'user__is_staff')
    raw_id_fields = ('user',)
    list_select_related = ('user',)
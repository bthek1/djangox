import django
from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.shortcuts import resolve_url
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from hijack.conf import settings
from hijack.contrib.admin import HijackUserAdminMixin
from hijack.forms import ESM

from .forms import CustomUserChangeForm, CustomUserCreationForm
from .models import CustomUser


class CustomUserAdmin(HijackUserAdminMixin, UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser

    list_display = (
        "email",
        "first_name",
        "last_name",
        "is_staff",
        "is_active",
        # "hijack_button",  # Use a method that provides the hijack button
    )
    list_filter = ("is_staff", "is_active")
    search_fields = ("email", "first_name", "last_name")
    ordering = ("email",)
    readonly_fields = ("last_login", "date_joined", "groups")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal Info", {"fields": ("first_name", "last_name")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_staff",
                    "is_active",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "password1",
                    "password2",
                    "is_staff",
                    "is_active",
                    "groups",
                ),
            },
        ),
    )

    @property
    def media(self):
        return super().media + forms.Media(js=[ESM("hijack/hijack.js")])

    def get_hijack_user(self, obj):
        """
        Return the user based on the current object.

        This method may be overridden to support hijack keys on related objects.
        """
        return obj

    def get_hijack_success_url(self, request, obj):
        """Return URL to which one will be forwarded to after hijacking another user."""
        success_url = settings.LOGIN_REDIRECT_URL
        if self.hijack_success_url:
            success_url = self.hijack_success_url
        elif hasattr(obj, "get_absolute_url"):
            success_url = obj
        return resolve_url(success_url)

    def hijack_button(self, request, obj):
        """
        Render hijack button.

        Should the user only be a related object we include the username in the button
        to ensure deliberate action. However, the name is omitted in the user admin,
        as the table layout suggests that the button targets the current user.
        """
        user = self.get_hijack_user(obj)
        return render_to_string(
            "button.html",
            {
                "request": request,
                "another_user": user,
                "username": str(user),
                "is_user_admin": self.model is type(user),
                "next": self.get_hijack_success_url(request, obj),
            },
            request=request,
        )

    def get_changelist_instance(self, request):
        # We inject the request for the CSRF token, see also:
        # https://code.djangoproject.com/ticket/13659
        def hijack_field(obj):
            return self.hijack_button(request, obj)

        hijack_field.short_description = _("impersonate user")

        # we
        list_display = [*self.get_list_display(request), hijack_field]
        # Same as super method, see also:
        # https://github.com/django/django/blob/76c0b32f826469320c59709d31e2f2126dd7c505/django/contrib/admin/options.py#L724-L750
        list_display_links = self.get_list_display_links(request, list_display)
        # Add the action checkboxes if any actions are available.
        if self.get_actions(request):
            list_display = ["action_checkbox", *list_display]
        sortable_by = self.get_sortable_by(request)
        ChangeList = self.get_changelist(request)
        args = [
            request,
            self.model,
            list_display,
            list_display_links,
            self.get_list_filter(request),
            self.date_hierarchy,
            self.get_search_fields(request),
            self.get_list_select_related(request),
            self.list_per_page,
            self.list_max_show_all,
            self.list_editable,
            self,
            sortable_by,
        ]
        if django.VERSION >= (4, 0):
            args.append(self.search_help_text)
        return ChangeList(*args)


admin.site.register(CustomUser, CustomUserAdmin)

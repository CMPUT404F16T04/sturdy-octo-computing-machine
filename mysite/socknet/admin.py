from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm as AdminUserCreationForm
from django.contrib.auth import get_user_model
from django.forms import PasswordInput, ValidationError, CharField

from socknet.models import *
from socknet.forms import *

class UserAdmin(admin.ModelAdmin):
    """
    Custom administrative page and actions for the User model.
    """
    list_display = ['username', 'is_approved', 'date_joined']
    ordering = ['username']
    actions = ['approve_users']

    # Field sets control which fields are displayed on the admin "add" and "change" pages
    def get_form(self, request, obj=None, **kwargs):
        if obj is None:
            return CreateUserForm
        else:
            kwargs['fields'] = ['username', 'is_active',]
            return super(UserAdmin, self).get_form(request, obj, **kwargs)


    def is_approved(self, obj):
        """
        Checks if a user has been approved.
        """
        return Author.objects.filter(user=obj).exists()
    is_approved.short_description = 'Approved'
    is_approved.boolean = True # Display as icon

    def approve_users(self, request, queryset):
        """
        Approve users who have signed up but do not have an account.
        Approval will assign the user account to an author and activate the account.
        """
        for user in queryset:
            # Assign each selected user to an author
            if not Author.objects.filter(user=user).exists():
                new_author = Author(user=user, displayName=user.username)
                new_author.url = request.get_host() + "/author/" + str(new_author.uuid) + "/"
                new_author.save()

        rows_updated = queryset.update(is_active=True)
        if rows_updated == 1:
            message_bit = "1 user was"
        else:
            message_bit = "%s users were" % rows_updated
        self.message_user(request, "%s successfully approved." % message_bit)
    approve_users.short_description = "Approve Selected Users"

class AuthorAdmin(admin.ModelAdmin):
    """
    A custom admin page for the Author model.
    IMPORTANT: Friends and followers should not be editable in the admin console
    because the system can be put into a weird state.
    """
    list_display = ['user']
    ordering = ['user']

    # Field sets control which fields are displayed on the admin "add" and "change" pages
    readonly_fields=('friends', 'who_im_following', 'ignored', 'foreign_friends', 'url')
    fieldsets = (
        (None, {
            'fields': ('user', 'displayName', 'url', 'about_me', 'birthday','github_url', 'friends', 'who_im_following', 'ignored', 'foreign_friends')
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        """
        Get the fields that are read-only. If we are making a new author, then allow user to be added.
        """
        if obj: # editing an existing object
            return self.readonly_fields + ('user',)
        return self.readonly_fields

class ConfigAdmin(admin.ModelAdmin):
    """
    A custom admin page for the AdminConfig model.
    Do not allow add or delete actions for this object.
    """
    def get_actions(self, request):
        # Code from: http://stackoverflow.com/questions/4043843/in-django-admin-how-do-i-disable-the-delete-link
        # Disable delete
        actions = super(ConfigAdmin, self).get_actions(request)
        del actions['delete_selected']
        return actions

    def has_delete_permission(self, request, obj=None):
        # Disable delete
        return False

    def has_add_permission(self, request):
        return False

# Our site config
admin.site.register(AdminConfig, ConfigAdmin)

# Unregister default user so that ours is used
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# Models we want to be able to edit in admin
admin.site.register(Node)
admin.site.register(Post)
admin.site.register(Author, AuthorAdmin)
admin.site.register(Comment)
admin.site.register(ImageServ)

from django.contrib import admin
from django.contrib.auth.models import User

from socknet.models import *

class UserAdmin(admin.ModelAdmin):
    """
    Custom administrative page and actions for the User model.
    """
    list_display = ['username', 'is_approved', 'date_joined']
    ordering = ['username']
    actions = ['approve_users']

    # Field sets control which fields are displayed on the admin "add" and "change" pages
    fieldsets = (
        (None, {
            'fields': ('username',)
        }),
        ('Permissions', {
            'fields': ('is_superuser',)
        }),
    )

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
                new_author = Author(user=user)
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
    CURRENTLY CAN ONLY VIEW AUTHOR INFORMATION FOR TESTING PURPOSES
    """
    list_display = ['user']
    ordering = ['user']
    change_form_template = 'admin/view_author.html'

    # Remove the delete Admin Action for this Model
    actions = None

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        #Return nothing to make sure user can't update any data
        pass

# Unregister default user so that ours is used
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# Models we want to be able to edit in admin
admin.site.register(Post)
admin.site.register(Author, AuthorAdmin)
admin.site.register(Comment)
admin.site.register(ImageServ)

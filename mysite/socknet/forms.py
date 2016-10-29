from django.forms import ModelForm , PasswordInput, ValidationError, CharField
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate

class RegistrationForm(ModelForm):
    """
    A form that creates a user, but the user will not be active
    until an administrator approves them.
    """

    password = CharField(label="Password", widget=PasswordInput)
    confirm_password = CharField(label="Confirm Password", widget=PasswordInput)

    class Meta:
        model = User
        fields = ['username']

    def clean_confirm_password(self):
        """
        Validate that the passwords match.
        """
        password = self.cleaned_data.get('password')
        confirm_password = self.cleaned_data.get('confirm_password')
        if password != confirm_password:
            raise ValidationError("Passwords must match")
        return confirm_password

    def clean_username(self):
        """
        Validate that the username is unique
        """
        username = self.cleaned_data.get("username")
        if User.objects.filter(username=username):
            raise ValidationError("Username is already in use")
        return username

    def save(self, commit=True):
        """
        Save the user but their account is not active yet.
        """
        user = super(RegistrationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password"])
        user.is_active = False
        if commit:
            user.save()
        return user

class CustomAuthenticationForm(AuthenticationForm):
    """
    Display account inactive error over invalid username and password.
    This allows a user to know that they are signed up, but awaiting approval.
    """

    def find_user(self, username):
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            return None

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        user = self.find_user(username)
        if (user and user.is_active == False):
            raise ValidationError("This account has not been approved yet.")
        return super(CustomAuthenticationForm, self).clean()

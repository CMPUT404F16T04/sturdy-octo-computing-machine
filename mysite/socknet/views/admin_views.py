from django.views import generic
from django.contrib import messages

from socknet.forms import RegistrationForm

class RegistrationView(generic.edit.FormView):
    template_name = "registration/registration.html"
    form_class = RegistrationForm
    success_url = '/login/'

    def form_valid(self, form):
        form.save()
        # Display a notification
        messages.add_message(self.request, messages.SUCCESS, "Registration Successful. An administrator will approve you account.")
        return super(RegistrationView, self).form_valid(form)

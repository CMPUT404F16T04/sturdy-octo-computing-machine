from django.dispatch import receiver
from django.db.models.signals import post_delete
from socknet.models import Author

@receiver(post_delete, sender=Author)
def post_delete_user(sender, instance, *args, **kwargs):
    instance.user.delete()

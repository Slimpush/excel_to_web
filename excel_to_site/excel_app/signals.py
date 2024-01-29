from django.db.models.signals import pre_save
from django.dispatch import receiver

from .models import Accounts


@receiver(pre_save, sender=Accounts)
def set_class_block(sender, instance, **kwargs):
    # Установка значения class_block перед сохранением объекта
    if not instance.class_block and instance.account_number:
        account_number = str(instance.account_number)
        instance.class_block = account_number[0] if account_number else None

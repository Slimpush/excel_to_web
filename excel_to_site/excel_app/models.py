from django.db import models


class Accounts(models.Model):
    account_number = models.CharField(max_length=20, unique=True)
    class_block = models.CharField(max_length=1, blank=True, null=True)

    def __str__(self):
        return f"{self.account_number} - Class Block {self.class_block}"


class AccountData(models.Model):
    account = models.ForeignKey(Accounts, on_delete=models.CASCADE)
    incoming_active = models.DecimalField(max_digits=20, decimal_places=2)
    incoming_passive = models.DecimalField(max_digits=20, decimal_places=2)
    debit_turnover = models.DecimalField(max_digits=20, decimal_places=2)
    credit_turnover = models.DecimalField(max_digits=20, decimal_places=2)
    outgoing_active = models.DecimalField(max_digits=20, decimal_places=2)
    outgoing_passive = models.DecimalField(max_digits=20, decimal_places=2)

    def __str__(self):
        return f"{self.account}"


class UploadedFile(models.Model):
    file_name = models.CharField(max_length=255)
    upload_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file_name

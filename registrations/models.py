from django.db import models

class EmailRegistration(models.Model):
    email = models.EmailField(unique=True)
    registered_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email


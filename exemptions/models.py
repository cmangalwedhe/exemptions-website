from django.db import models


class StringsList(models.Model):
    value = models.CharField(max_length=255)


# Create your models here.
class Exemption(models.Model):
    identifier = models.IntegerField(unique=False)
    exempted_strings = models.ManyToManyField(StringsList, blank=True, related_name='exempted_models')
    available_exemptions = models.IntegerField(unique=False, default=0)
    exemptions_used = models.IntegerField(unique=False, default=0)


from django.db import models


class StringsList(models.Model):
    value = models.CharField(max_length=255)


class CourseList(models.Model):
    name = models.CharField(max_length=255)
    period = models.IntegerField(unique=False)


# Create your models here.
class Exemption(models.Model):
    identifier = models.CharField(max_length=6, unique=False)
    exempted_strings = models.ManyToManyField(CourseList, blank=True, related_name='exempted_models')
    available_exemptions = models.IntegerField(unique=False, default=0)
    exemptions_used = models.IntegerField(unique=False, default=0)


class Teacher(models.Model):
    identifier = models.CharField(unique=False, max_length=255)
    classes = models.ManyToManyField(CourseList, blank=True, related_name='classes')
    exempted_ids = models.ManyToManyField(StringsList, blank=True, related_name='exempted_students')
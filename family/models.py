from django.db import models

# Create your models here.

class FamilyInfo(models.Model):
    fam_num = models.PositiveIntegerField(default=1)

class FamilyEmptyTime(models.Model):
    family_id = models.ForeignKey(FamilyInfo, on_delete=models.CASCADE) 
    family_empty_date = models.DateField()
    family_empty_min = models.PositiveIntegerField()
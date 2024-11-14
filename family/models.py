from django.db import models

# Create your models here.

class FamilyInfo(models.Model):
    family_id = models.BigAutoField()
    fam_num = models.PositiveIntegerField(default=1)

class FamilyEmptyTime(models.Model):
    family_empty_id = models.BigAutoField()
    family = models.ForeignKey(FamilyInfo, on_delete=models.CASCADE) 
    family_empty_date = models.DateField()
    family_empty_min = models.PositiveIntegerField()
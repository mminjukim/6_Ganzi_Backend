from django.db import models

# Create your models here.

class Place(models.Model):
    place_id = models.BigAutoField(primary_key=True)
    place_name = models.CharField(max_length=50, verbose_name='제휴업체 이름')
    place_link = models.URLField(verbose_name='제휴업체 링크', max_length=500)
    place_img = models.ImageField(verbose_name='제휴업체 사진', null=True, blank=True, upload_to='place_img/%Y%m%d/')
    place_min_time = models.PositiveIntegerField(verbose_name='제휴업체 최소 이용시간(분)')

    def __str__(self):
        return self.place_name
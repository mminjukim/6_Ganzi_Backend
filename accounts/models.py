from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractUser, BaseUserManager
from family.models import FamilyInfo
from sch_requests.models import Category
from django.conf import settings

# Create your models here.
class UserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifiers
    for authentication instead of usernames.
    """

    def create_user(self, email, password, **extra_fields):
        """
        Create and save a User with the given email and password.
        """
        if not email:
            raise ValueError(_('The Email must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    user_id = models.BigAutoField(primary_key=True)
    username = None
    email = models.EmailField(unique=True, max_length=255)
    family = models.ForeignKey(FamilyInfo, on_delete=models.CASCADE, null=True)
    nickname = models.CharField(max_length=50, default="")
    profile_img=models.ImageField(upload_to='user_img/%Y%m%d/', blank=True, null=True, default='')
    profile_agreement = models.BooleanField(default=False, verbose_name='선택약관 동의 여부')
    kakao_access_token = models.CharField(max_length=255, blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email
    
class Badge(models.Model):
    badge_id = models.BigAutoField(primary_key=True)
    badge_name = models.CharField(max_length=20, default="")
    badge_condition = models.IntegerField(default=0)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True)


class AcquiredBadge(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    family = models.ForeignKey(FamilyInfo, on_delete=models.CASCADE)
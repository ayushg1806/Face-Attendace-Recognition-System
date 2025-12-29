from django.db import models
from django.contrib.auth.models import User

class EmployeeProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    employee_id = models.CharField(max_length=50, unique=True)
    face_image = models.ImageField(upload_to='faces/', null=True, blank=True)
    # store face encoding as text (json list)
    face_encoding = models.TextField(null=True, blank=True)
    department = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f'{self.user.get_full_name()} ({self.employee_id})'

class Attendance(models.Model):
    employee = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE)
    date = models.DateField()
    check_in_time = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=20, default='Present')

    class Meta:
        unique_together = ('employee', 'date')
        ordering = ['-date']

    def __str__(self):
        return f'{self.employee.employee_id} - {self.date} - {self.status}'

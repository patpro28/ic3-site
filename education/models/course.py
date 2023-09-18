from django.db import models

class Theory(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.title

class Course(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    theory = models.ForeignKey(Theory, related_name='courses', verbose_name='theory', on_delete=models.SET_NULL, null=True, blank=True)
    is_public = models.BooleanField(default=False)
    is_locked = models.BooleanField(default=True)
    logo = models.ImageField(upload_to='courses/logos/', null=True, blank=True)

    def __str__(self):
        return self.name
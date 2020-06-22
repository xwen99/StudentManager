from django.db import models

# Create your models here.

class Students(models.Model):
    Id = models.CharField(max_length=7, primary_key=True)
    Name = models.CharField(max_length=20)
    PasswordMd5 = models.CharField(max_length=32)
    Description = models.TextField()
    Majority = models.ForeignKey("Majorities", on_delete=models.CASCADE)


class Courses(models.Model):
    Id = models.CharField(max_length=7, primary_key=True)
    Name = models.CharField(max_length=20)
    Credit = models.IntegerField()
    Teacher = models.ForeignKey("Teachers", on_delete=models.CASCADE)
    StartDate = models.DateField()
    StartClass = models.IntegerField(max_length=1)
    EndClass = models.IntegerField(max_length=1)
    Times = models.IntegerField()
    Place = models.CharField(max_length=20)
    Description = models.TextField()


class Teachers(models.Model):
    Id = models.CharField(max_length=7, primary_key=True)
    Name = models.CharField(max_length=20)
    Collage = models.ForeignKey("Collages", on_delete=models.CASCADE)
    PasswordMd5 = models.CharField(max_length=32)
    Description = models.TextField()
    Super = models.BooleanField()


class Collages(models.Model):
    Id = models.CharField(max_length=7, primary_key=True)
    Name = models.CharField(max_length=20)


class Majorities(models.Model):
    Id = models.CharField(max_length=7, primary_key=True)
    Name = models.CharField(max_length=20)
    Collage = models.ForeignKey("Collages", on_delete=models.CASCADE)


class MajCse(models.Model):
    Majority = models.ForeignKey("Majorities", on_delete=models.CASCADE)
    Course = models.ForeignKey("Courses", on_delete=models.CASCADE)


class StuCse(models.Model):
    Student = models.ForeignKey("Students", on_delete=models.CASCADE)
    Course = models.ForeignKey("Courses", on_delete=models.CASCADE)
    Completed = models.BooleanField()
    Score = models.DecimalField(max_digits=4, decimal_places=1)

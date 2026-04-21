from django.db import models



class TermsCondition(models.Model):
    title = models.CharField(max_length=250)
    text = models.TextField()

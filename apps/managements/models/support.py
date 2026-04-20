from django.db import models


class SupportFile(models.Model):
    file = models.FileField(upload_to="sup_mes_files")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class SupportModel(models.Model):
    full_name = models.CharField(max_length=250)
    email = models.EmailField()    
    message = models.TextField()
    files = models.ManyToManyField(SupportFile, related_name="support_message_files" )
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        
        return f"{self.full_name}----{self.email}"

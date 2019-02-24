from django.db import models as m

class Complaint(m.Model):
    class Meta:
        verbose_name = "Complaint"
        verbose_name_plural = "Complaints"
  
    def __str__(self):
        super()

    id = m.AutoField(verbose_name="Complaint ID", primary_key=True)
    text = m.TextField(verbose_name="Complaint Text")
    state = m.IntegerField(verbose_name="State")
    category = m.CharField(verbose_name="Category" ,max_length = 10)
    instagram_post_id = m.CharField(verbose_name="Instagram Post ID", max_length = 35, null=True)
    instagram_comment_id = m.CharField(verbose_name="Instagram Comment ID", max_length = 20, null=True)
    created_at = m.DateTimeField(auto_now_add=True)
    updated_at = m.DateTimeField(auto_now=True)
    username = m.CharField(verbose_name="Instagram Username", max_length = 30, null=True)

    trello_id = m.CharField(verbose_name="Trello Card ID", max_length = 32, db_index=True, null=True)
    
    ready_at = m.DateTimeField(null=True)
    wip_at = m.DateTimeField(null=True)
    resolved_at = m.DateTimeField(null=True)

from django.db import models as m

class Log(m.Model):
    class Meta:
        verbose_name = "Log"
        verbose_name_plural = "Logs"
  
    def __str__(self):
        super()

    id = m.AutoField(verbose_name="Log ID", primary_key=True)

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
    post_id = m.CharField(verbose_name="Instagram Post ID", max_length = 35)
    comment_id = m.CharField(verbose_name="Instagram Post ID", max_length = 20)
    created_at = m.DateTimeField(auto_now_add=True)
    updated_at = m.DateTimeField(auto_now=True)

    ready_at = m.DateTimeField()
    wip_at = m.DateTimeField()
    resolved_at = m.DateTimeField()

from django.db import models

# Create your models here.

# mysql参数binlog_format=mixed，否则
# 报错：django.db.utils.InternalError: (1665, 'Cannot execute statement: impossible to write to binary log since BINLOG_FORMAT = STATEMENT
class User(models.Model):
    '''用户表'''
    username = models.CharField(max_length=32,unique=True)
    password = models.CharField(max_length=32)
    group = models.ManyToManyField("Group") #多对多
    is_admin = models.BooleanField(default=False)


    def __str__(self):
        return self.username

    class Meta:
        verbose_name ="用户"
        verbose_name_plural ="用户表"

class Group(models.Model):
    '''用户组'''
    groupname = models.CharField(max_length=32,unique=True)

    def __str__(self):
        return self.groupname

    class Meta:
        verbose_name ="用户组"
        verbose_name_plural ="用户组"
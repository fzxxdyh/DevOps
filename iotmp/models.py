from django.db import models

from account.models import User as account_User
# Create your models here.

class Version(models.Model):
    '''用户表'''
    name = models.CharField(max_length=100, unique=True)
    create_user = models.CharField(max_length=32, null=True, blank=True)
    create_time = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name ="用户表"
        verbose_name_plural ="用户表"

class Files(models.Model):
    '''文件表'''
    name = models.CharField(max_length=255, )
    upload_user = models.CharField(max_length=32, null=True, blank=True)
    mtime = models.DateTimeField() #修改时间
    md5 = models.CharField(max_length=50)
    version = models.ForeignKey("Version", on_delete=models.CASCADE, default=None)  #外键是在子表上加的

    def __str__(self):
        return self.name

    class Meta:
        verbose_name ="文件表"
        verbose_name_plural ="文件表"
        unique_together = ('name', 'version',) #联合唯一

class Host(models.Model):
    '''文件表'''
    ip = models.CharField(max_length=15, unique=True)
    port = models.IntegerField(null=False, default=22)
    user = models.CharField(max_length=20)
    passwd = models.CharField(max_length=100, null=True, blank=True, default="")
    keyfile = models.CharField(max_length=500, null=True, blank=True, default="")
    note = models.CharField(max_length=50)

    def __str__(self):
        return self.ip

    class Meta:
        verbose_name ="主机"
        verbose_name_plural ="主机"

# class HostGroup(models.Model):
#     '''文件表'''
#     name = models.CharField(max_length=255, null=True, default="")
#     mysql_ip = models.CharField(max_length=15, null=True, default="", unique=True)
#     redis_ip = models.CharField(max_length=15, null=True, default="")
#     zook_ip = models.CharField(max_length=15, null=True, default="")
#     activemq_ip = models.CharField(max_length=15, null=True, default="")
#     es_ip = models.CharField(max_length=15, null=True, default="")
#     flowhys_ip = models.CharField(max_length=15, null=True, default="")
#     log_ip = models.CharField(max_length=15, null=True, default="")
#
#
#     def __str__(self):
#         return self.mysql_ip
#
#     class Meta:
#         verbose_name ="主机组"
#         verbose_name_plural ="主机组"
#         #unique_together = ('mysql_ip', 'redis_ip', 'zook_ip', 'activemq_ip', 'es_ip', 'flowhys_ip' ,'log_ip')  # 联合唯一

class Server(models.Model):
    '''服务等级表'''
    name = models.CharField(max_length=100, unique=True)
    level = models.SmallIntegerField()
    install_script = models.CharField(max_length=50)
    check_type_choices = ((0, 'url'),(1, 'shell'))
    check_type = models.SmallIntegerField(choices=check_type_choices, default=0)
    check_exp = models.CharField(max_length=200, default="")
    port = models.IntegerField(default=-1)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name ="等级表"
        verbose_name_plural ="等级表"

'''
truncate table iotmp_server;

insert into iotmp_server(name, level, install_script, check_type, check_exp, port) 
values("jdk", 1, '01jdk.sh', 1, "java -version", -1);

insert into iotmp_server(name, level, install_script, check_type, check_exp, port) 
values("mysql", 1, '02mysql.sh', 1, "sudo netstat -nltp|grep {port}", 3306);

insert into iotmp_server(name, level, install_script, check_type, check_exp, port) 
values("redis", 1, '03redis.sh', 1, "sudo netstat -nltp|grep {port}", 6379);

insert into iotmp_server(name, level, install_script, check_type, check_exp, port) 
values("zookeeper", 1, '04zookeeper.sh', 1, "sudo netstat -nltp|grep {port}", 2181);

insert into iotmp_server(name, level, install_script, check_type, check_exp, port) 
values("activemq", 1, '05activemq.sh', 0, 'http://{ip}:8161', 8161);

insert into iotmp_server(name, level, install_script, check_type, check_exp, port) 
values("elasticsearch", 1, '06elasticsearch.sh', 0, 'http://{ip}:9200/_cluster/health?pretty', 9200);

insert into iotmp_server(name, level, install_script, check_type, check_exp, port) 
values("canal", 2, '07canal.sh', 1, "sudo netstat -nltp|grep {port}", 11111);

insert into iotmp_server(name, level, install_script, check_type, check_exp, port) 
values("systemsetting", 2, '12SystemSetting.sh', 0, 'http://{ip}:8905/platformConfig/', 8905);

insert into iotmp_server(name, level, install_script, check_type, check_exp, port) 
values("dataTransformer.configuration", 2, '13DataTransformerCfg.sh', 0, 'http://{ip}:8890/index.html', 8890);

insert into iotmp_server(name, level, install_script, check_type, check_exp, port) 
values("flowhys", 2, '15FlowHYS.sh', 0, 'http://{ip}:8088/FlowHYS/', 8088);

insert into iotmp_server(name, level, install_script, check_type, check_exp, port) 
values("flowengine", 2, '18FlowEngine.sh', 0, 'http://{ip}:7088/FlowEngine/html/check/showInfo.html', 7088);

insert into iotmp_server(name, level, install_script, check_type, check_exp, port) 
values("flowexecutor", 2, '19FlowExecutor.sh', 0, 'http://{ip}:9088/FlowExecutor/html/check/showInfo.html', 9088);

insert into iotmp_server(name, level, install_script, check_type, check_exp, port) 
values("datawatcher", 2, '20DataWatcher.sh', 0, 'http://{ip}:8866/DataWatcher/quickCheck/relateConnect', 8866);

insert into iotmp_server(name, level, install_script, check_type, check_exp, port) 
values("dblogstash", 2, '08dblogstash.sh', 1, "sudo netstat -nltp|grep {port}", 9600);

insert into iotmp_server(name, level, install_script, check_type, check_exp, port) 
values("logstash", 2, '09logstash.sh', 1, "sudo netstat -nltp|grep {port}", 5043);

insert into iotmp_server(name, level, install_script, check_type, check_exp, port) 
values("timejob", 2, '25TimeJob.sh', 0, 'http://{ip}:8011/swagger-ui.html', 8011);


insert into iotmp_server(name, level, install_script, check_type, check_exp, port) 
values("dbcascade", 2, '22DbCascade.sh', 0, 'http://{ip}:6688/DbCascade/quickCheck/relateConnect', 6688);


insert into iotmp_server(name, level, install_script, check_type, check_exp, port) 
values("datatransformer.service", 3, '14DataTransformer.sh', 0, 'http://{ip}:8899/invoke/sync', 8899);


insert into iotmp_server(name, level, install_script, check_type, check_exp, port) 
values("flowhysui", 3, '16FlowHYSUI.sh', 0, 'http://{ip}:9000/FlowHYS/', 9000);

insert into iotmp_server(name, level, install_script, check_type, check_exp, port) 
values("hyes", 3, '11HyEs.sh', 0, 'http://{ip}:12007', 12007);


insert into iotmp_server(name, level, install_script, check_type, check_exp, port) 
values("filebeat", 3, '10filebeat.sh', 1, 'sudo ps -aux |grep -i filebeat', -1);



insert into iotmp_server(name, level, install_script, check_type, check_exp, port) 
values("logcaselogstash", 3, '23logcaselogstash.sh', 1, 'sudo ps -ef|grep -i logcaselogstash', -1);


insert into iotmp_server(name, level, install_script, check_type, check_exp, port) 
values("inspectmanage", 3, '24InspectManage.sh', 0, 'http://{ip}:9155/execute/searchTask', 9155);


insert into iotmp_server(name, level, install_script, check_type, check_exp, port) 
values("flowlog", 4, '21FlowLog.sh', 0, 'http://{ip}:8044/swagger-ui.html', 8044);

commit;

select * from iotmp_server;

# 24条记录

'''


class Tasks(models.Model):
    '''服务等级表'''
    ctime = models.DateTimeField()  # 创建时间
    type_choices = ((0, '安装'),(1, '更新'))
    type = models.SmallIntegerField(choices=type_choices)
    ip = models.CharField(max_length=15)  #主机Ip，非mysql_ip
    version_name = models.CharField(max_length=100)
    file_name = models.CharField(max_length=255)
    server_name = models.CharField(max_length=50)
    level = models.SmallIntegerField()
    state_choices = ((0, '等待中'),(1, '进行中'), (2, '成功'), (-1, '失败'), )
    state = models.SmallIntegerField(choices=type_choices)
    logfile = models.CharField(max_length=100, default="")
    username = models.CharField(max_length=50, default="")

    def __str__(self):
        return self.ctime.strftime("%Y%m%d %H:%M:%S") + "---" + self.ip

    class Meta:
        verbose_name ="任务表"
        verbose_name_plural ="任务表"
        unique_together = ('ctime', 'ip', 'version_name', 'file_name')  # 联合唯一
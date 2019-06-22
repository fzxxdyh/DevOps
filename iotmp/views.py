from django.shortcuts import render, redirect, HttpResponse
from account import models as account_models
from . import models
from django.db import models as dj_models
from django.db.models import Q
from django.core.paginator import PageNotAnInteger, EmptyPage, Paginator
from . import admin
from threading import Thread
import datetime, time
from DevOps.settings import DATA_DIR, VERSION_DIR, HOST_DIR, HOSTGROUP_DIR, CONFIG_FILE, LOG_DIR, INSTALL_SCRIPT_DIR
import os
from iotmp import utils
import hashlib
import json
from iotmp import myconfigparser as configparser
from shutil import copyfile
import threading
from django.utils.safestring import mark_safe
from account.views import login_auth

@login_auth
def index(request):
    _username = request.session.get('_username', None) #即使后面不加None，找不到也会返回默认None
    try:
        user = account_models.User.objects.get(username=_username) #查不到会报jenkins.models.DoesNotExist异常
    except account_models.User.DoesNotExist:
        # print('用户不存在！')
        return redirect('/account/login/')
    return render(request, 'iotmp/index.html',{
        'username': _username,
    })

@login_auth
def version(request):
    _username = request.session.get('_username', None)  # 即使后面不加None，找不到也会返回默认None
    rows = models.Version.objects.all().order_by("id")
    paginator = Paginator(rows, 50)  # 每页20条
    current_page = request.GET.get('_page')  # 找不到就为None,触发后面PageNotAnInteger异常
    try:
        query_sets = paginator.page(current_page)
    except PageNotAnInteger:  # 如果page为None，就会触发这个异常
        # If page is not an integer, deliver first page.
        query_sets = paginator.page(1)  # 第一页
    except EmptyPage:  # 大于paginator.num_pages或者小于1
        # If page is out of range (e.g. 9999), deliver last page of results.
        # query_sets = paginator.page(paginator.num_pages)  #最后一页
        query_sets = paginator.page(1)  # 全部定到第一页
    return render(request, 'iotmp/version_list.html',{
        'username': _username,
        'query_sets': query_sets,

    })

@login_auth
def version_new(request):
    _username = request.session.get('_username', None)
    if request.method == "POST":#新建版本库
        model_class = getattr(models, 'Version')
        fields_set = model_class._meta.get_fields()
        instance_obj = model_class() #这种方式创建的实例，不管字段是为非空，都可以成功，但如果没有instance_obj.save()前，使用ManyToMany字段时会报错
        # instance_obj = model_class.objects.create() #这种方式创建的实例，可以使用ManyToMany字段，但在建表创建非空字段时，不能设置default=None，否则此处报错
        for key, value in request.POST.items():#如果key对应的是一个列表，这样得到的value只是列表中的一个元素
            if value and key != "csrfmiddlewaretoken":
                for field in fields_set:
                    if field.name == key:#就是这个字段
                        if type(field) in [dj_models.OneToOneField, dj_models.ForeignKey]:
                            #print(field.name, type(field))
                            rel_model = field.related_model
                            rel_instances = rel_model.objects.get(id=value)
                            setattr(instance_obj, key, rel_instances)
                        elif type(field) == dj_models.ManyToManyField:
                            # 非常重要
                            instance_obj.save()  # 一定要先保存一下，否则getattr(instance_obj, key)会报错

                            mtm_obj = getattr(instance_obj, key) # 得到多对多的字段对象
                            value_list = request.POST.getlist(key)  # 这样才能得到列表全部数据
                            rel_model = field.related_model
                            for id in value_list:
                                rel_instances = rel_model.objects.get(id=id)
                                mtm_obj.add(rel_instances)  #如果已有，不会重复添加
                        elif type(field) in [dj_models.IntegerField, dj_models.BigIntegerField, dj_models.FloatField, dj_models.SmallIntegerField,]:
                            value = float(value)
                            setattr(instance_obj, key, value)
                        else:#其他字段类型
                            setattr(instance_obj, key, value)
        # 保存之前调用处理函数
        instance_obj.create_user = _username
        instance_obj.create_time = datetime.datetime.now()
        instance_obj.save()

        folder = os.path.join(VERSION_DIR, instance_obj.name)
        if not os.path.exists(folder):
            try:
                os.makedirs(folder)  # 如果不存在，会递归创建
            except Exception as e:
                print("ERROR, in version_new: " , e)
                instance_obj.delete()
                return HttpResponse("ERROR: %s" % e)

        return redirect('/iotmp/version/' )
    return render(request, 'iotmp/version_new.html',{
        'username': _username,
        'model_name': 'Version',

    })

@login_auth
def version_del(request, id):
    _username = request.session.get('_username', None)
    model_class = getattr(models, 'Version')
    instance_obj = model_class.objects.get(id=id)
    if request.method == "POST": #删除版本库
        folder = os.path.join(VERSION_DIR, instance_obj.name)
        utils.rmdir_all(folder)
        instance_obj.delete()

        return redirect('/iotmp/version/')

    return render(request, 'iotmp/version_del.html',{
        'username': _username,
        'model_name':'Version',
        'instance_obj':instance_obj,
    })

@login_auth
def version_files(request, id):
    _username = request.session.get('_username', None)  # 即使后面不加None，找不到也会返回默认None
    version_obj = models.Version.objects.get(id=id)
    if request.method == "POST":#上传文件
        file_list = request.FILES.getlist('file_list')
        for file in file_list:
            files_obj = models.Files.objects.filter(name=file.name, version=version_obj)
            if files_obj:
                files_obj.delete() #如果有多个，会一起删除， 不能用 del files_obj

            if not os.path.isdir( os.path.join(VERSION_DIR, version_obj.name) ):
                os.makedirs(os.path.join(VERSION_DIR, version_obj.name))  # 如果不存在，会递归创建
            server_file = os.path.join(VERSION_DIR, version_obj.name, file.name)
            md5_obj = hashlib.md5()
            f = open(server_file, 'wb')
            for chunk in file.chunks():
                f.write(chunk)
                md5_obj.update(chunk)
            f.close()
            hash_code = md5_obj.hexdigest()
            md5_value = str(hash_code).lower()
            timestamp = os.path.getmtime(server_file) #时间戮
            mtime = utils.TimeStampToTime(timestamp)

            files_obj = models.Files(name=file.name, upload_user=_username, mtime=mtime, md5=md5_value, version=version_obj)
            files_obj.save()

        return HttpResponse("文件上传完成！")

    rows = version_obj.files_set.all().order_by("id") #不加order by 会出现警告，说Paginator获得的数据顺序可能不是一致性的
    paginator = Paginator(rows, 50)  # 每页20条
    current_page = request.GET.get('_page')  # 找不到就为None,触发后面PageNotAnInteger异常
    try:
        query_sets = paginator.page(current_page)
    except PageNotAnInteger:  # 如果page为None，就会触发这个异常
        # If page is not an integer, deliver first page.
        query_sets = paginator.page(1)  # 第一页
    except EmptyPage:  # 大于paginator.num_pages或者小于1
        # If page is out of range (e.g. 9999), deliver last page of results.
        # query_sets = paginator.page(paginator.num_pages)  #最后一页
        query_sets = paginator.page(1)  # 全部定到第一页
    return render(request, 'iotmp/version_files.html',{
        'username': _username,
        'query_sets': query_sets,
        'version_name': version_obj.name,
    })

@login_auth
def version_delfile(request, id, fid):
    _username = request.session.get('_username', None)
    version_obj = models.Version.objects.get(id=id)
    file_obj = models.Files.objects.get(id=fid)
    if request.method == "POST":
        file_obj.delete()
        return redirect("/iotmp/version/files/%d/" % version_obj.id)
    return render(request, 'iotmp/version_delfile.html', {
        'username': _username,
        'version_name': version_obj.name,
        'version_id': version_obj.id,
        'file_name': file_obj.name,
    })

@login_auth
def host_new(request):
    _username = request.session.get('_username', None)
    if request.method == "POST":#新建主机
        err_msg = ""
        ip = request.POST.get("ip").strip() #找不到不会报错，返回None
        port = request.POST.get("port").strip()
        user = request.POST.get("user").strip()
        passwd = request.POST.get("passwd")
        note = request.POST.get("note")
        file_obj = request.FILES.get("keyfile")

        host = models.Host.objects.filter(ip=ip)
        if not utils.check_ip_addr(ip):
            err_msg = "ip地址[%s]不合法！" % ip
        elif host:
            err_msg = "主机[%s]已存在！" % ip
        elif not passwd and not file_obj:
            err_msg = "密码和证书不能都为空！"


        if err_msg:
            return render(request, 'iotmp/err_msg.html', {
                'username': _username,
                'err_msg': err_msg,
            })

        host_folder = os.path.join(HOST_DIR, ip)
        if not os.path.exists(host_folder):
            os.makedirs(host_folder)  # 如果不存在，会递归创建

        if file_obj:
            file_path = os.path.join(host_folder, file_obj.name)
            f = open(file_path, 'wb')
            for chunk in file_obj.chunks():
                f.write(chunk)
            f.close()
            host = models.Host(ip=ip, port=port, user=user, passwd=utils.get_encrypt_value(passwd),keyfile=file_path,
                               note=note)
        else:
            host = models.Host(ip=ip, port=port, user=user, passwd=utils.get_encrypt_value(passwd),
                               keyfile=None,
                               note=note)
        host.save()
        return redirect('/iotmp/host/')

    return render(request, 'iotmp/host_new.html',{
        'username': _username,
        'model_name': 'Host',

    })

@login_auth
def host_del(request, id):
    _username = request.session.get('_username', None)
    model_class = getattr(models, 'Host')
    instance_obj = model_class.objects.get(id=id)
    if request.method == "POST": #删除主机
        folder = os.path.join(HOST_DIR, instance_obj.ip)
        utils.rmdir_all(folder)
        instance_obj.delete()

        return redirect('/iotmp/host/')

    return render(request, 'iotmp/host_del.html',{
        'username': _username,
        'model_name':'Host',
        'instance_obj':instance_obj,
    })

@login_auth
def host(request):
    _username = request.session.get('_username', None)  # 即使后面不加None，找不到也会返回默认None
    rows = models.Host.objects.all().order_by("id")
    paginator = Paginator(rows, 5)  # 每页20条
    current_page = request.GET.get('_page')  # 找不到就为None,触发后面PageNotAnInteger异常
    try:
        query_sets = paginator.page(current_page)
    except PageNotAnInteger:  # 如果page为None，就会触发这个异常
        # If page is not an integer, deliver first page.
        query_sets = paginator.page(1)  # 第一页
    except EmptyPage:  # 大于paginator.num_pages或者小于1
        # If page is out of range (e.g. 9999), deliver last page of results.
        # query_sets = paginator.page(paginator.num_pages)  #最后一页
        query_sets = paginator.page(1)  # 全部定到第一页
    return render(request, 'iotmp/host_list.html',{
        'username': _username,
        'query_sets': query_sets,

    })


@login_auth
def hostgroup_new(request):
    _username = request.session.get('_username', None)
    if request.method == "POST":#新建主机组
        err_msg = ""
        dic = {}
        #print(request.POST)
        for key, value in request.POST.items():
            if key != "csrfmiddlewaretoken":
                dic[key] = value

        hostgroup_folder = os.path.join(HOSTGROUP_DIR, dic['mysql_ip'])
        if os.path.isdir(hostgroup_folder):
            err_msg = "主机组[%s]已存在！" %  dic['mysql_ip']
        else:
            for key, value in dic.items():
                if not utils.check_ip_addr(value):
                    err_msg = "ip地址[%s]不合法！" % value

        if err_msg:
            return render(request, 'iotmp/err_msg.html', {
                'username': _username,
                'err_msg': err_msg,
            })



        os.makedirs(hostgroup_folder)  # 如果不存在，会递归创建

        source = os.path.join(INSTALL_SCRIPT_DIR, CONFIG_FILE)
        target = os.path.join(HOSTGROUP_DIR, dic['mysql_ip'], CONFIG_FILE)
        copyfile(source, target)  #拷贝这个文件，仅在主机组视图中用到：/iotmp/hostgroup/

        conf_file = os.path.join(HOSTGROUP_DIR, dic["mysql_ip"], CONFIG_FILE)
        conf_obj = configparser.ConfigParser()
        conf_obj.read(conf_file, encoding="utf-8")

        for key, value in dic.items():
            conf_obj.set("config", key.upper(), value)


        f = open(conf_file, "w", encoding="utf-8")
        conf_obj.write(f)
        f.close()



        return redirect('/iotmp/hostgroup/')

    return render(request, 'iotmp/hostgroup_new.html',{
        'username': _username,
        'model_name': 'HostGroup',

    })

@login_auth
def hostgroup_del(request, mysql_ip):
    #print("hostgroup del....")
    _username = request.session.get('_username', None)
    if request.method == "POST": #删除主机组
        folder = os.path.join(HOSTGROUP_DIR, mysql_ip)
        utils.rmdir_all(folder)
        return redirect('/iotmp/hostgroup/')

    return render(request, 'iotmp/hostgroup_del.html',{
        'username': _username,
        'mysql_ip': mysql_ip,
    })

@login_auth
def hostgroup(request):
    _username = request.session.get('_username', None)  # 即使后面不加None，找不到也会返回默认None
    rows = []
    name = os.listdir(HOSTGROUP_DIR)
    for folder_name in name:
        if os.path.isdir(  os.path.join(HOSTGROUP_DIR, folder_name)  ):
            rows.append(folder_name)

    #rows = models.HostGroup.objects.all().order_by("id")
    paginator = Paginator(rows, 5)  # 每页20条
    current_page = request.GET.get('_page')  # 找不到就为None,触发后面PageNotAnInteger异常
    try:
        query_sets = paginator.page(current_page)
    except PageNotAnInteger:  # 如果page为None，就会触发这个异常
        # If page is not an integer, deliver first page.
        query_sets = paginator.page(1)  # 第一页
    except EmptyPage:  # 大于paginator.num_pages或者小于1
        # If page is out of range (e.g. 9999), deliver last page of results.
        # query_sets = paginator.page(paginator.num_pages)  #最后一页
        query_sets = paginator.page(1)  # 全部定到第一页
    return render(request, 'iotmp/hostgroup_list.html',{
        'username': _username,
        'query_sets': query_sets,

    })

@login_auth
def install(request):
    _username = request.session.get('_username', None)  # 即使后面不加None，找不到也会返回默认None

    if request.method == "POST":# 页面点击一键部署
        mysql_ip = request.POST.get("mysql_ip")
        redis_ip = request.POST.get("redis_ip")
        zook_ip = request.POST.get("zook_ip")
        activemq_ip = request.POST.get("activemq_ip")
        es_ip = request.POST.get("es_ip")
        flowhys_ip = request.POST.get("flowhys_ip")
        log_ip = request.POST.get("log_ip")
        es_jvm = request.POST.get("es_jvm")
        log_jvm = request.POST.get("log_jvm")
        dblog_jvm = request.POST.get("dblog_jvm")
        logcs_jvm = request.POST.get("logcs_jvm")


        ctime = datetime.datetime.now()
        G1_FILE = request.POST.getlist("G1_FILE")
        G2_FILE = request.POST.getlist("G2_FILE")
        G3_FILE = request.POST.getlist("G3_FILE")
        G1_IP = request.POST.get("G1_IP")
        G2_IP = request.POST.get("G2_IP")
        G3_IP = request.POST.get("G3_IP")
        if G1_FILE and G1_IP:
            #print("G1_FILE, Len(g1_file)", G1_FILE, len(G1_FILE))
            utils.save_config(local_ip=G1_IP, mysql_ip=mysql_ip, redis_ip=redis_ip, zook_ip=zook_ip, activemq_ip=activemq_ip,
                              es_ip=es_ip,
                              flowhys_ip=flowhys_ip, log_ip=log_ip, es_jvm=es_jvm, log_jvm=log_jvm, dblog_jvm=dblog_jvm,
                              logcs_jvm=logcs_jvm)
            for file in G1_FILE:
                #print("G1 FILE:", file)
                version_name, file_name = file.split(">")
                server_name, level = utils.file_map_server(file_name)
                #print("server_name:", server_name)
                if server_name.lower() == "mysql":
                    continue

                logfile = '{ip}_{ctime}_{server_name}.log'.format(ip=G1_IP, ctime=ctime.strftime("%Y%m%d_%H%M%S_%f"),
                                                                  server_name=server_name)
                task = models.Tasks(ctime=ctime, type=0, ip=G1_IP, version_name=version_name,file_name=file_name,
                                    server_name=server_name, level=level, state=0, logfile=logfile, username=_username
                                    )
                task.save()
        if G2_FILE and G2_IP:
            #print("G2_FILE, Len(g2_file)", G2_FILE, len(G2_FILE))
            utils.save_config(local_ip=G2_IP, mysql_ip=mysql_ip, redis_ip=redis_ip, zook_ip=zook_ip,
                              activemq_ip=activemq_ip,
                              es_ip=es_ip,
                              flowhys_ip=flowhys_ip, log_ip=log_ip, es_jvm=es_jvm, log_jvm=log_jvm, dblog_jvm=dblog_jvm,
                              logcs_jvm=logcs_jvm)
            for file in G2_FILE:
                #print("G2 FILE:", file)
                version_name, file_name = file.split(">")
                server_name, level = utils.file_map_server(file_name)
                #print("server_name:", server_name)
                if server_name.lower() == "mysql":
                    continue
                logfile = '{ip}_{ctime}_{server_name}.log'.format(ip=G2_IP, ctime=ctime.strftime("%Y%m%d_%H%M%S_%f"),
                                                                  server_name=server_name)
                task = models.Tasks(ctime=ctime, type=0, ip=G2_IP, version_name=version_name, file_name=file_name,
                                    server_name=server_name, level=level, state=0, logfile=logfile, username=_username
                                    )
                task.save()
        if G3_FILE and G3_IP:
            #print("G3_FILE, Len(g3_file)", G3_FILE, len(G3_FILE))
            utils.save_config(local_ip=G3_IP, mysql_ip=mysql_ip, redis_ip=redis_ip, zook_ip=zook_ip,
                              activemq_ip=activemq_ip,
                              es_ip=es_ip,
                              flowhys_ip=flowhys_ip, log_ip=log_ip, es_jvm=es_jvm, log_jvm=log_jvm, dblog_jvm=dblog_jvm,
                              logcs_jvm=logcs_jvm)

            for file in G3_FILE:
                #print("G3 FILE:", file)
                version_name, file_name = file.split(">")
                server_name, level = utils.file_map_server(file_name)
                #print("server_name:", server_name)
                if server_name.lower() == "mysql":
                    continue
                logfile = '{ip}_{ctime}_{server_name}.log'.format(ip=G3_IP, ctime=ctime.strftime("%Y%m%d_%H%M%S_%f"),
                                                                  server_name=server_name)
                task = models.Tasks(ctime=ctime, type=0, ip=G3_IP, version_name=version_name, file_name=file_name,
                                    server_name=server_name, level=level, state=0, logfile=logfile, username=_username
                                    )
                task.save()



        thread = threading.Thread(target=utils.exec_install, args=(ctime,mysql_ip))
        thread.start()


        return redirect("/iotmp/tasks/run/")


    return render(request, 'iotmp/install.html',{
        'username': _username,
    })

@login_auth
def server_info(request):
    _username = request.session.get('_username', None)  # 即使后面不加None，找不到也会返回默认None
    rows = models.Tasks.objects.filter(state=2).values("ip").distinct().order_by("ip") # ip去重复
    paginator = Paginator(rows, 5)  # 每页20条
    current_page = request.GET.get('_page')  # 找不到就为None,触发后面PageNotAnInteger异常
    try:
        query_sets = paginator.page(current_page)
    except PageNotAnInteger:  # 如果page为None，就会触发这个异常
        # If page is not an integer, deliver first page.
        query_sets = paginator.page(1)  # 第一页
    except EmptyPage:  # 大于paginator.num_pages或者小于1
        # If page is out of range (e.g. 9999), deliver last page of results.
        # query_sets = paginator.page(paginator.num_pages)  #最后一页
        query_sets = paginator.page(1)  # 全部定到第一页
    return render(request, 'iotmp/server_info.html',{
        'username': _username,
        'query_sets': query_sets,

    })

@login_auth
def server_info_del(request, ip):
    _username = request.session.get('_username', None)
    tasks_queryset = models.Tasks.objects.filter(ip=ip)
    if request.method == "POST": #删除主机
        tasks_queryset.delete()  #删除所有
        return redirect('/iotmp/server/info/')

    return render(request, 'iotmp/server_info_del.html',{
        'username': _username,
        'ip': ip,

    })

@login_auth
def server_host_del(request, ip, server_name):
    _username = request.session.get('_username', None)
    tasks_queryset = models.Tasks.objects.filter(ip=ip, server_name=server_name)
    if request.method == "POST": #删除主机
        tasks_queryset.delete()  #删除所有
        return redirect('/iotmp/server/info/%s/' % ip )

    return render(request, 'iotmp/server_host_del.html',{
        'username': _username,
        'ip': ip,
        'server_name': server_name,

    })

@login_auth
def server_host(request, host_ip):
    _username = request.session.get('_username', None)  # 即使后面不加None，找不到也会返回默认None
    rows = models.Tasks.objects.filter(ip=host_ip, state=2).values("server_name").distinct().order_by("server_name") # 去重复
    #返回结果：<QuerySet [{'server_name': 'redis'}, {'server_name': 'jdk'}, {'server_name': 'flowhysui'}, {'server_name': 'systemsetting'}]>

    paginator = Paginator(rows, 50)  # 每页20条
    current_page = request.GET.get('_page')  # 找不到就为None,触发后面PageNotAnInteger异常
    try:
        query_sets = paginator.page(current_page)
    except PageNotAnInteger:  # 如果page为None，就会触发这个异常
        # If page is not an integer, deliver first page.
        query_sets = paginator.page(1)  # 第一页
    except EmptyPage:  # 大于paginator.num_pages或者小于1
        # If page is out of range (e.g. 9999), deliver last page of results.
        # query_sets = paginator.page(paginator.num_pages)  #最后一页
        query_sets = paginator.page(1)  # 全部定到第一页
    return render(request, 'iotmp/server_host.html',{
        'username': _username,
        'query_sets': query_sets,
        'host_ip': host_ip,

    })


@login_auth
def server_check(request, ip, server_name):
    _username = request.session.get('_username', None)
    server = models.Server.objects.get(name=server_name)
    result = ''
    if server.port != -1:#有port
        server_port = int(server.port)
        cmd = server.check_exp.format(port=server_port)
    else: #没有port
        cmd = server.check_exp

    host = models.Host.objects.get(ip=ip)
    ssh = utils.get_ssh(host.ip, host.user, port=host.port, passwd=utils.get_decode_value(host.passwd), key_file=host.keyfile)
    stdin, stdout, stderr = ssh.exec_command(cmd)
    for line in stdout:
        result += line + '<br/>'

    for line in stderr:
        result += line + '<br/>'

    ssh.close()

    return render(request, 'iotmp/server_check.html', {
        'username': _username,
        'result': mark_safe(result),
        'cmd': cmd,
    })

@login_auth
def tasks_log(request, id):
    _username = request.session.get('_username', None)
    task = models.Tasks.objects.get(id=id)

    if task.state == 0:
        return HttpResponse("此任务未开始，烦请等待。")
    else:
        file_path = os.path.join(LOG_DIR, task.ip, task.logfile)
        return render(request, 'iotmp/tasks_log.html', {
            'username': _username,
            'file_path':file_path,
        })




@login_auth
def tasks(request):
    _username = request.session.get('_username', None)

    rows = models.Tasks.objects.all().order_by("-id")
    paginator = Paginator(rows, 50)  # 每页20条
    current_page = request.GET.get('_page')  # 找不到就为None,触发后面PageNotAnInteger异常
    try:
        query_sets = paginator.page(current_page)
    except PageNotAnInteger:  # 如果page为None，就会触发这个异常
        # If page is not an integer, deliver first page.
        query_sets = paginator.page(1)  # 第一页
    except EmptyPage:  # 大于paginator.num_pages或者小于1
        # If page is out of range (e.g. 9999), deliver last page of results.
        # query_sets = paginator.page(paginator.num_pages)  #最后一页
        query_sets = paginator.page(1)  # 全部定到第一页

    return render(request, 'iotmp/tasks.html',{
        'username': _username,
        'query_sets':query_sets,
    })

@login_auth
def tasks_run(request):
    _username = request.session.get('_username', None)

    rows = models.Tasks.objects.filter(Q(state=0) | Q (state=1)).order_by("-id")
    paginator = Paginator(rows, 50)  # 每页20条
    current_page = request.GET.get('_page')  # 找不到就为None,触发后面PageNotAnInteger异常
    try:
        query_sets = paginator.page(current_page)
    except PageNotAnInteger:  # 如果page为None，就会触发这个异常
        # If page is not an integer, deliver first page.
        query_sets = paginator.page(1)  # 第一页
    except EmptyPage:  # 大于paginator.num_pages或者小于1
        # If page is out of range (e.g. 9999), deliver last page of results.
        # query_sets = paginator.page(paginator.num_pages)  #最后一页
        query_sets = paginator.page(1)  # 全部定到第一页

    return render(request, 'iotmp/tasks.html',{
        'username': _username,
        'query_sets':query_sets,
    })

@login_auth
def tasks_success(request):
    _username = request.session.get('_username', None)

    rows = models.Tasks.objects.filter(state=2).order_by("-id")
    paginator = Paginator(rows, 50)  # 每页20条
    current_page = request.GET.get('_page')  # 找不到就为None,触发后面PageNotAnInteger异常
    try:
        query_sets = paginator.page(current_page)
    except PageNotAnInteger:  # 如果page为None，就会触发这个异常
        # If page is not an integer, deliver first page.
        query_sets = paginator.page(1)  # 第一页
    except EmptyPage:  # 大于paginator.num_pages或者小于1
        # If page is out of range (e.g. 9999), deliver last page of results.
        # query_sets = paginator.page(paginator.num_pages)  #最后一页
        query_sets = paginator.page(1)  # 全部定到第一页

    return render(request, 'iotmp/tasks_success.html',{
        'username': _username,
        'query_sets':query_sets,
    })

@login_auth
def tasks_failed(request):
    _username = request.session.get('_username', None)

    rows = models.Tasks.objects.filter(state=-1).order_by("-id")
    paginator = Paginator(rows, 50)  # 每页20条
    current_page = request.GET.get('_page')  # 找不到就为None,触发后面PageNotAnInteger异常
    try:
        query_sets = paginator.page(current_page)
    except PageNotAnInteger:  # 如果page为None，就会触发这个异常
        # If page is not an integer, deliver first page.
        query_sets = paginator.page(1)  # 第一页
    except EmptyPage:  # 大于paginator.num_pages或者小于1
        # If page is out of range (e.g. 9999), deliver last page of results.
        # query_sets = paginator.page(paginator.num_pages)  #最后一页
        query_sets = paginator.page(1)  # 全部定到第一页

    return render(request, 'iotmp/tasks.html',{
        'username': _username,
        'query_sets':query_sets,
    })

@login_auth
def tasks_del(request, id):
    _username = request.session.get('_username', None)
    model_class = getattr(models, 'Tasks')
    instance_obj = model_class.objects.get(id=id)
    if request.method == "POST": #删除任务
        instance_obj.delete()
        logfile = os.path.join(LOG_DIR, instance_obj.logfile)
        if os.path.isfile(logfile):
            #print("in tasks_del,删除文件" , logfile)
            os.remove(logfile)
        return redirect('/iotmp/')

    return render(request, 'iotmp/tasks_del.html',{
        'username': _username,
        'model_name':'Tasks',
        'instance_obj':instance_obj,
    })

@login_auth
def select_env(request, mysql_ip):
    _username = request.session.get('_username', None)  # 即使后面不加None，找不到也会返回默认None
    dic = {}
    if mysql_ip:# ajax发过来的查询
        config_file = os.path.join(HOSTGROUP_DIR, mysql_ip, CONFIG_FILE)
        if os.path.isfile(config_file):
            conf_obj = configparser.ConfigParser()
            conf_obj.read(config_file, encoding="utf-8")

            mysql_ip = conf_obj.get('config', "MYSQL_IP")
            redis_ip = conf_obj.get('config', "REDIS_IP")
            zook_ip = conf_obj.get('config', "ZOOK_IP")
            activemq_ip = conf_obj.get('config', "ACTIVEMQ_IP")
            es_ip = conf_obj.get('config', "ES_IP")
            flowhys_ip = conf_obj.get('config', "FLOWHYS_IP")
            log_ip = conf_obj.get('config', "LOG_IP")
            # conf_obj.set("config", "MYSQL_IP", "1.1.1.1")
            # conf_obj.set("config", "ES_JVM", "900M")
            # conf_obj.write(open(conf_file, "w"))

            dic["mysql_ip"] = mysql_ip
            dic["redis_ip"] = redis_ip
            dic["zook_ip"] = zook_ip
            dic["activemq_ip"] = activemq_ip
            dic["es_ip"] = es_ip
            dic["flowhys_ip"] = flowhys_ip
            dic["log_ip"] = log_ip

    return HttpResponse(json.dumps(dic), content_type="application/json")


##增、删、改、查
@login_auth
def new_obj(request, model_name):
    _username = request.session.get('_username', None)
    if request.method == "POST":#新建记录
        #print('post-->', request.POST, type(request.POST))
        model_class = getattr(models, model_name)
        fields_set = model_class._meta.get_fields()
        instance_obj = model_class() #这种方式创建的实例，不管字段是为非空，都可以成功，但如果没有instance_obj.save()前，使用ManyToMany字段时会报错
        # instance_obj = model_class.objects.create() #这种方式创建的实例，可以使用ManyToMany字段，但在建表创建非空字段时，不能设置default=None，否则此处报错
        for key, value in request.POST.items():#如果key对应的是一个列表，这样得到的value只是列表中的一个元素
            if value and key != "csrfmiddlewaretoken":
                for field in fields_set:
                    if field.name == key:#就是这个字段
                        if type(field) in [dj_models.OneToOneField, dj_models.ForeignKey]:
                            #print(field.name, type(field))
                            rel_model = field.related_model
                            rel_instances = rel_model.objects.get(id=value)
                            setattr(instance_obj, key, rel_instances)
                        elif type(field) == dj_models.ManyToManyField:

                            # 非常重要
                            instance_obj.save()  # 一定要先保存一下，否则getattr(instance_obj, key)会报错


                            mtm_obj = getattr(instance_obj, key) # 得到多对多的字段对象
                            value_list = request.POST.getlist(key)  # 这样才能得到列表全部数据
                            rel_model = field.related_model
                            for id in value_list:
                                rel_instances = rel_model.objects.get(id=id)
                                mtm_obj.add(rel_instances)  #如果已有，不会重复添加
                        elif type(field) in [dj_models.IntegerField, dj_models.BigIntegerField, dj_models.FloatField, dj_models.SmallIntegerField,]:
                            value = float(value)
                            setattr(instance_obj, key, value)

                        else:#其他字段类型
                            setattr(instance_obj, key, value)
        # 保存之前调用处理函数
        before_save_func = getattr(admin, 'new_%s_before_save' % model_name)
        if model_name == "Version":
            before_save_func(instance_obj, _username)
        instance_obj.save()

        return redirect('/iotmp/select/%s/' % model_name)
    return render(request, 'iotmp/new_obj.html',{
        'username': _username,
        'model_name':model_name,
    })

@login_auth
def del_obj(request, model_name, obj_id):
    _username = request.session.get('_username', None)
    model_class = getattr(models, model_name)
    instance_obj = model_class.objects.get(id=obj_id)
    if request.method == "POST":
        instance_obj.delete()
        return redirect('/monitor/select/%s/' % model_name)

    return render(request, 'monitor/del_obj.html',{
        'username': _username,
        'model_name':model_name,
        'instance_obj':instance_obj,
    })

@login_auth
def update_obj(request, model_name, obj_id):
    _username = request.session.get('_username', None)
    model_class = getattr(models, model_name)
    instance_obj = model_class.objects.get(id=obj_id)
    if request.method == "POST":#更新记录
        #print('post-->', request.POST, type(request.POST))
        fields_set = model_class._meta.get_fields()
        # instance_obj = model_class() #这种方式创建的实例，当使用ManyToMany字段时会报错
        # instance_obj = model_class.objects.create() #这种方式创建的实例，可以使用ManyToMany字段，但在建表创建非空字段时，不能设置default=None，否则此处报错
        for key, value in request.POST.items():#如果key对应的是一个列表，这样得到的value只是列表中的一个元素
            if value and key != "csrfmiddlewaretoken":
                for field in fields_set:
                    if field.name == key:#就是这个字段
                        if type(field) in [dj_models.OneToOneField, dj_models.ForeignKey]:
                            rel_model = field.related_model
                            rel_instances = rel_model.objects.get(id=value)
                            setattr(instance_obj, key, rel_instances)
                        elif type(field) == dj_models.ManyToManyField:
                            mtm_obj = getattr(instance_obj, key) # 得到多对多的字段对象
                            for rel_obj in mtm_obj.all(): #先清空，这是唯一和new_obj不同的地方
                                mtm_obj.remove(rel_obj)
                            value_list = request.POST.getlist(key)  # 这样才能得到列表全部数据
                            rel_model = field.related_model
                            for id in value_list:
                                rel_instances = rel_model.objects.get(id=id)
                                mtm_obj.add(rel_instances)  #如果已有，不会重复添加
                        elif type(field) in [dj_models.IntegerField, dj_models.BigIntegerField, dj_models.FloatField, dj_models.SmallIntegerField,]:
                            value = float(value)
                            setattr(instance_obj, key, value)

                        else:#其他字段类型
                            setattr(instance_obj, key, value)
        instance_obj.save()


        return redirect('/monitor/select/%s/' % model_name)
    return render(request, 'monitor/update_obj.html',{
        'username': _username,
        'model_name':model_name,
        'instance_obj': instance_obj,

    })

@login_auth
def select_model(request, model_name):
    _username = request.session.get('_username', None)
    if request.method == "POST":#刷新脚本状态
        thread_list = []
        for script in models.Script.objects.all():
            t = Thread(target=ssh_cmd, args=(script,) )#优先使用证书连接
            t.start()
            thread_list.append(t)
        for t in thread_list:
            t.join() #等待所有线程结束
        return redirect('/monitor/select/Script/') #如果不重定向，页面点刷新永远是POST

    model_class = getattr(models, model_name)
    rows = model_class.objects.all().order_by("id")
    paginator = Paginator(rows, 5)  # 每页20条
    current_page = request.GET.get('_page')  # 找不到就为None,触发后面PageNotAnInteger异常
    try:
        query_sets = paginator.page(current_page)
    except PageNotAnInteger:  # 如果page为None，就会触发这个异常
        # If page is not an integer, deliver first page.
        query_sets = paginator.page(1)  # 第一页
    except EmptyPage:  # 大于paginator.num_pages或者小于1
        # If page is out of range (e.g. 9999), deliver last page of results.
        # query_sets = paginator.page(paginator.num_pages)  #最后一页
        query_sets = paginator.page(1)  # 全部定到第一页

    return render(request, 'iotmp/select_model.html', {
        'username': _username,
        'model_name':model_name,
        'query_sets':query_sets,
    })
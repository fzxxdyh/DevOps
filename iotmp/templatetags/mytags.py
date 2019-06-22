from django import template
from django.utils.safestring import mark_safe
from iotmp import models
from django.db import models as dj_models
from django.db.models import Max
from iotmp import admin
from DevOps.settings import HOSTGROUP_DIR, CONFIG_FILE
import time
import os
from iotmp import myconfigparser as configparser

register = template.Library()


@register.simple_tag
def build_paginators(query_sets):
    '''返回整个分页元素'''
    if not query_sets:
        return ""
    page_btns = ''

    # added_dot_ele = False #
    # for page_num in query_sets.paginator.page_range:
    #     if page_num < 3 or page_num > query_sets.paginator.num_pages -2 \
    #             or abs(query_sets.number - page_num) <= 2: #代表最前2页或最后2页 #abs判断前后1页
    #         ele_class = ""
    #         if query_sets.number == page_num:
    #             added_dot_ele = False
    #             ele_class = "active"
    #         page_btns += '''<li class="%s"><a href="?page=%s">%s</a></li>''' % (
    #         ele_class, page_num,page_num)
    #
    #     else: #显示...
    #         if added_dot_ele == False: #现在还没加...
    #             page_btns += '<li><a>...</a></li>'
    #             added_dot_ele = True

    dot_flag = True
    for num in query_sets.paginator.page_range: # 如果总共12页，就是1--12
        if num == query_sets.number: # query_sets.number代表页面中的当前页数值
            dot_flag = True
            current_page = 'active'
        else:
            current_page = ''

        if num < 3 or abs(num-query_sets.number)<=2 or num > query_sets.paginator.num_pages - 2: #前后两页和中间页
            page_btns += '''<li class="%s"><a href="?_page=%s">%s</a></li>''' % (current_page,num, num)
        elif dot_flag:
            page_btns += '''<li><a>...</a></li>'''
            dot_flag = False

    return mark_safe(page_btns)

@register.simple_tag
def display_new_obj(model_name):
    row_ele = ''
    table = getattr(models, model_name)
    # print('table别名', table._meta.verbose_name) 获得表别名
    fields_set = table._meta.get_fields()
    # print(fields_set)

    for field in fields_set:# 顺序：Rel字段 AutoField 普通字段 ManyToMany字段都排在最后

        #这些字段不需要显示
        hide_list = getattr(admin, 'new_%s_hide_fields' % model_name, None) #找不到就返回None，不抛异常
        if field.name in hide_list:
            continue

        if type(field) not in [dj_models.OneToOneRel, dj_models.ManyToOneRel, dj_models.ManyToManyRel, dj_models.AutoField]:#否则 field.verbose_name会报异常，而且这三个不需要

            if field.null:#允许为空
                required = ""
                color = ""
            else:
                required = "required"
                color = "red"

            row_ele += '''<label style="margin-left:20%;width:100px;color:{color}">{verbose_name}</label>
            '''.format(color=color,verbose_name=field.verbose_name)
            # python默认：当建表时没写field.verbose_name，则field.verbose_name = field.name


            width_size = "600px"
            if type(field) in [dj_models.ManyToManyField, dj_models.TextField]:
                multiple = "multiple"  #TextField字段没有此属性
                height_size = "200px"
            else:
                multiple = ""
                height_size = "50px"


            # 1、关系字段
            if type(field) in [dj_models.OneToOneField, dj_models.ForeignKey, dj_models.ManyToManyField]:
                rel_model = field.related_model
                option_ele = ''
                for row in rel_model.objects.all():
                    option_ele += '''<option value="{rel_id}">{row}</option>'''.format(rel_id=row.id, row=row)

                row_ele += '''
                    <select  {multiple} name="{field_name}" style="width:{width_size};height: {height_size};" {required}>
                        {option_ele}
                    </select>
                    '''.format(multiple=multiple, field_name=field.name, width_size=width_size, height_size=height_size,
                               required=required, option_ele=option_ele)

            # 2、choices字段
            elif field.choices:#不为空表明是choices字段
                option_ele = ''
                for row in field.get_choices():# [('', '---------'), (0, '正常'), (1, '异常'), (2, '告警')]
                    option_ele += '''<option value="{value}">{display_value}</option>'''.format(value=row[0], display_value=row[1])

                row_ele += '''<select  name="{field_name}" style="width: {width_size};height: {height_size};" {required}>
                                {option_ele}
                           </select>
                    '''.format(field_name=field.name, width_size=width_size, height_size=height_size, required=required, option_ele=option_ele)

            # 3、NullBooleanField  尽量不用吧
            # elif type(field) == dj_models.NullBooleanField:#比BooleanField多个Null
            #     row_ele += '''<select  name="{field_name}" style="width: {width_size};height: {height_size};" {required}>
            #                   <option value="">------</option>
            #                   <option value="1">Yes</option>    <!-- 这个值应该根据业务来 -->
            #                   <option value="0">No</option>
            #                </select> '''.format(field_name=field.name, width_size=width_size, height_size=height_size, required=required,)

            # 4、TextField
            elif type(field) == dj_models.TextField:
                row_ele += '''<textarea style="width:{width_size};height:{height_size};vertical-align:middle;" name="{field_name}" {required}> </textarea>
                       '''.format(width_size=width_size, height_size=height_size, field_name=field.name, required=required, )


            else:
                # 5、时间字段
                if type(field) == dj_models.DateTimeField:
                    input_type = "datetime-local"
                elif type(field) == dj_models.DateField:
                    input_type = "date"
                elif type(field) == dj_models.TimeField:
                    input_type = "time"

                # 6、EmailField
                elif type(field) == dj_models.EmailField:
                    input_type = "email"

                # 7、其他字段
                else:
                    input_type = "text"
                row_ele += '''<input type="{input_type}" name="{field_name}" {required} style="width: {width_size};height: {height_size};">
                           '''.format(input_type=input_type, field_name=field.name, required=required, width_size=width_size, height_size=height_size, )

            row_ele += '<hr/>' #水平线

    #print(row_ele)
    return mark_safe(row_ele)

@register.simple_tag
def display_table_head(model_name):
    row_ele = '<th>序号</th>'
    table = getattr(models, model_name)
    fields_set = table._meta.get_fields()

    for field in fields_set:# 顺序：Rel字段 AutoField 普通字段 ManyToMany字段都排在最后
        if type(field) not in [dj_models.OneToOneRel, dj_models.ManyToOneRel, dj_models.ManyToManyRel, dj_models.ManyToManyField, dj_models.AutoField]:#否则 field.verbose_name会报异常，而且这三个不需要
            row_ele += '''<th>{verbose_name}</th>'''.format(verbose_name=field.verbose_name)


    row_ele += '<th>删除</th>'


    return mark_safe(row_ele)

@register.simple_tag
def display_table_body(model_name, query_sets=None):
    if not query_sets:
        return ""
    row_ele = ''
    per_page = query_sets.paginator.per_page  # 每页多少条
    number = query_sets.number  # 当前是第几页
    start = (number - 1) * per_page + 1  # 当前页从几开始
    for index, row in enumerate(query_sets, start):
        row_ele += '''<tr><td><a href="/monitor/update/{model_name}/{obj_id}/">{index}</a></td>'''.format(model_name=model_name, obj_id=row.id, index=index)
        for field in row._meta.get_fields():  # 顺序：Rel字段 AutoField 普通字段 ManyToMany字段都排在最后
            if type(field) not in [dj_models.OneToOneRel, dj_models.ManyToOneRel, dj_models.ManyToManyRel,dj_models.ManyToManyField, dj_models.AutoField]:  # 否则 field.verbose_name会报异常，而且这三个不需要
                color = ""
                if field.choices:#是choices字段
                    value = getattr(row, "get_%s_display" % field.name)()
                    if value == "异常":
                        color = "red"

                elif type(field) in [dj_models.DateTimeField, dj_models.DateField, dj_models.TimeField]:
                    value = getattr(row, field.name).strftime("%Y-%m-%d %H:%M:%S")
                else:
                    value = getattr(row, field.name)
                row_ele += '''<td style="color:{color}">{value}</td>'''.format(color=color, value=value)
        row_ele += '''<td><a href="/monitor/del/{model_name}/{id}/"><img src="/static/img/del.png" style="width:30px;height:30px;"></a></td>'''.format(model_name=model_name, id=row.id)
        row_ele += '</tr>'
    return mark_safe(row_ele)

@register.simple_tag
def display_update_obj(model_name,instance_obj):
    row_ele = ''
    fields_set = instance_obj._meta.get_fields()
    # print(fields_set)

    for field in fields_set:# 顺序：Rel字段 AutoField 普通字段 ManyToMany字段都排在最后
        if type(field) not in [dj_models.OneToOneRel, dj_models.ManyToOneRel, dj_models.ManyToManyRel, dj_models.AutoField]:#否则 field.verbose_name会报异常，而且这三个不需要
            # 这些字段不需要显示
            hide_list = getattr(admin, 'new_%s_hide_fields' % model_name)
            if field.name in hide_list:
                continue


            if field.null:#允许为空
                required = ""
                color = ""
            else:
                required = "required"
                color = "red"

            row_ele += '''<label style="margin-left:20%;width:100px;color:{color}">{verbose_name}</label>
            '''.format(color=color,verbose_name=field.verbose_name)
            # python默认：当建表时没写field.verbose_name，则field.verbose_name = field.name


            width_size = "600px"
            if type(field) in [dj_models.ManyToManyField, dj_models.TextField]:
                multiple = "multiple"  #TextField字段没有此属性
                height_size = "200px"
            else:
                multiple = ""
                height_size = "50px"

            value = getattr(instance_obj, field.name)
            if value:
                if type(field) == dj_models.DateTimeField:
                    value = value.strftime("%Y-%m-%dT%H:%M")  # 2019-01-18T00:59
                elif type(field) == dj_models.DateField:
                    value = value.strftime("%Y-%m-%d")
                elif type(field) == dj_models.TimeField:
                    value = value.strftime("%H:%M")
            else:
                value = ""


            # 1、关系字段
            if type(field) in [dj_models.OneToOneField, dj_models.ForeignKey, dj_models.ManyToManyField]:
                rel_model = field.related_model
                rel_obj = getattr(instance_obj, field.name) #可能是一个对象，也可能是一个查询集
                option_ele = ''
                for row in rel_model.objects.all():
                    if type(field) == dj_models.ManyToManyField:
                        if row in rel_obj.all():
                            select = "selected"
                        else:
                            select = ""
                    else:
                        if row == rel_obj:
                            select = "selected"
                        else:
                            select = ""
                    option_ele += '''<option {select} value="{rel_id}">{row}</option>'''.format(select=select, rel_id=row.id, row=row)

                row_ele += '''
                    <select {multiple} name="{field_name}" style="width:{width_size};height: {height_size};" {required}>
                        {option_ele}
                    </select>
                    '''.format(multiple=multiple, field_name=field.name, width_size=width_size, height_size=height_size,
                               required=required, option_ele=option_ele)

            # 2、choices字段
            elif field.choices:#不为空表明是choices字段
                option_ele = ''
                for row in field.get_choices():# [('', '---------'), (0, '正常'), (1, '异常'), (2, '告警')]
                    if row[0] == getattr(instance_obj, field.name):
                        select = "selected"
                    else:
                        select = ""
                    option_ele += '''<option {select} value="{value}">{display_value}</option>'''.format(select=select, value=row[0], display_value=row[1])

                row_ele += '''<select  name="{field_name}" style="width: {width_size};height: {height_size};" {required}>
                                {option_ele}
                           </select>
                    '''.format(field_name=field.name, width_size=width_size, height_size=height_size, required=required, option_ele=option_ele)

            # 3、NullBooleanField
            # elif type(field) == dj_models.NullBooleanField:#比BooleanField多个Null
            #     row_ele += '''<select  name="{field_name}" style="width: {width_size};height: {height_size};" {required}>
            #                   <option value="">------</option>
            #                   <option value="1">Yes</option>    <!-- 这个值应该根据业务来 -->
            #                   <option value="0">No</option>
            #                </select> '''.format(field_name=field.name, width_size=width_size, height_size=height_size, required=required,)

            # 4、TextField
            elif type(field) == dj_models.TextField:
                row_ele += '''<textarea style="width:{width_size};height:{height_size};vertical-align:middle;" name="{field_name}" {required}>{value}</textarea>
                       '''.format(width_size=width_size, height_size=height_size, field_name=field.name, required=required, value=value )


            else:
                # 5、时间字段
                if type(field) == dj_models.DateTimeField:
                    input_type = "datetime-local"
                elif type(field) == dj_models.DateField:
                    input_type = "date"
                elif type(field) == dj_models.TimeField:
                    input_type = "time"

                # 6、EmailField
                elif type(field) == dj_models.EmailField:
                    input_type = "email"

                # 7、其他字段
                else:
                    input_type = "text"

                row_ele += '''<input type="{input_type}" name="{field_name}" {required} style="width: {width_size};height: {height_size};" value="{value}">
                           '''.format(input_type=input_type, field_name=field.name, required=required, width_size=width_size, height_size=height_size, value=value)

            row_ele += '<hr/>' #水平线

    return mark_safe(row_ele)


@register.simple_tag
def display_version_files(query_sets=None): # 传进来的query_sets是models.Files对象集合
    if not query_sets:
        return ""
    row_ele = ''
    per_page = query_sets.paginator.per_page  # 每页多少条
    number = query_sets.number  # 当前是第几页
    start = (number - 1) * per_page + 1  # 当前页从几开始
    for index, row in enumerate(query_sets, start):
        #t = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(float(file))) 时间戳
        row_ele += '''
        <tr>
            <td>{index}</td>
            <td>{filename}</td>
            <td>{upload_user}</td>
            <td>{mtime}</td>
            <td>{md5}</td>
            <td><a href="/iotmp/version/delfile/{id}/{fid}/"><img src="/static/img/del.png" style="width:30px;height:30px;"></a></td>
        </tr>
            '''.format(index=index, filename=row.name, upload_user=row.upload_user,
                       mtime=row.mtime.strftime("%Y-%m-%d %H:%M:%S"), md5=row.md5, id=row.version.id, fid=row.id)

    return mark_safe(row_ele)

@register.simple_tag
def display_version(query_sets=None): # 传进来的query_sets是models.Files对象集合
    if not query_sets:
        return ""
    row_ele = ''
    per_page = query_sets.paginator.per_page  # 每页多少条
    number = query_sets.number  # 当前是第几页
    start = (number - 1) * per_page + 1  # 当前页从几开始
    for index, row in enumerate(query_sets, start):
        row_ele += '''
        <tr>
            <td>{index}</td>
            <td>{name}</td>
            <td><a href="/iotmp/version/files/{id}/">{file_nums}</a></td>
            <td>{create_user}</td>
            <td>{create_time}</td>
            <td><a href="/iotmp/version/del/{id}/"><img src="/static/img/del.png" style="width:30px;height:30px;"></a></td>
        </tr>
            '''.format(id=row.id, index=index, name=row.name, file_nums=row.files_set.all().count(),
                       create_user=row.create_user, create_time=row.create_time.strftime("%Y-%m-%d %H:%M:%S"), )

    return mark_safe(row_ele)

@register.simple_tag
def display_host(query_sets=None): # 传进来的query_sets是models.Files对象集合
    if not query_sets:
        return ""
    row_ele = ''
    per_page = query_sets.paginator.per_page  # 每页多少条
    number = query_sets.number  # 当前是第几页
    start = (number - 1) * per_page + 1  # 当前页从几开始
    for index, row in enumerate(query_sets, start):
        row_ele += '''
        <tr>
            <td>{index}</td>
            <td>{ip}</td>
            <td>{port}</td>
            <td>{user}</td>
            <td>{keyfile}</td>
            <td>{note}</td>
            <td><a href="/iotmp/host/del/{id}/"><img src="/static/img/del.png" style="width:30px;height:30px;"></a></td>
        </tr>
            '''.format(index=index, ip=row.ip, port=row.port,
                       user=row.user, keyfile=row.keyfile, note=row.note, id=row.id)

    return mark_safe(row_ele)


@register.simple_tag
def display_hostgroup(query_sets=None): # 传进来的query_sets是models.Files对象集合
    if not query_sets:
        return ""

    row_ele = ''
    per_page = query_sets.paginator.per_page  # 每页多少条
    number = query_sets.number  # 当前是第几页
    start = (number - 1) * per_page + 1  # 当前页从几开始
    for index, row in enumerate(query_sets, start):
        config_file = os.path.join(HOSTGROUP_DIR,  row, CONFIG_FILE)
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
        else:
            mysql_ip = ""
            redis_ip = ""
            zook_ip = ""
            activemq_ip = ""
            es_ip = ""
            flowhys_ip = ""
            log_ip = ""


        row_ele += '''
        <tr>
            <td>{index}</td>
            <td>{mysql_ip}</td>
            <td>{redis_ip}</td>
            <td>{zook_ip}</td>
            <td>{activemq_ip}</td>
            <td>{es_ip}</td>
            <td>{flowhys_ip}</td>
            <td>{log_ip}</td>
            <td><a href="/iotmp/hostgroup/del/{mysql_ip}/"><img src="/static/img/del.png" style="width:30px;height:30px;"></a></td>
        </tr>
            '''.format(index=index,  mysql_ip=mysql_ip, redis_ip=redis_ip,zook_ip=zook_ip,
                       activemq_ip=activemq_ip, es_ip=es_ip, flowhys_ip=flowhys_ip, log_ip=log_ip,
                       )

    return mark_safe(row_ele)


@register.simple_tag
def display_tasks(query_sets=None): # 传进来的query_sets是models.Files对象集合
    if not query_sets:
        return ""
    row_ele = ''
    per_page = query_sets.paginator.per_page  # 每页多少条
    number = query_sets.number  # 当前是第几页
    start = (number - 1) * per_page + 1  # 当前页从几开始
    for index, row in enumerate(query_sets, start):
        if row.type == 0:
            type = '安装'
        elif row.type == 1:
            type = '更新'

        color = ''
        if row.state == 0:
            state = '等待中'
            color = 'gray'
        elif row.state == 1:
            state = '进行中'
            color = 'green'
        elif row.state == 2:
            state = '成功'
        elif row.state == -1:
            state = '失败'


        row_ele += '''
        <tr>
            <td><a href="/iotmp/tasks/log/{id}/">{index}</a></td>
            <td>{ctime}</td>
            <td>{type}</td>
            <td>{host_ip}</td>
            <td>{version_name}</td>
            <td>{file_name}</td>
            <td style="color:{color}">{state}</td>
            <td><a href="/iotmp/tasks/del/{id}/"><img src="/static/img/del.png" style="width:30px;height:30px;"></a></td>
        </tr>
            '''.format(index=index, ctime=row.ctime.strftime("%Y%m%d %H:%M:%S"), type=type, host_ip=row.ip,
                       version_name=row.version_name, file_name=row.file_name, color=color, state=state, id=row.id)

    return mark_safe(row_ele)

@register.simple_tag
def display_tasks_success(query_sets=None): # 传进来的query_sets是models.Files对象集合
    if not query_sets:
        return ""
    row_ele = ''
    per_page = query_sets.paginator.per_page  # 每页多少条
    number = query_sets.number  # 当前是第几页
    start = (number - 1) * per_page + 1  # 当前页从几开始
    for index, row in enumerate(query_sets, start):
        if row.type == 0:
            type = '安装'
        elif row.type == 1:
            type = '更新'

        if row.state == 0:
            state = '等待中'
        elif row.state == 1:
            state = '进行中'
        elif row.state == 2:
            state = '成功'
        elif row.state == -1:
            state = '失败'


        row_ele += '''
        <tr>
            <td><a href="/iotmp/tasks/log/{id}/">{index}</a></td>
            <td>{ctime}</td>
            <td>{type}</td>
            <td>{host_ip}</td>
            <td>{version_name}</td>
            <td>{file_name}</td>
            <td>{state}</td>
        </tr>
            '''.format(index=index, ctime=row.ctime.strftime("%Y%m%d %H:%M:%S"), type=type, host_ip=row.ip,
                       version_name=row.version_name, file_name=row.file_name, state=state, id=row.id)

    return mark_safe(row_ele)

@register.simple_tag
def display_server_info(query_sets=None): # 传进来的query_sets是models.Files对象集合
    if not query_sets:
        return ""
    row_ele = ''
    per_page = query_sets.paginator.per_page  # 每页多少条
    number = query_sets.number  # 当前是第几页
    start = (number - 1) * per_page + 1  # 当前页从几开始
    for index, row in enumerate(query_sets, start): #注意此处的row是一个dict类型 {'ip': '10.10.10.2'}
        ip = row["ip"]
        server_nums = models.Tasks.objects.filter(ip=ip, state=2).values("server_name").distinct().count()
        ctime_dic =  models.Tasks.objects.filter(ip=ip, state=2).aggregate(max_ctime=Max("ctime")) # 字典类型，如不指定key，默认为ctime__max
        ctime_str = ctime_dic["max_ctime"].strftime("%Y-%m-%d %H:%M:%S")
        user = models.Tasks.objects.filter(ip=ip, state=2, ctime=ctime_dic["max_ctime"]) # 用逗号隔开表示and意思，想用or的话得用Q
        user = user[0].username #正常情况去重复后用户只有一个

        row_ele += '''
        <tr>
            <td>{index}</td>
            <td>{ip}</td>
            <td><a href="/iotmp/server/info/{ip}/">{server_nums}</a></td>
            <td>{ctime_str}</td>
            <td>{user}</td>
            <td><a href="/iotmp/server/info/del/{ip}/"><img src="/static/img/del.png" style="width:30px;height:30px;"></a></td>
        </tr>
            '''.format(index=index, ip=ip, server_nums=server_nums, ctime_str=ctime_str, user=user,
                       )

    return mark_safe(row_ele)

@register.simple_tag
def display_server_host(host_ip, query_sets=None): # 传进来的query_sets是models.Files对象集合
    # query_sets：<QuerySet [{'server_name': 'redis'}, {'server_name': 'jdk'}, {'server_name': 'flowhysui'}, {'server_name': 'systemsetting'}]>
    if not query_sets:
        return ""
    row_ele = ''
    per_page = query_sets.paginator.per_page  # 每页多少条
    number = query_sets.number  # 当前是第几页
    start = (number - 1) * per_page + 1  # 当前页从几开始
    for index, row in enumerate(query_sets, start): #注意此处的row是一个dict类型 {'server_name': 'redis'}
        server_name = row["server_name"]
        ctime_dic =  models.Tasks.objects.filter(ip=host_ip, state=2, server_name=server_name).aggregate(max_ctime=Max("ctime")) # 字典类型，如不指定key，默认为ctime__max
        ctime_str = ctime_dic["max_ctime"].strftime("%Y-%m-%d %H:%M:%S")
        tasks = models.Tasks.objects.filter(ip=host_ip, ctime=ctime_dic["max_ctime"], server_name=server_name, state=2) # 用逗号隔开表示and意思，想用or的话得用Q
        version_name = tasks[0].version_name #正常情况只有一个
        file_name = tasks[0].file_name
        user = tasks[0].username

        server_queryset = models.Server.objects.filter(name=server_name)
        if server_queryset:
            server = server_queryset[0] #正常情况只能找到一个
            if server.check_type == 0:# 检测地址是一个url
                url = server.check_exp.format(ip=host_ip)
            else:
                url = "/iotmp/server/check/{ip}/{server_name}/".format(ip=host_ip, server_name=server_name)
        else:
            url = ""

        row_ele += '''
        <tr>
            <td>{index}</td>
            <td>{ip}</td>
            <td>{server_name}</td>
            <td>{version}</td>
            <td>{version_name}</td>
            <td>{file_name}</td>
            <td>{ctime_str}</td>
            <td><a target="_blank" href="{url}">服务检测</a></td>
            <td>{user}</td>
            <td><a href="/iotmp/server/host/del/{ip}/{server_name}/"><img src="/static/img/del.png" style="width:30px;height:30px;"></a></td>
        </tr>
            '''.format(index=index, ip=host_ip, server_name=server_name, version="1.0.0", version_name=version_name, file_name=file_name,
                       ctime_str=ctime_str, url=url, user=user,
                       )

    return mark_safe(row_ele)

@register.simple_tag
def display_logfile(file_path):
    if not os.path.isfile(file_path):
        return ""
    row_ele = ''
    f = open(file_path, 'r', encoding="utf-8")
    for line in f:
        row_ele += "%s%s" % (line, '<br />')

    return mark_safe(row_ele)

@register.simple_tag
def select_env():
    folder_list = []
    name = os.listdir(HOSTGROUP_DIR)
    for folder_name in name:
        if os.path.isdir(  os.path.join(HOSTGROUP_DIR, folder_name)  ):
            folder_list.append(folder_name)
    row_ele = '<option value ="">------</option>'
    for folder in folder_list:
        row_ele += '''
            <option value ="{mysql_ip}">{mysql_ip}</option>
            '''.format(mysql_ip=folder)

    return mark_safe(row_ele)


@register.simple_tag
def select_version_files(group_file):
    a = """
    <li><a href="javascript:void(0);" onclick="display_menu(this)">H版</a>
         <ul style="list-style: none;">
             <li><input type="checkbox">flow.tar.gz</li>
             <li><input type="checkbox">flowui.zip</li>
             <li><input type="checkbox">logstash.tar.gx</li>
         </ul>
    </li>

    <li><a href="javascript:void(0);" onclick="display_menu(this)">G版</a>
         <ul style="list-style: none;">
             <li><input type="checkbox">主机性能</li>
             <li><input type="checkbox">主机性能</li>
             <li><input type="checkbox">主机性能</li>
         </ul>
    </li>
    """
    row_ele = ''
    version_all = models.Version.objects.all()

    for version in version_all:
        row_ele += '''<li><a href="javascript:void(0);" onclick="display_menu(this)">{version_name}</a>
         <ul style="list-style: none;display:none">'''.format(version_name=version.name)

        version_files = models.Files.objects.filter(version=version)
        for file in version_files:
            # 使用>号连接版本库与文件名，因为版本库是目录，目录名不可能包含>号
            row_ele += '''<li>
            <input type="checkbox" name="{group_file}" value="{version_name}>{file_name}">{file_name}
            </li>'''.format(
                group_file=group_file, version_name=version.name, file_name=file.name)

        row_ele += '''</ul> </li>'''

    return mark_safe(row_ele)


@register.simple_tag
def select_host(group_ip):
    a = '''
        <select name="G1_IP">
            <option value="192.100.100.100">192.100.100.100</option>
            <option value="">11</option>
            <option value="">11</option>
        </select>
    '''
    row_ele = ''
    row_ele += '''<select name="{group_ip}">'''.format(group_ip=group_ip)
    #先加个空的
    row_ele += '''<option value="">---------------</option>'''
    host_all = models.Host.objects.all()
    for host in host_all:
        row_ele += '''<option value="{ip}">{ip}</option>'''.format(ip=host.ip)

    row_ele += '''</select>'''
    return mark_safe(row_ele)
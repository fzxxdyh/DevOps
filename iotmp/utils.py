import hashlib
import os, sys
import time
import string
import random
from iotmp import myconfigparser as configparser
from DevOps.settings import HOSTGROUP_DIR, CONFIG_FILE, VERSION_DIR , INSTALL_SCRIPT_DIR, LOG_DIR, NGINX_DIR
from shutil import copyfile
from iotmp import models
import re
import paramiko


def get_encrypt_value(strings):
    '''
    for i in range(127):
        print(i, chr(i))
    a-z: 97-122,   A-Z:  65-90,  0-9: 48-57
    ord('a') --> 97
    chr(97)  --> 'a'
    '''
    if not strings.strip():
        return ""
    # letters = string.ascii_letters # 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
    lowercase = string.ascii_lowercase # 'abcdefghijklmnopqrstuvwxyz'  取2个
    uppercase = string.ascii_uppercase # 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'  取2个
    digits = string.digits # '0123456789' 取2个
    punctuation = string.punctuation # '!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~' 取2个
    enc_str = ''

    # 1、加8个随机字符串
    for i in range(2):# 小写、大写、数字、特殊字符都取2个，总共长度加8
        enc_str += random.choice(lowercase) + random.choice(uppercase) + random.choice(digits) + random.choice(punctuation)

    # 2、加上2位原字符串长度
    length =  len(strings) #原始字符串的长度
    if length < 10 and length > 0:
        s_len = "0" + str(length)  # 08、07 。。
    else:
        s_len = str(length)
    enc_str += s_len  #8位随机字符串+2位原字符长度，总计10位

    # 3、原字符串-4
    for i in strings:
        num = ord(i) - 4 #在原数值上减4
        enc_str += chr(num)

    # 4、补满50位
    str_box = string.ascii_letters + string.digits + string.punctuation #大小写+数字+符号
    for i in range(0, 50-length, 1):#range(start, stop[, step])
        enc_str += random.choice(str_box)
    return enc_str


def get_decode_value(strings):
    if not strings.strip():
        return ""
    length = int(strings[8:10]) #原始字符串长度
    sub_str = strings[10:length+10] #取中间部分
    dec_str = ''
    for i in sub_str:
        num = ord(i) + 4 #加回来
        dec_str += chr(num)
    return dec_str

def get_md5_value(string):
    if string:
        m = hashlib.md5(bytes('GgsDdu', encoding='utf-8'))
        m.update(bytes(string, encoding='utf-8'))
        return m.hexdigest()


def rmdir_all(dirPath):
    if not os.path.isdir(dirPath):
        return

    for file in os.listdir(dirPath):
        filePath = os.path.join(dirPath, file)
        if os.path.isfile(filePath):
            os.remove(filePath)
        elif os.path.isdir(filePath):
            rmdir_all(filePath)

    for folder in os.listdir(dirPath):
        os.rmdir(os.path.join(dirPath, folder))

    os.rmdir(dirPath)


def TimeStampToTime(timestamp):
    timeStruct = time.localtime(timestamp)
    return time.strftime('%Y-%m-%d %H:%M:%S',timeStruct)

def check_ip_addr(ip):
    if not ip:
        return False

    sub_ip = ip.split(".")
    if len(sub_ip) != 4:
        return False

    for sub in sub_ip:
        if not sub.isdigit():
            return False
        if int(sub) > 255 or int(sub) < 0:
            return False
    return True

def get_ssh(ip, user, port=22, passwd=None, key_file=None):
    '''优先使用证书连接'''

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    if key_file:
        private_key = paramiko.RSAKey.from_private_key_file(key_file, password=None)#如果生成证书时有设置密码，就加上
        ssh.connect(hostname=ip, port=port, username=user, pkey=private_key, banner_timeout=600)
    elif passwd:
        ssh.connect(hostname=ip, port=port, username=user, password=passwd, banner_timeout=600)
    else:
        print("must have keyfile or password!")
        return None

    #基于现有ssh连接创建文件传输连接
    # transport = ssh.get_transport()
    # sftp = paramiko.SFTPClient.from_transport(transport)
    # sftp.put(r'D:\ssh\a.txt', r'/tmp/a.txt')
    # sftp.close()
    # ssh.close()

    return ssh

def get_sftp(ssh):
    transport = ssh.get_transport()
    sftp = paramiko.SFTPClient.from_transport(transport)
    #sftp.put(r'D:\ssh\a.txt', r'/tmp/a.txt')
    #sftp.close()
    return sftp

def get_sftp2(ssh):
    transport = ssh.get_transport()

    sftp = paramiko.SFTPClient.from_transport(transport)

    #sftp.put(r'D:\ssh\a.txt', r'/tmp/a.txt')
    #sftp.close()
    return sftp

def save_config(**kwargs):
    mysql_ip = kwargs.get("mysql_ip", None)
    local_ip = kwargs.get("local_ip", None)
    #print("in save_config", kwargs)
    if mysql_ip and local_ip:
        if not os.path.isdir( os.path.join(HOSTGROUP_DIR, mysql_ip, local_ip) ):#新建
            conf_file_dir = os.path.join(HOSTGROUP_DIR, mysql_ip, local_ip)
            os.makedirs(conf_file_dir) #递归创建目录
            source = os.path.join(INSTALL_SCRIPT_DIR, CONFIG_FILE) #从安装脚本目录拷贝
            target = os.path.join(HOSTGROUP_DIR, mysql_ip, local_ip, CONFIG_FILE)
            copyfile(source, target)

        conf_file = os.path.join(HOSTGROUP_DIR, mysql_ip, local_ip, CONFIG_FILE)
        conf_obj = configparser.ConfigParser()
        conf_obj.read(conf_file, encoding="utf-8")
        for key, value in kwargs.items():
            conf_obj.set("config", key.upper(), value)

        f = open(conf_file, "w", encoding="utf-8")
        conf_obj.write(f)
        f.close()

        # 覆盖主机组下的配置文件
        source = os.path.join(HOSTGROUP_DIR, mysql_ip, local_ip, CONFIG_FILE)
        target = os.path.join(HOSTGROUP_DIR, mysql_ip, CONFIG_FILE)
        copyfile(source, target)



def file_map_server(file_name):
    file_name = file_name.lower()
    server_all = models.Server.objects.all()
    for row in server_all:
        server_name = row.name.lower()
        pattern = '[\.\-\_]%s[\.\-\_]' % server_name  # server_name在文件名中间，前面是[.-_]其中之一，后面也是这样
        if re.search(pattern, file_name):#能找到
            return (row.name, row.level)
        else:
            pattern = '^%s[\.\-\_]' % server_name   # server_name在文件名开头，后面是[.-_]其中之一
            if re.search(pattern, file_name):#能找到
                return (row.name, row.level)

    return (None, None)





def exec_install(ctime, mysql_ip):
    tasks_queryset = models.Tasks.objects.filter(ctime=ctime).order_by("level", "ip")
    for index, t in enumerate(tasks_queryset):
        if t.state == 0:
            t.state = 1 #进行中
            t.save()
        else:
            continue
        host = models.Host.objects.get(ip=t.ip)
        if not os.path.isdir( os.path.join(LOG_DIR, t.ip) ):#创建日志目录
            os.makedirs(os.path.join(LOG_DIR, t.ip))  # 如果不存在，会递归创建
        logfile = os.path.join(LOG_DIR, t.ip, t.logfile)
        f = open(logfile, 'w', encoding="utf-8") #每个tasks都会产生一个日志文件
        passwd = get_decode_value(host.passwd)
        try:
            ssh = get_ssh(host.ip, host.user, port=host.port, passwd=passwd, key_file=host.keyfile)
            # 先在目标服务器上创建目录
            cmds = ["mkdir -p /home/iotmp/devops/tgz/", "mkdir -p /home/iotmp/devops/install/"]
            for cmd in cmds:
                stdin, stdout, stderr = ssh.exec_command(cmd)
                for line in stdout:
                    #print(line)
                    f.write(line + '\n')
                    f.flush()
                    sys.stdout.flush()

                for line in stderr:
                    #print(line)
                    f.write(line + '\n')
                    f.flush()
                    sys.stderr.flush()

            sftp = get_sftp(ssh)

            # 1.拷贝安装文件
            local_file = os.path.join(VERSION_DIR, t.version_name, t.file_name)
            remote_file = "/home/iotmp/devops/tgz/%s" % t.file_name #必须有文件名
            #print("local_file1:", local_file)
            sftp.put(local_file, remote_file)

            # 2. 拷贝安装脚本
            server_obj = models.Server.objects.get(name=t.server_name)
            script_name = server_obj.install_script
            local_script_file = os.path.join(INSTALL_SCRIPT_DIR, script_name)
            remote_script_file = "/home/iotmp/devops/install/%s" % script_name
            #print("local_file2:", local_file)
            sftp.put(local_script_file, remote_script_file)

            # 3. 拷贝00config配置文件
            confile_file = os.path.join(HOSTGROUP_DIR, mysql_ip, t.ip, CONFIG_FILE)
            remote_config_file = "/home/iotmp/devops/install/%s" % CONFIG_FILE
            #print("local_file3:", local_file)
            sftp.put(confile_file, remote_config_file)

            # 4、flowhysui 特别处理
            if t.server_name.lower() == 'flowhysui':
                nginx_script = os.path.join(INSTALL_SCRIPT_DIR, '17nginx.sh')
                sftp.put(nginx_script, "/home/iotmp/devops/install/17nginx.sh")
                nginx_files = ["nginx-1.14.1.tar.gz", "openssl-fips-2.0.10.tar.gz", "pcre-8.40.tar.gz", "zlib-1.2.11.tar.gz" ]
                for filename in nginx_files:
                    sftp.put( os.path.join(NGINX_DIR, filename), "/home/iotmp/devops/tgz/%s" % filename )

                cmds = ["sed -i 's#\r##g' %s" % remote_config_file, "chmod 775 %s" % remote_script_file,
                        "chmod 775 /home/iotmp/devops/install/17nginx.sh", remote_script_file]
            else:
                cmds = ["sed -i 's#\r##g' %s" %  remote_config_file,"chmod 775 %s" % remote_script_file,  remote_script_file]

            # cmds = ["/home/iotmp/devops/install/test.sh"]
            for cmd in cmds:
                stdin, stdout, stderr = ssh.exec_command(cmd)
                for line in stdout:
                    #print(line)
                    f.write(line + '\n')
                    f.flush()
                    sys.stdout.flush()

                for line in stderr:
                    #print(line)
                    f.write(line + '\n')
                    f.flush()
                    sys.stderr.flush()

            t.state = 2 #成功
            t.save()
            sftp.close()
            ssh.close()

        except Exception as e:
            print("ERROR, in utils.exec_install", e)
            for t in tasks_queryset:
                if t.state != 2:#没有成功
                    t.state = -1  # 失败
                    t.save()
            f.write(str(e) + '\n')
            sys.exit(1) #该子线程退出
            # os._exit(1) #django进程都没了，什么都没了

        finally:
            f.close()





if __name__ == "__main__":
    # ip = '192.168.110.50'
    # user = 'root'
    # passwd = 'root@123'
    # cmds = ['ifconfig', 'hostname', '/tmp/opts50.sh -uroot,apps -p123456 -h10.10.10.1']
    # ssh = get_ssh(ip, user, passwd=passwd)
    # for cmd in cmds:
    #     stdin, stdout, stderr = ssh.exec_command(cmd)
    #     for line in stdout.readlines():
    #         print(line)
    #     for line in stderr.readlines():
    #         print(line)
    # ssh.close()
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DevOps.settings')
    django.setup()
    dir_path = "D:\\dyh\\python\\hykj\\DevOps\\data\\version\\sfaf555"
    from iotmp import models
    import os
    for file in os.listdir(dir_path):
        server_name, level = file_map_server(file)
        print(file, server_name, level)

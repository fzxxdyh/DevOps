#!/bin/bash


workdir=$(cd $(dirname $0); pwd)
sed -i "s# ##g" $workdir/00config.ini
source $workdir/00config.ini > /dev/null 2>&1
TODAY=`date "+%Y%m%d"`


if [ -f /usr/local/nginx/sbin/nginx ];then
    echo "nginx is exist!"
    count=`sudo netstat -nltp|grep nginx|wc -l`
    if [ $count -eq 0 ];then
        echo "start nginx...."
        /usr/local/nginx/sbin/nginx
    fi
    exit 1
fi



count=`rpm -qa gcc gcc-c++|wc -l`
if [ $count -ne 2 ];then
    sudo yum -y install gcc gcc-c++
fi


 
cd $TGZ_DIR/nginx/
tar zxf nginx-1.14.1.tar.gz
tar zxf openssl-fips-2.0.10.tar.gz
tar zxf pcre-8.40.tar.gz
tar zxf zlib-1.2.11.tar.gz

cd $TGZ_DIR/nginx/openssl-fips-2.0.10
sudo sh -c "./config && make && make install"

cd $TGZ_DIR/nginx/pcre-8.40
sudo sh -c "./configure && make && make install"


cd $TGZ_DIR/nginx/zlib-1.2.11
sudo sh -c "./configure && make && make install"


cd $TGZ_DIR/nginx/nginx-1.14.1
cpuNum=`cat /proc/cpuinfo| grep "processor"| wc -l`
sed -i "s/{cpuNum}/$cpuNum/g"       ./conf/nginx.conf 
sed -i "s/{localIP}/$FlowHYS_IP/g"  ./conf/nginx.conf
sudo sh -c "./configure && make && make install"

sudo chown -R iotmp:iotmp /usr/local/nginx
sudo chmod 755 /usr/local/nginx/sbin/nginx


/usr/local/nginx/sbin/nginx -c /usr/local/nginx/conf/nginx.conf

if [ $? -eq 0 ];then
    echo "nginx start success!"
else
    echo "nginx start fail!"
fi

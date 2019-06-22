#!/bin/bash
# author: dyh

workdir=$(cd $(dirname $0); pwd)
sed -i "s# ##g" $workdir/00config.ini
source $workdir/00config.ini > /dev/null 2>&1
TODAY=`date "+%Y%m%d"`

mkdir -p $HOME_DIR/base/

tar zxf $TGZ_DIR/IOTMP.BaseSystem.JDK.tgz -C $HOME_DIR/base/

count=`cat /etc/profile|grep JAVA_HOME|wc -l`
if [ $count -eq 0 ];then
    echo 'JAVA_HOME=/home/iotmp/base/jdk1.8'  |sudo tee -a /etc/profile
    echo 'export PATH=${PATH}:$JAVA_HOME/bin' |sudo tee -a /etc/profile  
fi

if [ ! -h /usr/bin/java ];then
    sudo ln -s /home/iotmp/base/jdk1.8/bin/java /usr/bin/java
fi

echo "jdk install finished!"

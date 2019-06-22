#!/bin/bash


workdir=$(cd $(dirname $0); pwd)
sed -i "s# ##g" $workdir/00config.ini
source $workdir/00config.ini > /dev/null 2>&1
TODAY=`date "+%Y%m%d"`

mkdir -p $HOME_DIR/base/

pids=`sudo netstat -nltp|grep -i zookeeper|grep -w $ZOOK_PORT|awk -F'/' '{print $1}'|awk '{print $NF}'`
for pid in $pids
do
    sudo kill -9  $pid
done

if [ -d $HOME_DIR/base/zookeeper/ ];then
    if [ ! -d $BACKUP_DIR/$TODAY/zookeeper/ ];then
        mkdir -p $BACKUP_DIR/$TODAY/
        sudo mv $HOME_DIR/base/zookeeper/ $BACKUP_DIR/$TODAY/
    else
        rm -rf $HOME_DIR/base/zookeeper/
    fi
fi


tar zxf $TGZ_DIR/IOTMP.BaseSystem.Zookeeper.tgz -C $HOME_DIR/base/
sudo chown -R iotmp:iotmp $HOME_DIR/base/zookeeper/
sudo chmod -R 755 $HOME_DIR/base/zookeeper/bin/*

if [ ! -f $HOME_DIR/base/zookeeper/conf/zoo.cfg ];then
    cp $HOME_DIR/base/zookeeper/conf/zoo_sample.cfg $HOME_DIR/base/zookeeper/conf/zoo.cfg
    line=`cat -n $HOME_DIR/base/zookeeper/conf/zoo.cfg|grep "dataDir="|awk '{print $1}'`
    old=`cat $HOME_DIR/base/zookeeper/conf/zoo.cfg|grep "dataDir="|awk -F'=' '{print $2}'`
    new=/home/iotmp/base/zookeeper/data
    sed -i "${line}s#${old}#${new}#" $HOME_DIR/base/zookeeper/conf/zoo.cfg
else
    count=`cat $HOME_DIR/base/zookeeper/conf/zoo.cfg|grep "/home/iotmp/base/zookeeper/data"|wc -l`
    if [ $count -eq 0 ];then
        line=`cat -n $HOME_DIR/base/zookeeper/conf/zoo.cfg|grep "dataDir="|awk '{print $1}'`
        old=`cat $HOME_DIR/base/zookeeper/conf/zoo.cfg|grep "dataDir="|awk -F'=' '{print $2}'`
        new=/home/iotmp/base/zookeeper/data
        sed -i "${line}s#${old}#${new}#" $HOME_DIR/base/zookeeper/conf/zoo.cfg
    fi
fi


count=`cat /etc/profile|grep zookeeper|wc -l`
if [ $count -eq 0 ];then
    sudo sed -i '$aexport PATH=${PATH}:/home/iotmp/base/zookeeper/bin' /etc/profile
fi


echo '[Unit]
Description=Zookeeper.service
After=network.target
[Service]
User=iotmp
Type=forking
Environment=ZOO_LOG_DIR=/home/iotmp/base/zookeeper/logs
Environment=PATH=/usr/local/bin:/bin:/usr/bin:/usr/local/sbin:/usr/sbin:/home/iotmp/.local/bin:/home/iotmp/bin:/home/iotmp/base/jdk1.8/bin:/home/iotmp/base/jdk1.8/bin:/home/iotmp/base/zookeeper/bin
ExecStart=/home/iotmp/base/zookeeper/bin/zkServer.sh start
ExecStop=/home/iotmp/base/zookeeper/bin/zkServer.sh stop
ExecReload=/home/iotmp/base/zookeeper/bin/zkServer.sh restart
[Install]
WantedBy=multi-user.target'|sudo tee /usr/lib/systemd/system/zookeeper.service


sudo systemctl daemon-reload
sudo systemctl enable zookeeper
sudo systemctl start zookeeper
sudo systemctl status zookeeper


echo "zookeeper install finished!"

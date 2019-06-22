#!/bin/bash

workdir=$(cd $(dirname $0); pwd)
sed -i "s# ##g" $workdir/00config.ini
source $workdir/00config.ini > /dev/null 2>&1
TODAY=`date "+%Y%m%d"`

mkdir -p $HOME_DIR/base/

pids=`sudo netstat -nltp|grep redis|grep -w $REDIS_PORT|awk -F'/' '{print $1}'|awk '{print $NF}'`
for pid in $pids
do
    sudo kill -9  $pid
done

if [ -d $HOME_DIR/base/redis/ ];then
    if [ ! -d $BACKUP_DIR/$TODAY/redis/ ];then
        mkdir -p $BACKUP_DIR/$TODAY/
        sudo mv $HOME_DIR/base/redis/ $BACKUP_DIR/$TODAY/
    else
        rm -rf $HOME_DIR/base/redis/
    fi
fi


tar zxf $TGZ_DIR/IOTMP.DataStorage.Redis.tgz -C $HOME_DIR/base/
sudo chown -R iotmp:iotmp $HOME_DIR/base/redis/
sudo chmod 755 /home/iotmp/base/redis/src/redis-server
sudo chmod 755 /home/iotmp/base/redis/src/redis-cli

count=`cat /etc/profile|grep redis|wc -l`
if [ $count -eq 0 ];then
    sudo sed -i '$aexport PATH=${PATH}:/home/iotmp/base/redis/bin' /etc/profile
fi


echo '[Unit]
Description=redis
[Service]
ExecStart=/home/iotmp/base/redis/src/redis-server /home/iotmp/base/redis/redis.conf --daemonize yes  --supervised systemd
ExecStop=/home/iotmp/base/redis/src/redis-cli -h 127.0.0.1 -p 6379 shutdown
Type=notify
User=iotmp
Group=iotmp
[Install]
WantedBy=multi-user.target'|sudo tee /usr/lib/systemd/system/redis.service


sudo systemctl daemon-reload
sudo systemctl enable redis
sudo systemctl start redis
sudo systemctl status redis


echo "redis install finished!"

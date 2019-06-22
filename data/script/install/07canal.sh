#!/bin/bash

workdir=$(cd $(dirname $0); pwd)
sed -i "s# ##g" $workdir/00config.ini
source $workdir/00config.ini > /dev/null 2>&1
TODAY=`date "+%Y%m%d"`

mkdir -p $HOME_DIR/base/

pids=`sudo netstat -nltp|grep -w 11111|awk -F'/' '{print $1}'|awk '{print $NF}'`
for pid in $pids
do
    sudo kill -9  $pid
done

if [ -d $HOME_DIR/base/canal/ ];then
    if [ ! -d $BACKUP_DIR/$TODAY/canal/ ];then
        mkdir -p $BACKUP_DIR/$TODAY/
        sudo mv $HOME_DIR/base/canal/ $BACKUP_DIR/$TODAY/
    else
        rm -rf $HOME_DIR/base/canal/
    fi
fi


tar zxf $TGZ_DIR/IOTMP.BaseSystem.Canal.tgz -C $HOME_DIR/base/
sudo chown -R iotmp:iotmp $HOME_DIR/base/canal/
sudo chmod 755 $HOME_DIR/base/canal/bin/*


line=`cat -n $HOME_DIR/base/canal/conf/dataWatcher/instance.properties|grep address|grep $MYSQL_PORT|awk '{print $1}'`
oldip=`cat $HOME_DIR/base/canal/conf/dataWatcher/instance.properties|grep address|grep $MYSQL_PORT|awk -F'=' '{print $2}'|awk -F':' '{print $1}'`
sed -i "${line}s#$oldip#$MYSQL_IP#" $HOME_DIR/base/canal/conf/dataWatcher/instance.properties


echo '[Unit]
Description=Canal.service
After=network.target
[Service]
Type=forking
User=iotmp
ExecStart=/home/iotmp/base/canal/bin/startup.sh
ExecStop=/home/iotmp/base/canal/bin/stop.sh
ExecRestart=/home/iotmp/base/canal/bin/restart.sh
[Install]
WantedBy=multi-user.target'|sudo tee /usr/lib/systemd/system/canal.service


sudo systemctl daemon-reload
sudo systemctl enable canal
sudo systemctl start canal
sudo systemctl status canal


echo "canal install finished!"

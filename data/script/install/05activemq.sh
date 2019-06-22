#!/bin/bash

workdir=$(cd $(dirname $0); pwd)
sed -i "s# ##g" $workdir/00config.ini
source $workdir/00config.ini > /dev/null 2>&1
TODAY=`date "+%Y%m%d"`

mkdir -p $HOME_DIR/base/

pids=`sudo netstat -nltp|grep -i activemq|grep -w $ACTIVEMQ_PORT|awk -F'/' '{print $1}'|awk '{print $NF}'`
for pid in $pids
do
    sudo kill -9  $pid
done

if [ -d $HOME_DIR/base/activemq/ ];then
    if [ ! -d $BACKUP_DIR/$TODAY/activemq/ ];then
        mkdir -p $BACKUP_DIR/$TODAY/
        sudo mv $HOME_DIR/base/activemq/ $BACKUP_DIR/$TODAY/
    else
        rm -rf $HOME_DIR/base/activemq/
    fi
fi


tar zxf $TGZ_DIR/IOTMP.BaseSystem.ActiveMQ.tgz -C $HOME_DIR/base/
sudo chown -R iotmp:iotmp $HOME_DIR/base/activemq/
sudo chmod 755 $HOME_DIR/base/activemq/bin/*



echo '[Unit]
Description=ActiveMQ.service
After=network.target
[Service]
Type=forking
User=iotmp
ExecStart=/home/iotmp/base/activemq/bin/activemq start
ExecStop=/home/iotmp/base/activemq/bin/activemq stop
ExecReload=/home/iotmp/base/activemq/bin/activemq restart
[Install]
WantedBy=multi-user.target'|sudo tee /usr/lib/systemd/system/activemq.service


sudo systemctl daemon-reload
sudo systemctl enable activemq
sudo systemctl start activemq
sudo systemctl status activemq


echo "activemq install finished!"

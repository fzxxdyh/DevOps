#!/bin/bash

workdir=$(cd $(dirname $0); pwd)
sed -i "s# ##g" $workdir/00config.ini
source $workdir/00config.ini > /dev/null 2>&1
TODAY=`date "+%Y%m%d"`

count=`cat /etc/sysctl.conf|grep vm.max_map_count|wc -l`
if [ $count -eq 0 ];then
    echo 'vm.max_map_count=262144'|sudo tee -a /etc/sysctl.conf
    sudo sysctl -p
fi

count=`cat /etc/security/limits.conf|grep nofile|grep 65536|wc -l`
if [ $count -eq 0 ];then
    echo '* soft nofile 65536 '|sudo tee -a /etc/security/limits.conf
    echo '* hard nofile 65536 '|sudo tee -a /etc/security/limits.conf
    sudo sh -c 'ulimit -n 65536'
fi



pids=`sudo netstat -nltp|grep -w $ES_PORT|awk -F'/' '{print $1}'|awk '{print $NF}'`
for pid in $pids
do
    sudo kill -9  $pid
done

if [ -d $HOME_DIR/elasticsearch-6.0.0/ ];then
    if [ ! -d $BACKUP_DIR/$TODAY/elasticsearch-6.0.0/ ];then
        mkdir -p $BACKUP_DIR/$TODAY/
        sudo mv $HOME_DIR/elasticsearch-6.0.0/ $BACKUP_DIR/$TODAY/
    else
        rm -rf $HOME_DIR/elasticsearch-6.0.0/
    fi
fi


tar zxf $TGZ_DIR/elasticsearch-6.0.0.tar.gz -C $HOME_DIR/
sudo chown -R iotmp:iotmp $HOME_DIR/elasticsearch-6.0.0/
sudo chmod 755 $HOME_DIR/elasticsearch-6.0.0/bin/*

line=`cat $HOME_DIR/elasticsearch-6.0.0/config/jvm.options|grep -v -E "^#|^$"|grep "\-Xms"`
sed -i "s#$line#-Xms$ES_JVM#g" $HOME_DIR/elasticsearch-6.0.0/config/jvm.options

line=`cat $HOME_DIR/elasticsearch-6.0.0/config/jvm.options|grep -v -E "^#|^$"|grep "\-Xmx"`
sed -i "s#$line#-Xmx$ES_JVM#g" $HOME_DIR/elasticsearch-6.0.0/config/jvm.options


echo '[Unit]
Description=Elasticsearch.service
After=network-online.target
[Service]
Environment=ES_HOME=/home/iotmp/elasticsearch-6.0.0
Environment=ES_PATH_CONF=/home/iotmp/elasticsearch-6.0.0/config
Environment=PID_DIR=/var/run/elasticsearch
EnvironmentFile=/home/iotmp/elasticsearch-6.0.0/config/elasticsearch.yml
WorkingDirectory=/home/iotmp/elasticsearch-6.0.0
User=iotmp
Group=iotmp
ExecStart=/home/iotmp/elasticsearch-6.0.0/bin/elasticsearch
StandardOutput=journal
StandardError=inherit
LimitNOFILE=65536
LimitNPROC=4096
LimitAS=infinity
LimitFSIZE=infinity
TimeoutStopSec=0
KillSignal=SIGTERM
KillMode=process
SendSIGKILL=no
SuccessExitStatus=143
[Install]
WantedBy=multi-user.target'|sudo tee /usr/lib/systemd/system/elasticsearch.service


sudo systemctl daemon-reload
sudo systemctl enable elasticsearch
sudo systemctl start elasticsearch
sudo systemctl status elasticsearch


echo "elasticsearch install finished!"

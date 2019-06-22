#!/bin/bash
# author:dyh

workdir=$(cd $(dirname $0); pwd)
sed -i "s# ##g" $workdir/00config.ini
source $workdir/00config.ini > /dev/null 2>&1
TODAY=`date "+%Y%m%d"`

pids=$(ps -ef|grep -v -E "grep|$0"|grep -w filebeat| awk '{print $2}')
for pid in $pids
do
    sudo kill -9  $pid
    echo "kill process $pid"
done


if [ -d ${HOME_DIR}/filebeat/ ];then
    if [ ! -d ${BACKUP_DIR}/${TODAY}/filebeat/ ];then
        mkdir -p ${BACKUP_DIR}/${TODAY}/
        sudo mv ${HOME_DIR}/filebeat/ ${BACKUP_DIR}/${TODAY}/
    else
        rm -rf ${HOME_DIR}/filebeat/
    fi
fi


tar zxf ${TGZ_DIR}/IOTMP.BaseSystem.FileBeat.tgz -C $HOME_DIR
sudo chown -R iotmp:iotmp $HOME_DIR/filebeat/
sudo chmod 755 $HOME_DIR/filebeat/filebeat


oldip=`cat $HOME_DIR/filebeat/filebeat.yml |grep 5043|awk -F'"' '{print $2}'|awk -F':' '{print $1}'|awk '{gsub(/^\s+|\s+$/, "");print}'`
sed -i "s#$oldip#$LOG_IP#g" $HOME_DIR/filebeat/filebeat.yml



echo '[Unit]
Description=filebeat.service
[Service]
User=iotmp
ExecStart=/home/iotmp/filebeat/filebeat -c /home/iotmp/filebeat/filebeat.yml
[Install]
WantedBy=multi-user.target'|sudo tee /usr/lib/systemd/system/filebeat.service

sudo systemctl daemon-reload
sudo systemctl enable filebeat
sudo systemctl start filebeat
sudo systemctl status filebeat


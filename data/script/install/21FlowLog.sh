#!/bin/bash
# author:dyh

workdir=$(cd $(dirname $0); pwd)
sed -i "s# ##g" $workdir/00config.ini
source $workdir/00config.ini > /dev/null 2>&1
TODAY=`date "+%Y%m%d"`

SERVER_NAME=FlowLog


pids=$(ps -ef|grep -v -E "grep|$0"|grep -w $SERVER_NAME| awk '{print $2}')
for pid in $pids
do
    sudo kill -9  $pid
    echo "kill process $pid"
done


if [ -d ${HOME_DIR}/${SERVER_NAME}/ ];then
    if [ ! -d ${BACKUP_DIR}/${TODAY}/${SERVER_NAME}/ ];then
        mkdir -p ${BACKUP_DIR}/${TODAY}/
        sudo mv ${HOME_DIR}/${SERVER_NAME}/ ${BACKUP_DIR}/${TODAY}/
    else
        rm -rf ${HOME_DIR}/FlowLog/
    fi
fi


tar zxf ${TGZ_DIR}/IOTMP.CAS.FlowLog-2.0.0-prod.tgz -C $HOME_DIR
sudo chown -R iotmp:iotmp /home/iotmp/FlowLog/
sudo chmod 755 /home/iotmp/FlowLog/bin/*

oldip=`cat ${HOME_DIR}/${SERVER_NAME}/config/application.properties|grep "2181"|awk -F'://' '{print $2}'|awk -F':' '{print $1}'|awk '{gsub(/^\s+|\s+$/, "");print}'`
line=`cat -n ${HOME_DIR}/${SERVER_NAME}/config/application.properties|grep '2181'|awk '{print $1}'`
sed -i  "${line}s/$oldip/$ZOOK_IP/" ${HOME_DIR}/${SERVER_NAME}/config/application.properties


# serverInfo.xml
count=`cat ${HOME_DIR}/${SERVER_NAME}/config/serverInfo.xml|grep '<address/>'|wc -l`
if [ $count -eq 1 ];then
    old='<address/>'
    new="<address>${LOCAL_IP}</address>"
    sed -i "s#$old#$new#g" ${HOME_DIR}/${SERVER_NAME}/config/serverInfo.xml
fi

count=`cat ${HOME_DIR}/${SERVER_NAME}/config/serverInfo.xml|grep '<address>'|wc -l`
if [ $count -eq 1 ];then
    old=`cat ${HOME_DIR}/${SERVER_NAME}/config/serverInfo.xml|grep '<address>'`
    new="<address>${LOCAL_IP}</address>"
    sed -i "s#$old#$new#g" ${HOME_DIR}/${SERVER_NAME}/config/serverInfo.xml
fi



echo '[Unit]
Description=FlowLog.service
[Service]
Type=forking
User=iotmp
ExecStart=/home/iotmp/FlowLog/bin/FlowLog.sh start
ExecStop=/home/iotmp/FlowLog/bin/FlowLog.sh stop
ExecReload=/home/iotmp/FlowLog/bin/FlowLog.sh restart
[Install]
WantedBy=multi-user.target'|sudo tee /usr/lib/systemd/system/FlowLog.service

sudo systemctl daemon-reload
sudo systemctl enable FlowLog
sudo systemctl start FlowLog
sudo systemctl status FlowLog


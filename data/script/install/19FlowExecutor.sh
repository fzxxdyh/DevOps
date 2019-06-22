#!/bin/bash

workdir=$(cd $(dirname $0); pwd)
sed -i "s# ##g" $workdir/00config.ini
source $workdir/00config.ini > /dev/null 2>&1
TODAY=`date "+%Y%m%d"`


SERVER_NAME=FlowExecutor

pids=$(ps -ef | grep -v -E "grep|$0"|grep "FlowExecutor"| awk '{print $2}')
for pid in $pids
do
    echo  $pid
    kill -9  $pid
done


if [ -d ${HOME_DIR}/FlowExecutor/ ];then
    if [ ! -d ${BACKUP_DIR}/${TODAY}/FlowExecutor/ ];then
        mkdir -p ${BACKUP_DIR}/${TODAY}/
        sudo mv ${HOME_DIR}/FlowExecutor/ ${BACKUP_DIR}/${TODAY}/
    else
        rm -rf ${HOME_DIR}/FlowExecutor/
    fi
fi



tar zxf  $TGZ_DIR/IOTMP.CAS.FlowExecutor-0.0.1-SNAPSHOT-dev.tgz -C $HOME_DIR/
sudo chown -R iotmp:iotmp $HOME_DIR/FlowExecutor/
sudo chmod 755 $HOME_DIR/FlowExecutor/bin/*


oldip=`cat $HOME_DIR/FlowExecutor/config/application-dev.yml|grep "jdbc:mysql"|awk -F'://' '{print $2}'|awk -F':' '{print $1}'|awk '{gsub(/^\s+|\s+$/, "");print}'`
line=`cat -n $HOME_DIR/FlowExecutor/config/application-dev.yml|grep 'jdbc:mysql'|awk '{print $1}'`
sed -i  "${line}s/$oldip/$MYSQL_IP/" $HOME_DIR/FlowExecutor/config/application-dev.yml


oldip=`cat $HOME_DIR/FlowExecutor/config/application-dev.yml|grep "zookeeperAddress"|awk -F'://' '{print $2}'|awk -F':' '{print $1}'|awk '{gsub(/^\s+|\s+$/, "");print}'`
line=`cat -n $HOME_DIR/FlowExecutor/config/application-dev.yml|grep 'zookeeperAddress'|awk '{print $1}'`
sed -i  "${line}s/$oldip/$ZOOK_IP/" $HOME_DIR/FlowExecutor/config/application-dev.yml

oldip=`cat $HOME_DIR/FlowExecutor/config/application-dev.yml|grep "host"|awk -F':' '{print $2}'|awk '{gsub(/^\s+|\s+$/, "");print}'`
line=`cat -n $HOME_DIR/FlowExecutor/config/application-dev.yml|grep 'host'|awk '{print $1}'`
sed -i  "${line}s/$oldip/$REDIS_IP/" $HOME_DIR/FlowExecutor/config/application-dev.yml


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




sudo sh -c 'echo "
[Unit]
Description=FlowExecutor.service
After=network.target
[Service]
Type=forking
User=iotmp
ExecStart=/home/iotmp/FlowExecutor/bin/FlowExecutor.sh start
ExecStop=/home/iotmp/FlowExecutor/bin/FlowExecutor.sh stop
ExecReload=/home/iotmp/FlowExecutor/bin/FlowExecutor.sh restart
[Install]
WantedBy=multi-user.target
" > /usr/lib/systemd/system/FlowExecutor.service'


sudo systemctl daemon-reload
sudo systemctl start FlowExecutor
sudo systemctl enable FlowExecutor
sudo systemctl status FlowExecutor





#!/bin/bash
# author:dyh


workdir=$(cd $(dirname $0); pwd)
sed -i "s# ##g" $workdir/00config.ini
source $workdir/00config.ini > /dev/null 2>&1
TODAY=`date "+%Y%m%d"`

mkdir -p /home/iotmp/formAtt


pids=$(ps -ef|grep -v -E "grep|$0"|grep -w FlowHYS| awk '{print $2}')
for pid in $pids
do
    sudo kill -9  $pid
    echo "kill pid:$pid"
done


if [ -d ${HOME_DIR}/FlowHYS/ ];then
    TODAY=`date "+%Y%m%d"`
    if [ ! -d ${BACKUP_DIR}/${TODAY}/FlowHYS/ ];then
        mkdir -p ${BACKUP_DIR}/${TODAY}/
        sudo mv ${HOME_DIR}/FlowHYS/ ${BACKUP_DIR}/${TODAY}/
    else
        rm -rf ${HOME_DIR}/FlowHYS/
    fi
fi


tar zxf ${TGZ_DIR}/IOTMP.UDFPlatform.FlowHYS.tgz -C $HOME_DIR
sudo chown -R iotmp:iotmp ${HOME_DIR}/FlowHYS/
sudo chmod 755 ${HOME_DIR}/FlowHYS/bin/*

oldip=`cat ${HOME_DIR}/FlowHYS/webapps/FlowHYS/WEB-INF/classes/config/system.properties|grep "3306"|awk -F'://' '{print $2}'|awk -F':' '{print $1}'|awk '{gsub(/^\s+|\s+$/, "");print}'`
line=`cat -n ${HOME_DIR}/FlowHYS/webapps/FlowHYS/WEB-INF/classes/config/system.properties|grep '3306'|awk '{print $1}'`
sed -i  "${line}s/$oldip/$MYSQL_IP/" ${HOME_DIR}/FlowHYS/webapps/FlowHYS/WEB-INF/classes/config/system.properties


oldip=`cat ${HOME_DIR}/FlowHYS/webapps/FlowHYS/WEB-INF/classes/config/system.properties|grep "2181"|awk -F'://' '{print $2}'|awk -F':' '{print $1}'|awk '{gsub(/^\s+|\s+$/, "");print}'`
line=`cat -n ${HOME_DIR}/FlowHYS/webapps/FlowHYS/WEB-INF/classes/config/system.properties|grep '2181'|awk '{print $1}'`
sed -i  "${line}s/$oldip/$ZOOK_IP/" ${HOME_DIR}/FlowHYS/webapps/FlowHYS/WEB-INF/classes/config/system.properties


oldip=`cat ${HOME_DIR}/FlowHYS/webapps/FlowHYS/WEB-INF/classes/config/system.properties|grep 'redis.host'|awk -F'=' '{print $2}'|awk '{gsub(/^\s+|\s+$/, "");print}'`
line=`cat -n ${HOME_DIR}/FlowHYS/webapps/FlowHYS/WEB-INF/classes/config/system.properties|grep 'redis.host'|awk '{print $1}'`
sed -i  "${line}s/$oldip/$REDIS_IP/" ${HOME_DIR}/FlowHYS/webapps/FlowHYS/WEB-INF/classes/config/system.properties


# serverInfo.xml
count=`cat ${HOME_DIR}/FlowHYS/webapps/FlowHYS/WEB-INF/classes/config/serverInfo.xml|grep '<address/>'|wc -l`
if [ $count -eq 1 ];then
    old='<address/>'
    new="<address>${LOCAL_IP}</address>"
    sed -i "s#$old#$new#g" ${HOME_DIR}/FlowHYS/webapps/FlowHYS/WEB-INF/classes/config/serverInfo.xml
fi

count=`cat ${HOME_DIR}/FlowHYS/webapps/FlowHYS/WEB-INF/classes/config/serverInfo.xml|grep '<address>'|wc -l`
if [ $count -eq 1 ];then
    old=`cat ${HOME_DIR}/FlowHYS/webapps/FlowHYS/WEB-INF/classes/config/serverInfo.xml|grep '<address>'`
    new="<address>${LOCAL_IP}</address>"
    sed -i "s#$old#$new#g" ${HOME_DIR}/FlowHYS/webapps/FlowHYS/WEB-INF/classes/config/serverInfo.xml
fi



echo '[Unit]
Description=FlowHYS.service
After=network.target
[Service]
Type=forking
User=iotmp
ExecStart=/home/iotmp/FlowHYS/bin/startup.sh
[Install]
WantedBy=multi-user.target'|sudo tee /usr/lib/systemd/system/FlowHYS.service

sudo systemctl daemon-reload
sudo systemctl enable FlowHYS
sudo systemctl start FlowHYS
sudo systemctl status FlowHYS


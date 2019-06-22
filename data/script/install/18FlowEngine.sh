#!/bin/bash
# author:dyh

workdir=$(cd $(dirname $0); pwd)
sed -i "s# ##g" $workdir/00config.ini
source $workdir/00config.ini > /dev/null 2>&1
TODAY=`date "+%Y%m%d"`

SERVER_NAME=FlowEngine


pids=$(ps -ef|grep -v -E "grep|$0"|grep -w $SERVER_NAME| awk '{print $2}')

for pid in $pids
do
    sudo kill -9  $pid
    echo "kill process $pid"
done


if [ -d ${HOME_DIR}/${SERVER_NAME}/ ];then
    TODAY=`date "+%Y%m%d"`
    if [ ! -d ${BACKUP_DIR}/${TODAY}/${SERVER_NAME}/ ];then
        mkdir -p ${BACKUP_DIR}/${TODAY}/
        sudo mv ${HOME_DIR}/${SERVER_NAME}/ ${BACKUP_DIR}/${TODAY}/
    else
        rm -rf ${HOME_DIR}/FlowEngine/
    fi
fi


tar zxf ${TGZ_DIR}/IOTMP.UDFPlatform.FlowEngine.tgz -C $HOME_DIR
sudo chown -R iotmp:iotmp /home/iotmp/FlowEngine/
sudo chmod 755 /home/iotmp/FlowEngine/bin/*

oldip=`cat ${HOME_DIR}/${SERVER_NAME}/webapps/FlowEngine/WEB-INF/classes/config/system.properties|grep "2181"|awk -F'://' '{print $2}'|awk -F':' '{print $1}'|awk '{gsub(/^\s+|\s+$/, "");print}'`
line=`cat -n ${HOME_DIR}/${SERVER_NAME}/webapps/FlowEngine/WEB-INF/classes/config/system.properties|grep '2181'|awk '{print $1}'`
sed -i  "${line}s/$oldip/$ZOOK_IP/" ${HOME_DIR}/${SERVER_NAME}/webapps/FlowEngine/WEB-INF/classes/config/system.properties



oldip=`cat ${HOME_DIR}/${SERVER_NAME}/webapps/FlowEngine/WEB-INF/classes/config/system.properties|grep "3306"|awk -F'://' '{print $2}'|awk -F':' '{print $1}'|awk '{gsub(/^\s+|\s+$/, "");print}'`
line=`cat -n ${HOME_DIR}/${SERVER_NAME}/webapps/FlowEngine/WEB-INF/classes/config/system.properties|grep '3306'|awk '{print $1}'`
sed -i  "${line}s/$oldip/$MYSQL_IP/" ${HOME_DIR}/${SERVER_NAME}/webapps/FlowEngine/WEB-INF/classes/config/system.properties

# update dbname
count=`cat ${HOME_DIR}/${SERVER_NAME}/webapps/FlowEngine/WEB-INF/classes/config/system.properties|grep ":3306"|grep "{"|wc -l`
if [ $count -gt 0 ];then
    old_dbname=`cat ${HOME_DIR}/${SERVER_NAME}/webapps/FlowEngine/WEB-INF/classes/config/system.properties|grep ":3306"|awk -F'{' '{print $2}'|awk -F'}' '{print $1}'|awk '{gsub(/^\s+|\s+$/, "");print}'`
    old_dbname='{'${old_dbname}'}'
    new_dbname=basisdata
    line=`cat -n ${HOME_DIR}/${SERVER_NAME}/webapps/FlowEngine/WEB-INF/classes/config/system.properties|grep ":3306"|awk '{print $1}'`
    # echo "old_db: $old_dbname  new_db: $new_dbname  line: $line "
    sed -i  "${line}s/$old_dbname/$new_dbname/" ${HOME_DIR}/${SERVER_NAME}/webapps/FlowEngine/WEB-INF/classes/config/system.properties
fi


oldip=`cat ${HOME_DIR}/${SERVER_NAME}/webapps/FlowEngine/WEB-INF/classes/config/system.properties|grep "redis.host"|awk -F'=' '{print $2}'|awk '{gsub(/^\s+|\s+$/, "");print}'`
line=`cat -n ${HOME_DIR}/${SERVER_NAME}/webapps/FlowEngine/WEB-INF/classes/config/system.properties|grep "redis.host"|awk '{print $1}'`
sed -i  "${line}s/$oldip/$REDIS_IP/" ${HOME_DIR}/${SERVER_NAME}/webapps/FlowEngine/WEB-INF/classes/config/system.properties


# serverInfo.xml
count=`cat ${HOME_DIR}/${SERVER_NAME}/webapps/FlowEngine/WEB-INF/classes/config/serverInfo.xml|grep '<address/>'|wc -l`
if [ $count -eq 1 ];then
    old='<address/>'
    new="<address>${LOCAL_IP}</address>"
    sed -i "s#$old#$new#g" ${HOME_DIR}/${SERVER_NAME}/webapps/FlowEngine/WEB-INF/classes/config/serverInfo.xml
fi

count=`cat ${HOME_DIR}/${SERVER_NAME}/webapps/FlowEngine/WEB-INF/classes/config/serverInfo.xml|grep '<address>'|wc -l`
if [ $count -eq 1 ];then
    old=`cat ${HOME_DIR}/${SERVER_NAME}/webapps/FlowEngine/WEB-INF/classes/config/serverInfo.xml|grep '<address>'`
    new="<address>${LOCAL_IP}</address>"
    sed -i "s#$old#$new#g" ${HOME_DIR}/${SERVER_NAME}/webapps/FlowEngine/WEB-INF/classes/config/serverInfo.xml
fi


echo '[Unit]
Description=FlowEngine.service
[Service]
Type=forking
User=iotmp
ExecStart=/home/iotmp/FlowEngine/bin/startup.sh
ExecStop=/home/iotmp/FlowEngine/bin/shutdown.sh
[Install]
WantedBy=multi-user.target'|sudo tee /usr/lib/systemd/system/FlowEngine.service

sudo systemctl daemon-reload
sudo systemctl enable FlowEngine
sudo systemctl start FlowEngine
sudo systemctl status FlowEngine


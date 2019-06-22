#!/bin/bash
# author:dyh

workdir=$(cd $(dirname $0); pwd)
sed -i "s# ##g" $workdir/00config.ini
source $workdir/00config.ini > /dev/null 2>&1
TODAY=`date "+%Y%m%d"`

SERVER_NAME=HyEs

pids=$(ps -ef|grep -v -E "grep|$0"|grep -w HyEs| awk '{print $2}')
for pid in $pids
do
    sudo kill -9  $pid
    echo "kill process $pid"
done


if [ -d ${HOME_DIR}/HyEs/ ];then
    TODAY=`date "+%Y%m%d"`
    if [ ! -d ${BACKUP_DIR}/${TODAY}/HyEs/ ];then
        mkdir -p ${BACKUP_DIR}/${TODAY}/
        sudo mv ${HOME_DIR}/HyEs/ ${BACKUP_DIR}/${TODAY}/
    else
        rm -rf ${HOME_DIR}/HyEs/
    fi
fi


tar zxf ${TGZ_DIR}/IOTMP.BaseSystem.HyEs-2.0.0-prod.tgz -C $HOME_DIR
sudo chown -R iotmp:iotmp ${HOME_DIR}/HyEs/
sudo chmod 755 ${HOME_DIR}/HyEs/bin/*


oldip=`cat ${HOME_DIR}/HyEs/config/application.properties|grep "3306"|sed -n '1p'|awk -F'://' '{print $2}'|awk -F':' '{print $1}'|awk '{gsub(/^\s+|\s+$/, "");print}'`
line=`cat -n ${HOME_DIR}/HyEs/config/application.properties|grep '3306'|awk '{print $1}'`
for row in $line
do
    sed -i  "${row}s/$oldip/$MYSQL_IP/" ${HOME_DIR}/HyEs/config/application.properties
done

oldip=`cat ${HOME_DIR}/HyEs/config/ElasticsearchProperties.properties|grep "3306"|sed -n '1p'|awk -F'://' '{print $2}'|awk -F':' '{print $1}'|awk '{gsub(/^\s+|\s+$/, "");print}'`
line=`cat -n ${HOME_DIR}/HyEs/config/ElasticsearchProperties.properties|grep '3306'|awk '{print $1}'`
sed -i  "${line}s/$oldip/$MYSQL_IP/" ${HOME_DIR}/HyEs/config/ElasticsearchProperties.properties



oldip=`cat ${HOME_DIR}/HyEs/config/application.properties|grep "redis.host"|awk -F'=' '{print $2}'|awk '{gsub(/^\s+|\s+$/, "");print}'`
line=`cat -n ${HOME_DIR}/HyEs/config/application.properties|grep "redis.host"|awk '{print $1}'`
sed -i  "${line}s/$oldip/$REDIS_IP/" ${HOME_DIR}/HyEs/config/application.properties


oldip=`cat ${HOME_DIR}/HyEs/config/application.properties|grep "61616"|awk -F'://' '{print $2}'|awk -F':' '{print $1}'|awk '{gsub(/^\s+|\s+$/, "");print}'`
line=`cat -n ${HOME_DIR}/HyEs/config/application.properties|grep "61616"|awk '{print $1}'`
sed -i  "${line}s/$oldip/$ACTIVEMQ_IP/" ${HOME_DIR}/HyEs/config/application.properties




oldip=`cat ${HOME_DIR}/HyEs/config/application.properties|grep "2181"|awk -F'://' '{print $2}'|awk -F':' '{print $1}'|awk '{gsub(/^\s+|\s+$/, "");print}'`
line=`cat -n ${HOME_DIR}/HyEs/config/application.properties|grep "2181"|awk '{print $1}'`
sed -i  "${line}s/$oldip/$ZOOK_IP/" ${HOME_DIR}/HyEs/config/application.properties



oldip=`cat ${HOME_DIR}/HyEs/config/ElasticsearchProperties.properties|grep "elasticearch_ip"|awk -F'=' '{print $2}'|awk '{gsub(/^\s+|\s+$/, "");print}'`
line=`cat -n ${HOME_DIR}/HyEs/config/ElasticsearchProperties.properties|grep "elasticearch_ip"|awk '{print $1}'`
sed -i  "${line}s/$oldip/$ES_IP/" ${HOME_DIR}/HyEs/config/ElasticsearchProperties.properties

oldip=`cat ${HOME_DIR}/HyEs/config/ElasticsearchProperties.properties|grep "9200"|awk -F'://' '{print $2}'|awk -F':' '{print $1}'|awk '{gsub(/^\s+|\s+$/, "");print}'`
line=`cat -n ${HOME_DIR}/HyEs/config/ElasticsearchProperties.properties|grep "9200"|awk '{print $1}'`
sed -i  "${line}s/$oldip/$ES_IP/" ${HOME_DIR}/HyEs/config/ElasticsearchProperties.properties

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
Description=HyEs.service
[Service]
Type=forking
User=iotmp
ExecStart=/home/iotmp/HyEs/bin/HyEs.sh start
ExecStop=/home/iotmp/HyEs/bin/HyEs.sh stop
[Install]
WantedBy=multi-user.target'|sudo tee /usr/lib/systemd/system/HyEs.service

sudo systemctl daemon-reload
sudo systemctl enable HyEs
sudo systemctl start HyEs
sudo systemctl status HyEs


#!/bin/bash
# author:dyh

workdir=$(cd $(dirname $0); pwd)
sed -i "s# ##g" $workdir/00config.ini
source $workdir/00config.ini > /dev/null 2>&1
TODAY=`date "+%Y%m%d"`

SERVER_NAME=logstash
PROCESS_NAME=logstash-6.0.0

pids=$(ps -ef|grep -v -E "grep|$0"|grep -w $PROCESS_NAME| awk '{print $2}')
for pid in $pids
do
    sudo kill -9  $pid
    echo "kill process $pid"
done


if [ -d ${HOME_DIR}/${PROCESS_NAME}/ ];then
    if [ ! -d ${BACKUP_DIR}/${TODAY}/${PROCESS_NAME}/ ];then
        mkdir -p ${BACKUP_DIR}/${TODAY}/
        sudo mv ${HOME_DIR}/${PROCESS_NAME}/ ${BACKUP_DIR}/${TODAY}/
    else
        rm -rf ${HOME_DIR}/${PROCESS_NAME}/
    fi
fi


tar zxf ${TGZ_DIR}/IOTMP.BaseSystem.Logstash.tgz -C $HOME_DIR
sudo chown -R iotmp:iotmp $HOME_DIR/logstash-6.0.0/
sudo chmod 755 $HOME_DIR/logstash-6.0.0/bin/*

line=`cat $HOME_DIR/logstash-6.0.0/config/jvm.options|grep -v -E "^#|^$"|grep "\-Xms"`
sed -i "s#$line#-Xms$LOG_JVM#g" $HOME_DIR/logstash-6.0.0/config/jvm.options

line=`cat $HOME_DIR/logstash-6.0.0/config/jvm.options|grep -v -E "^#|^$"|grep "\-Xmx"`
sed -i "s#$line#-Xmx$LOG_JVM#g" $HOME_DIR/logstash-6.0.0/config/jvm.options


oldip=`cat ${HOME_DIR}/${PROCESS_NAME}/bin/mysql/jdbc13.conf|grep "3306"|sed -n '1p'|awk -F'://' '{print $2}'|awk -F':' '{print $1}'|awk '{gsub(/^\s+|\s+$/, "");print}'`
line=`cat -n ${HOME_DIR}/${PROCESS_NAME}/bin/mysql/jdbc13.conf|grep '3306'|awk '{print $1}'`
for row in $line
do
    sed -i  "${row}s/$oldip/$MYSQL_IP/" ${HOME_DIR}/${PROCESS_NAME}/bin/mysql/jdbc13.conf
done


old_jar_path=`cat ${HOME_DIR}/${PROCESS_NAME}/bin/mysql/jdbc13.conf|grep "mysql-connector-java"|sed -n '1p'|awk -F'"' '{print $2}'`
new_jar_path=${HOME_DIR}/${PROCESS_NAME}/bin/mysql/mysql-connector-java-5.1.36-bin.jar
sed -i "s#${old_jar_path}#${new_jar_path}#g" ${HOME_DIR}/${PROCESS_NAME}/bin/mysql/jdbc13.conf


oldip=`cat ${HOME_DIR}/${PROCESS_NAME}/bin/mysql/jdbc13.conf|grep "9200"|sed -n '1p'|awk -F'"' '{print $2}'|awk -F':' '{print $1}'|awk '{gsub(/^\s+|\s+$/, "");print}'`
line=`cat -n ${HOME_DIR}/${PROCESS_NAME}/bin/mysql/jdbc13.conf|grep "9200"|awk '{print $1}'`
for row in $line
do
    sed -i  "${row}s/$oldip/$ES_IP/" ${HOME_DIR}/${PROCESS_NAME}/bin/mysql/jdbc13.conf
done






echo '[Unit]
Description=Logstash.service
[Service]
User=iotmp
ExecStart=/home/iotmp/logstash-6.0.0/bin/logstash -f /home/iotmp/logstash-6.0.0/bin/mysql/jdbc13.conf
[Install]
WantedBy=multi-user.target'|sudo tee /usr/lib/systemd/system/logstash.service

sudo systemctl daemon-reload
sudo systemctl enable logstash
sudo systemctl start logstash
sudo systemctl status logstash


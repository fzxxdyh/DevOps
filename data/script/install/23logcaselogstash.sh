#!/bin/bash
# author:dyh

workdir=$(cd $(dirname $0); pwd)
sed -i "s# ##g" $workdir/00config.ini
source $workdir/00config.ini > /dev/null 2>&1
TODAY=`date "+%Y%m%d"`

SERVER_NAME=logcaselogstash-6.6.2


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
        rm -rf ${HOME_DIR}/logcaselogstash-6.6.2/
    fi
fi


tar zxf ${TGZ_DIR}/IOTMP.BaseSystem.logcaseLogstash.tgz -C $HOME_DIR
sudo chown -R iotmp:iotmp /home/iotmp/$SERVER_NAME/
sudo chmod 755 $HOME_DIR/$SERVER_NAME/bin/*



if [ -f $HOME_DIR/logcaselogstash-6.6.2/bin/mysql/log_cascade.conf ];then
    configfile=$HOME_DIR/logcaselogstash-6.6.2/bin/mysql/log_cascade.conf

elif [ -f $HOME_DIR/logcaselogstash-6.6.2/config/log_cascade.conf ];then
    configfile=$HOME_DIR/logcaselogstash-6.6.2/config/log_cascade.conf
else
    echo "cannot found config file log_cascade.conf!"
    exit 1
fi



oldip=`cat $configfile |grep 9200|sed -n '1p'|awk -F'"' '{print $2}'|awk -F':' '{print $1}'|awk '{gsub(/^\s+|\s+$/, "");print}'`
sed -i  "s/$oldip/$ES_IP/g" $configfile

oldip=127.0.0.1
sed -i  "s/$oldip/$ES_IP/g" $configfile

oldip=localhost
sed -i  "s/$oldip/$ES_IP/g" $configfile


# modify jvm
jvm_file=$HOME_DIR/logcaselogstash-6.6.2/config/jvm.options

line=`cat $jvm_file|grep -v -E "^#|^$"|grep "\-Xms"`
sed -i "s#$line#-Xms$LOGCS_JVM#g" $jvm_file

line=`cat $jvm_file|grep -v -E "^#|^$"|grep "\-Xmx"`
sed -i "s#$line#-Xmx$LOGCS_JVM#g" $jvm_file


echo "[Unit]
Description=logcaselogstash.service
[Service]
User=iotmp
ExecStart=/home/iotmp/$SERVER_NAME/bin/logstash -f $configfile
[Install]
WantedBy=multi-user.target"|sudo tee /usr/lib/systemd/system/logcaselogstash.service


sudo systemctl daemon-reload
sudo systemctl enable logcaselogstash
sudo systemctl start logcaselogstash
sudo systemctl status logcaselogstash


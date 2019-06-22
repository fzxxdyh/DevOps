#!/bin/bash
# author:dyh

workdir=$(cd $(dirname $0); pwd)
sed -i "s# ##g" $workdir/00config.ini
source $workdir/00config.ini > /dev/null 2>&1
TODAY=`date "+%Y%m%d"`

if [ -d ${HOME_DIR}/FlowHYSUI/ ];then
    TODAY=`date "+%Y%m%d"`
    if [ ! -d ${BACKUP_DIR}/${TODAY}/FlowHYSUI/ ];then
        mkdir -p ${BACKUP_DIR}/${TODAY}/
        sudo mv ${HOME_DIR}/FlowHYSUI/ ${BACKUP_DIR}/${TODAY}/
        mkdir ${HOME_DIR}/FlowHYSUI/
    else
        rm -rf ${HOME_DIR}/FlowHYSUI/*
    fi
else 
    mkdir -p $HOME_DIR/FlowHYSUI/
fi

mkdir -p $TGZ_DIR/tmp/
rm -rf $TGZ_DIR/tmp/*

unzip $TGZ_DIR/FlowHYSUI.zip -d $TGZ_DIR/tmp/
name=`ls $TGZ_DIR/tmp/`
if [ "$name"x = "FlowHYS"x ];then
    mv $TGZ_DIR/tmp/FlowHYS/ ${HOME_DIR}/FlowHYSUI/
elif [ "$name"x = "FlowHYSUI"x ];then
    mv $TGZ_DIR/tmp/FlowHYSUI/FlowHYS/ ${HOME_DIR}/FlowHYSUI/
fi


oldip=`cat ${HOME_DIR}/FlowHYSUI/FlowHYS/config.json|grep FlowHYS|awk -F'://' '{print $2}'|awk -F':' '{print $1}'|awk '{gsub(/^\s+|\s+$/, "");print}'`

sed -i "s#$oldip#$FLOWHYS_IP#g" ${HOME_DIR}/FlowHYSUI/FlowHYS/config.json

sudo chown -R iotmp:iotmp ${HOME_DIR}/FlowHYSUI/

$workdir/17nginx.sh

echo "FlowHYSUI install finished!"

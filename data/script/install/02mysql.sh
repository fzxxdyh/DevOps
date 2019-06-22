#!/bin/bash

workdir=$(cd $(dirname $0); pwd)
sed -i "s# ##g" $workdir/00config.ini
source $workdir/00config.ini > /dev/null 2>&1
TODAY=`date "+%Y%m%d"`

count=`sudo /etc/init.d/mysql status|grep "SUCCESS! MySQL running"|wc -l`
if [ $count -eq 1 ];then
    sudo /etc/init.d/mysql stop
fi



if [ -d $HOME_DIR/mysql/ ];then
    if [ ! -d $BACKUP_DIR/$TODAY/mysql/ ];then
        mkdir -p $BACKUP_DIR/$TODAY/
        sudo mv $HOME_DIR/mysql/ $BACKUP_DIR/$TODAY/
    fi
fi


tar zxf  $TGZ_DIR/IOTMP.DataStorage.MySQL.tgz -C $TGZ_DIR/
sudo chown -R iotmp:iotmp $TGZ_DIR/mysql/
mv $TGZ_DIR/mysql/  $HOME_DIR/

sudo rm -f /tmp/mysql.sock
count=`rpm -qa|grep perl-Data-Dumper|wc -l`
if [ $count -eq 0 ];then
    sudo yum -y install perl-Data-Dumper
fi


cd $HOME_DIR/mysql/
./scripts/mysql_install_db --user=iotmp --basedir=./ --datadir=./data
sudo cp -p support-files/my.cnf /etc/
sudo cp -p support-files/mysql /etc/init.d/
sudo chkconfig --add mysql
sudo chkconfig mysql on


count=`cat /etc/profile|grep "$HOME_DIR/mysql"|wc -l`
if [ $count -eq 0 ];then
    echo 'export PATH=${PATH}:$HOME_DIR/mysql/bin' |sudo tee -a /etc/profile
fi

source /etc/profile


sudo service mysql start

mysqladmin -u root password '123456' > /dev/null 2>&1

sql="
delete from mysql.user where user=''; 
create database basisdata default charset 'utf8'; 
create database elasticsearch_table_correlation default charset 'utf8'; 
create database timejob default charset 'utf8'; 
grant  all  on  *.*  to  root@'%' identified by '123456'; 
grant  all  on  *.*  to  canal@'%' identified by 'canal'; 
grant  all  on  *.*  to  canal@'127.0.0.1' identified by 'canal'; 
grant  all  on  *.*  to  canal@'localhost' identified by 'canal'; 
commit;
flush privileges;
"

mysql -uroot -p123456 -e "$sql"



echo "mysql install finished"

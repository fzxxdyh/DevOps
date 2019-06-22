import pymysql
import threading

def open_db_conn(ip, port, database, username, passwd,):
    connect = pymysql.connect(host=ip, port=port, database=database, user=username,
                              password=passwd, charset="utf8")
    return connect

def insert_data(conn, start, end):
    cur = conn.cursor()
    for i in range(start, end, 1):
        name = 'test%s' % str(i)
        sql = '''insert into history(h_c_id, h_c_d_id, h_c_w_id, h_d_id, h_w_id, h_date, h_amount, h_data) values(%d, %d, %d, %d, %d, "%s", %f, "%s")''' % \
              (i, 10, 5, 3, 100, '2019-01-01 08:30:00', 9.46, name)
        #print(sql)
        cur.execute(sql)
        if i % 50000 == 0:
            conn.commit()
            print(i)
    conn.commit()
    cur.close()
    conn.close()

if __name__ == "__main__":
    ip = '192.168.8.86'
    port = 8066
    database = 'tpcctest'
    username = 'root'
    passwd = '123456'
    thread_list = []
    start = 1
    end = 1000001
    for i in range(20):
        conn = open_db_conn(ip, port, database, username, passwd)
        t = threading.Thread(target=insert_data, args=(conn, start, end))
        start = start + 1000000
        end = end + 1000000
        thread_list.append(t)

    for t in thread_list:
        t.start()

    print("main end!")


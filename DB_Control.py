# -*- coding: utf-8 -*-
"""
Created on Wed Apr 26 07:42:11 2023

@author: harry
"""

import psycopg2
import pandas as pd
from datetime import datetime
from contextlib import contextmanager
import rolltools_api_0717 as api

credential_pool = [
    {'appid':'uxnxyhgkujxpgqbt','secret':'UHJqRjR6S25DaSttRWxZUElSbnovUT09'},
    {'appid':'ljsuumpnlndfcgkp','secret':'shA51m3OLRkHsloqJOBYmJupEHaFR6XT'},
    # 添加更多的認證
]

current_credential_index = 0  # 初始使用第一組認證

    
def get_next_credential():
    global current_credential_index
    credential = credential_pool[current_credential_index]
    current_credential_index = (current_credential_index + 1) % len(credential_pool)
    return credential

def create_connection():
    return psycopg2.connect(database="DIMO", user="harry", password="910615", host="127.0.0.1", port="5432")

@contextmanager
def db_connection():
    conn = create_connection()
    try:
        yield conn
    finally:
        conn.close()

def check_user_in_userInfo(user_id):
    sql=f""" select user_id from user_info where user_id='{user_id}'"""
    with db_connection() as conn:
        cur = conn.cursor()
        cur.execute(sql)
        result=cur.fetchall()
    if(len(result)==0):
        # print(result)
        return False
    else:
        # print(result)
        return True
    
# conn = psycopg2.connect(database="DIMO", user="harry", password="910615", host="127.0.0.1", port="5432")
# print ("Opened database successfully")
# db=conn.cursor()
def create_table(conn, table_name):
    # 使用連線建立游標
    cur = conn.cursor()

    # 建立資料表的 SQL 語句
    create_table_query = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(255),
            date date, 
            time time, 
            food_name VARCHAR(255), 
            food_id VARCHAR(255), 
            calories DOUBLE PRECISION, 
            protein DOUBLE PRECISION, 
            fat DOUBLE PRECISION, 
            carbohydrates DOUBLE PRECISION,
            quantity DOUBLE PRECISION
            
        );
    """

    # 執行 SQL 語句
    cur.execute(create_table_query)

    
    return True

def record2db(quantity,keyword,uid):
    credential=get_next_credential()
    now = datetime.now()
    current_time=str(now.month)+str(now.day)
    table_name='dimorecord'+current_time
    
    with db_connection() as conn:
        result=api.query(credential.get('appid'),credential.get('secret'),keyword,False,False)
        cur=conn.cursor()
        date = now.date()
        time = now.time()
        sql = f"""INSERT INTO {table_name} (user_id, date, time, food_name, food_id, calories, protein, fat, carbohydrates,quantity)
        values('{uid}','{date}','{time}','{result.get('name')}','{keyword}','{result.get('calory')}','{result.get('protein')}','{result.get('fat')}','{result.get('carb')}',{quantity}) """
        
        commition=create_table(conn, table_name)
        if commition:
            cur.execute(sql)
            conn.commit()
            print(f'CreateTableSuccessful/nTable:{table_name}')
            return True
        else:
            print('CreateTableFaild')
            return False
        cur.close()
def record2dbWithCData(uid,foodinfo):
    now = datetime.now()
    current_time=str(now.month)+str(now.day)
    table_name='dimorecord'+current_time
    
    with db_connection() as conn:
        cur=conn.cursor()
        date = now.date()
        time = now.time()
        sql = f"""INSERT INTO {table_name} (user_id, date, time, food_name, calories, protein, fat, carbohydrates,quantity)
        values('{uid}','{date}','{time}','{foodinfo['食品名稱']}','{foodinfo['熱量']}','{foodinfo['蛋白質']}','{foodinfo['脂質']}','{foodinfo['碳水化合物']}','{foodinfo['份量']}') """
        
        commition=create_table(conn, table_name)
        if commition:
            cur.execute(sql)
            conn.commit()
            print(f'CreateTableSuccessful/nTable:{table_name}')
            return True
        else:
            print('CreateTableFaild')
            return False
        cur.close()
        
def updateQuantity(quantity,foodID,uid):
    
    now = datetime.now()
    time=now.time()
    current_time=str(now.month)+str(now.day)
    table_name='dimorecord'+current_time
    
    with db_connection() as conn:
        cur=conn.cursor()
        
        sql =f"""UPDATE {table_name}
                SET quantity = {quantity}
                WHERE food_id = '{foodID}' and user_id='{uid}' and time='{time}';"""
        cur.execute(sql)
        conn.commit()
        cur.close()
    return True

def queryfromDB(date,uid):
    try:
        now = datetime.now()
        if date=='today':
            now = datetime.now()
            current_time=str(now.month)+str(now.day)
            table_name='dimorecord'+current_time
        
            sql=f"""select * from {table_name} 
                    where  user_id='{uid}'
                    ORDER BY id ASC
                """
        else:
            monthAndDay=date[5:]
            month,day=monthAndDay.split("-")
            
            table_name='dimorecord'+month+day
            print(table_name)
            sql=f"""select * from {table_name} 
                    where  user_id='{uid}'
                    ORDER BY id ASC
                """
        with db_connection() as conn:
            cur=conn.cursor()
            cur.execute(sql)
            result=cur.fetchall()
            cur.close()
        
        return result
    except psycopg2.errors.UndefinedTable:
        return 'noTable'

def deleteData(user_id,itemId,foodName,date):
    try:
        monthAndDay=date[5:]
        month,day=monthAndDay.split("-")
        
        table_name='dimorecord'+month+day
        sql=f"""delete from {table_name} where id ='{itemId}' and user_id ='{user_id}' and food_name='{foodName}'   """
        
        with db_connection() as conn:
            cur=conn.cursor()
            cur.execute(sql)
            conn.commit()
            cur.close()
        
        return True
    except:
        print('刪除資料時發生錯誤')
        return False
    
def record_userInfo2Table(user_id,user_info):
    sql=f"""
        INSERT INTO user_info (user_id, gender, height, weight, exercise_intensity, fitness_goal)
        VALUES ('{user_id}', '{user_info['性別']}','{user_info['身高']}','{user_info['體重']}','{user_info['平均運動強度']}','{user_info['體態目標']}')
        """ 
    with db_connection() as conn:
        cur=conn.cursor()
        cur.execute(sql)
        conn.commit()
        cur.close()
    return True

if __name__=='__main__':
    result=queryfromDB('today','Ub5136c58845e8760da3979c36d8dbb5b' )
    print(len(result))
    print(result)
    print(result[1][3])
    #     None
    # queryfromDB('today', 'AM', 'Ub5136c58845e8760da3979c36d8dbb5b')
#     r=get_items('蘋果')
#     print(r)
#     db.close()
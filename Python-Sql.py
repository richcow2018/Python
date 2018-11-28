#!/usr/bin/env python
# coding: utf-8

# In[20]:


import mysql.connector

# connect to the COMP MySQL server, again, the account is mine, replace the user and password with your MySQL account
conn_remote = mysql.connector.connect(host='',database='',user='',password='')
if conn_remote.is_connected():
    print('Connected to MySQL database')


# In[21]:


import mysql.connector
from mysql.connector import MySQLConnection, Error

def query_with_fetchall():
    try:
        conn = mysql.connector.connect(host='',database='',user='',password='')
        cursor = conn.cursor()
        cursor.execute("* FROM customers order by creditLimit DESC limit 10 ")
 
        rows = cursor.fetchall()
 
        for row in rows:
            print(row)
            
    except Error as e:
        print(e)
 
    finally:
        cursor.close()
        conn.close()

query_with_fetchall()


# In[47]:


# Here is an example about uploading BLOB
import mysql.connector
from mysql.connector import MySQLConnection, Error

def read_file(filename):
    with open(filename, 'rb') as f:
        photo = f.read()
        print(type(photo))
    return photo

conn = mysql.connector.connect(host='mysql.comp.polyu.edu.hk',database='17005589g',user='17005589g',password='oxcdcrlp')
cursor = conn.cursor()

query = "UPDATE productlines SET image = %s WHERE productline = 'Planes'"
args = (read_file("/Users/jimmychu/Downloads/ship.jpg"),)

cursor.execute(query, args)
conn.commit()

cursor.close()
conn.close()


# In[49]:


# Here is an example about retrieving BLOB
import mysql.connector
from mysql.connector import MySQLConnection, Error
import io
from PIL import Image

def write_file(data, filename):
    with open(filename, 'wb') as f:
        f.write(data)

conn = mysql.connector.connect(host='',database='',user='',password='',use_unicode=False)
cursor = conn.cursor()

query = "SELECT image FROM productlines WHERE productline = 'Planes'"
cursor.execute(query)
image_byte = cursor.fetchone()[0]

write_file(image_byte,r"/Users/jimmychu/Downloads/ship2.jpg")

image = Image.open(io.BytesIO(image_byte))
image.show()

cursor.close()
conn.close()


# In[ ]:





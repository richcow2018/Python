## Date: 22 Mar 2019
## Author: Jimmy Chu
## question 3 assignment 2

## system library import
from sqlite3 import dbapi2 as sqlite
import sys
import os
from collections import namedtuple

## variable declaration
dbFilePath = "/Users/jimmychu/Documents/PythonProgram/asgn2/q3.db"
csvFilePath = "/Users/jimmychu/Documents/PythonProgram/asgn2/output.txt"

DATABASE_SCHEMA = """
    CREATE TABLE if not exists patientProfile
    (
    ID            INTEGER PRIMARY KEY AUTOINCREMENT,
    Last_Name     VARCHAR(64),
    First_Name    VARCHAR(64),  
    Hong_Kong_ID  INTEGER UNIQUE,
    Mobile_No     INTEGER,
    Address       VARCHAR(64),
    DOB           INTEGER,
    Gender        VARCHAR[64],
    unique (Last_Name)
    );"""

dummyData = "INSERT INTO patientProfile (Last_Name,First_Name,Hong_Kong_ID,Mobile_No,Address,DOB,Gender) \
VALUES ('Jimmy5', 'Chu5', 'h123456(N)', 91234778, 'asdfasweasfdafdasdfasdf', 2342, 'Male');"

customData = "INSERT INTO patientProfile (Last_Name, First_Name, Hong_Kong_ID, Mobile_No, Address, DOB, Gender) \
VALUES (?, ?, ?, ?, ?, ?, ?)"

selectAll = 'select * from patientProfile'

## this is the class for initializing and accessing the database
class DB:

  def __init__(self):
    try:
      self.con = sqlite.connect(dbFilePath)
    except sqlite.Error as e:
      print 'Error Exception:', e
    
  def query(self, sqlCommand):
    try:
      cur = self.con.cursor()
      cur.execute(sqlCommand)
      data = cur.fetchall()
      if not data:
        self.con.commit()
      return data
    except sqlite.Error as e:
      print 'Error Exception:', e

  def printRecord(self, sqlCommand):
    try:
      rdata = self.query(sqlCommand)
      for row in rdata:
        print row
        raw_input("\nPress Enter to continue...\n")
    except sqlite.Error as e:
      print 'Error Exception:', e

  def addNewRecord(self, field, value):
    try:
      cur = self.con.cursor()
      cur.execute(field, value)
      self.con.commit()
      print '\nRecord Inserted'
    except sqlite.Error as e:
      print 'Error Exception:', e
      
  def exportRecord(self, sqlCommand):
    try:
      with open(csvFilePath, 'w+') as fb: 
        c = self.query(sqlCommand)
        for row in c:
          a = str(row)
          fb.write(a)
        print '\nExported to', csvFilePath 
    except:
      raise

  def tableFields(self):
    try:
      lName = raw_input("Last Name: ")
      fName = raw_input("First Name: ")
      hkID = raw_input("Hong Kong ID (integer only): ")
      mNumber = raw_input("Mobile Number (integer only): ")
      Addr = raw_input("Address: ")
      dateOfBirth = raw_input("Date of Birth (integer only): ")
      sGen = raw_input("Gender: ")
      stringData = "(" + lName, fName, hkID, mNumber, Addr, dateOfBirth, sGen + ")"
      self.addNewRecord(customData, stringData)
    except sqlite.Error as e:
      print 'Error Exception:', e
      
  def disconnect(self):    
    try:
      self.con.close()
    except sqlite.Error as e:
      print 'Error Exception:', e

## this is the class for displaying Menu and option handling
class Menu():

    Option = namedtuple('Option', 'label')
    _menuOpt = {'1': Option("Add a new patient record"), '2': Option("View existing patient record(s)"),
                '3': Option("Export patient records to text file"), '4': Option("Exit the system")}

    def printHeader(self):
        print "\n *** Please Select An Option ***\n"

    def printMainMenu(self):
        self.printHeader()
        for option in sorted(self._menuOpt.keys()):
            print "{0} {1}".format(option, self._menuOpt[option].label)

    def prompt(self):
        return raw_input("Select Option: ")

    def exeInput(self, choseOption):
        db = DB()
        try:            
            if choseOption == '3':
              db.exportRecord(selectAll)             
            elif choseOption == '2':
              db.printRecord(selectAll)
            elif choseOption == '1':
              db.tableFields()
            elif choseOption == '4':               
              print self._menuOpt[choseOption].label
              sys.exit(1)
            else:
              print "\nplease enter correct options 1-4"
        except:
          raise

# Start Menu display
menu = Menu()

while True:
  menu.printMainMenu()
  menu.exeInput(menu.prompt())


#initial the DB conn
db = DB()


#the end of program
db.disconnect()
sys.exit(1)

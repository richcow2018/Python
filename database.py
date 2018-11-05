## Purpose: sync between AD and AIHR database
## since the this server can't connect to AIHR database, it will use the exported CSV file from AIHR databse 
## editor: Jimmy Chu
## Date: 30Aug2018

import cx_Oracle
import csv
import time
from ldap3 import Connection, Server, SIMPLE, SYNC, SUBTREE, ALL, MODIFY_REPLACE

## AIHR Database info 
ip = ''
port = 
SID = ''
user = ''
psw = ''
dsn_tns = cx_Oracle.makedsn(ip, port, SID)

## AD connection info
server = Server('abc.com', get_info=ALL)
filter = "(&(objectclass=person)(userAccountControl=66048))"
#filter = "(&(objectclass=person)(userAccountControl=66050))"  ## pull the inactive users
# filter = '(&(objectCategory=*)(sAMAccountName=r*))'
base_dn = "DC=abc,DC=com"
user_dn = "CN=user.name,OU=ProQC,OU=Users,OU=AI,DC=abc,DC=com"
password = "password"

## file info
filepath = "C:\\Users\\user.name\\Desktop\\oracle\\aihr.csv"
csvFileResult = []
searchParameters = { 'search_base': base_dn,
                     'search_filter': filter,
                     'attributes': ['mail','company','manager','department','description','title', 'userAccountControl'] }


class DB:
    def __init__(self):
        try:
            self.DBconn = cx_Oracle.connect(user, psw, dsn_tns)
        except cx_Oracle.DatabaseError as e:
            error, = e.args
            print(error.code)
            raise
            
    def query(self, query):
        cursor = self.DBconn.cursor()
        result = cursor.execute(query)
        return result
    
    def disconnect(self):    
        try:
            self.DBconn.close()
        except cx_Oracle.DatabaseError as e:
            error, = e.args
            print(error.code)
            raise

class AD:
	def __init__(self):
		try:
			self.ADconn = Connection(server, user_dn, password, auto_bind=True)
		except core.exceptions.LDAPBindError as e:
			print('LDAP Bind Failed: ', e) 
			raise
		
	def ADsearch(self, searchParameters):
		#self.ADconn.search(**searchParameters)  ## max is 1000 record
		#result = self.ADconn.response
		result = self.ADconn.extend.standard.paged_search(**searchParameters)  ## retrieve more than 1000 record
		return result

	def disconnect(self):
		self.ADconn.unbind()

## read CSV file into variable		
with open(filepath, "r") as csvfile: 
	data = csv.reader((line.replace('\0','') for line in csvfile), delimiter=",")
	for row in data:
		try:
			if row[3] != "":
				csvFileResult.append(row)
		except IndexError:
			pass
		continue
	
	
## instantiate AIHR Database connection, since ADDS can't connect 
## db = DB()
# c = db.query("select table_name from all_tables")
## c = db.query("select * from fimaster.vw_acct_emp WHERE fimaster.vw_acct_emp.status = 'Active'")
##for row in c:
##    print(row[3])
## db.disconnect()

## instantiate AD connection
ad = AD()
adResultOuter = ad.ADsearch(searchParameters)

h = 0

## start to search in AD records
for i in adResultOuter:

	## will step into main process if attribute key is in AD record 
	if 'attributes' in i.keys(): 
		adEmailOutputOuter=''.join(str(e) for e in i['attributes']['mail'])  ## covert list type into string type
		
		## only email attribute in AD is not empty and will go to the loop for looking employee detail from CSV file
		if adEmailOutputOuter != "":    
			for j in range(len(csvFileResult)):  ## loop in record range in CSV file
				if csvFileResult[j][3].lower() == adEmailOutputOuter.lower():   ## compare AD email and csv email address
					
					## deparment information update
					csvDept = csvFileResult[j][4]   ## store department info into temp variable from csv file
					adDeptOutput=''.join(str(e) for e in i['attributes']['department'])   ## convert list type into string type
					
					## if it is an empty department in AD, will to go update it from csv file
					##if adDeptOutput == "":
					adReturn = ad.ADconn.modify(i['dn'],{'department': (MODIFY_REPLACE, [csvDept])})
					
					## ****** START -- custom modification for changing any field  ******** # 
					# adManagerOutput=''.join(str(e) for e in i['attributes']['manager'])   ## convert list type into string type
					# if adManagerOutput == "":
					#try:
						#print(i)
					#	print(" userAccountControl ", i['attributes']['userAccountControl'], " email ", i['attributes']['mail'], " manager ", i['attributes']['manager'])
					#	adReturn = ad.ADconn.modify(i['dn'],{'manager': (MODIFY_REPLACE, ['CN=James.Bond,OU=IT,OU=Users,OU=AI,DC=abc,DC=com'])})
						#adReturn = ad.ADconn.modify(i['dn'],{'manager': (MODIFY_REPLACE, [''])})
					#	print(" adReturn ", adReturn)		
						
					#except KeyError:
					#	pass
					#continue
					 
					# print(" userAccountControl ", i)
					# print(" adReturn ", adReturn)
					#break 
					## ****** END -- custom modification for changing any field  ******** # 
					
					
					## Job title information update
					csvJobTitle = csvFileResult[j][8]   ## store Job title info into temp variable from csv file
					adJobOutput=''.join(str(e) for e in i['attributes']['title'])  ## convert list type into string type
					
					## if it is an empty job title in AD, will to go update it from csv file
					##if adJobOutput == "":
					adReturn = ad.ADconn.modify(i['dn'],{'title': (MODIFY_REPLACE, [csvJobTitle])})

				    ## Manager information update
					csvManagerName = csvFileResult[j][11].replace(' ', '.')  ## get the manager name from csv file and join into correct email format
					csvManagerName = csvManagerName + str('@abc.com')				
					
					# adManagerName = i['attributes']['manager']
					# adManagerNameOutput = ''.join(str(e) for e in adManagerName) ## convert list type into string type 
					
					## if it is an empty manager in AD, will to go update it from csv file
					adResultInner = ad.ADsearch(searchParameters)
					
					## nested loop to compare AD manager and CSV manager
					for k in adResultInner:
						h += 1
						try:
							adEmailOutputInner = ''.join(str(f) for f in k['attributes']['mail']) 
							if csvManagerName.lower() == adEmailOutputInner.lower():
								adManagerTemp = k['dn']  ## store the user dn in to temp variable
								adReturn = ad.ADconn.modify(i['dn'],{'manager': (MODIFY_REPLACE, [adManagerTemp])})
								## adReturn = True
								## print(" adReturn ", adReturn, " counter = ", h, " adManagerTemp = ", adManagerTemp, " adEmailOutputInner = ", adEmailOutputInner.lower(), " csvManagerName = ", csvManagerName.lower())
						except KeyError:
							pass
						continue
						
		
		
## disconnect the AD and exit		
ad.disconnect()
	
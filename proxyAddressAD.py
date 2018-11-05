## Purpose: add proxyAddresses in AD
## editor: Jimmy Chu
## Date: 9Oct2018

import time
from ldap3 import Connection, Server, SIMPLE, SYNC, SUBTREE, ALL, MODIFY_REPLACE, MODIFY_ADD

## AD connection info
server = Server('abc.com', get_info=ALL)
filter = "(&(objectclass=person)(userAccountControl=66048))"
#filter = "(&(objectclass=person)(userAccountControl=66050))"  ## pull the inactive users
# filter = '(&(objectCategory=*)(sAMAccountName=r*))'
base_dn = "DC=abc,DC=com"
user_dn = "CN=user.name,OU=ProQC,OU=Users,OU=AI,DC=abc,DC=com"
password = "XXXXXXXXXX"


searchParameters = { 'search_base': base_dn,
                     'search_filter': filter,
                     'attributes': ['mail','userAccountControl', 'proxyAddresses', 'sAMAccountName'] }


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



## instantiate AD connection
ad = AD()
adResultOuter = ad.ADsearch(searchParameters)


## start to search in AD records
for i in adResultOuter:
	
	## will step into main process if attribute key is in AD record 
	if 'attributes' in i.keys(): 

		qimaSMTP = 'smtp:' + i['attributes']['sAMAccountName'] + '@ABC.com'

		try:
			adReturn = ad.ADconn.modify(i['dn'],{'proxyAddresses': (MODIFY_ADD, [qimaSMTP])})
			print(adReturn)
		except KeyError:
			pass
		continue
		
		
		
## disconnect the AD and exit		
ad.disconnect()
	
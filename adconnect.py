from ldap3 import Server, Connection, ALL, NTLM

serverName = ''
domainName = ''
userName = ''
password = ''
base = 'longString'

server = Server('', get_info=ALL)
# conn = Connection(server, user="Domain\\User", password="password", authentication=“NTLM”)

filter = "(uid="+self.username + ")"
connect.search(search_base=base_dn, search_filter=filter, search_scope=SUBTREE, attributes=['cn', 'fullName', 'imHauptEmail', 'imMatrikelNr'])


for i in conn.entries:
	print('USER = {0} : {1} : {2}').format(i.sAMAccountName.values[0], i.displayName.values[0], i.userAccountControl.values[0])
	
	server = Server('', get_info=ALL)
	conn = Connection(server, user="", password="", authentication="NTLM")
	
	conn.extend.standard.who_am_i()
	
	conn = Connection(server, 'CN=user.name,OU=ProQC,OU=Users,OU=AI,DC=asiainspection,DC=com', '', auto_bind=True)
	
	CN=user.name,OU=ProQC,OU=Users,OU=AI,DC=asiainspection,DC=com
	
	conn.search('DC=asiainspection,DC=com', search_scope=SUBTREE, '(objectclass=person)')
	conn.search('DC=asiainspection,DC=com', '(objectclass=person)', attributes=['mail'])
	result = conn.response
	studentEmail = str(result[0]['attributes']['mail'][0])

	# smail = str(result[100]['raw_attributes']['mail'][0])

	conn.entries[
	
	# smail = result[100]['raw_attributes']['mail'][0]
# smail = str(smail,'utf-8')
# print(smail)
aix.yang@abc.com

from ldap3 import Server, Connection, ALL    
    def ldapsearch(i):
        try:
            conn.search('ou=people,dc=xxxx,dc=fr', '(&(objectclass=person)(uid='+i+'))', attributes=['mail', 'cn', 'uid'])
            return conn.entries[0]['mail']        
        except:
            return'uid not found'

server = Server('myldapserver_url:389')
conn = Connection(server, auto_bind=True)

ldapsearch('myUid')
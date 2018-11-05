# from ldap3 import Server, Connection, ALL, NTLM


from ldap3 import Connection, Server, SIMPLE, SYNC, SUBTREE, ALL


server = Server('abc.com', get_info=ALL)

conn = Connection(server, 'CN=user.name,OU=ProQC,OU=Users,OU=AI,DC=abc,DC=com', '', auto_bind=True)

filter = "(userAccountControl=66048)"
base_dn = "DC=abc,DC=com"

conn.search(search_base=base_dn, search_filter=filter, search_scope=SUBTREE, attributes=['mail'])

result = conn.response

for i in result:
	# smail=i['raw_attributes']['mail']
	if 'raw_attributes' in i.keys(): 
		smail=i['raw_attributes']['mail']
		output=' '.join(str(e) for e in smail)  
		if output != "":
			output=output.replace("b'", "").replace("'", "")
			print(output)
			if output == "Niki.Liu@abc.com":
				print("exit")

conn.unbind()
import re
import string

keyDict = {}

inFilePath = "/Users/jimmychu/Documents/PythonProgram/asgn2/d2013.bin"
#outFilePath = "/Users/jimmychu/Documents/PythonProgram/asgn2/q1a_out.txt"

# main logic for fetch out the required data and store into dictionary
with open(inFilePath) as fp:    
    for iterations in range(1000):
        getline = fp.readline()
        #print getline
        keyMatch = re.findall(r'^M[H|N]+\s=+\s.*', getline)        
        for keyValue in keyMatch:
            dataList = keyValue.split(" = ")
            #print type(dataList)
            temp = dataList[1:2]
            key = ''.join(str(e) for e in temp)
            temp = dataList[0:1]
            value = ''.join(str(e) for e in temp)
            keyDict[key] = value
    
# display the key and value     
for key,val in keyDict.items():
    print key, ":", val

print "\nThere are", len(keyDict), "items in total."

print "\nFinish" 


exit

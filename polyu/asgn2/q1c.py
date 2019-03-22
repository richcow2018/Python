import anydbm
import re
import string

counter = 0
inFilePath = "/Users/jimmychu/Documents/PythonProgram/asgn2/d2013.bin"
outFilePath = "/Users/jimmychu/Documents/PythonProgram/asgn2/q1c"

# Open database, creating it if necessary.
db = anydbm.open(outFilePath, 'c')

with open(inFilePath) as fp:
    for line in fp:
        #keyMatch = re.findall(r'^MH+\s=+\s.*', line)
        keyMatch = re.findall(r'^MH+\s=+\s(.*)', line)
        if keyMatch:
            counter += 1
            MH = 'MH' + str(counter)
            db[MH] = ''.join(str(e) for e in keyMatch[0:1])
            #print db.get()
            

counter = 0       

# Loop through contents. Other dictionary methods
# such as .keys(), .values() also work.
for kValue in db.keys():
    if counter >= 20:
        break
    counter = counter + 1
    print kValue, db[kValue]
    
print "\nfinish"

db.close()


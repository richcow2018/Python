import re
import string

infile = open('/Users/jimmychu/Documents/PythonProgram/asgn2/d2013.bin', "r")
outfile = open('/Users/jimmychu/Documents/PythonProgram/asgn2/q1a_out.txt', "w")
result = infile.read(500) #read first 500byte in memory
print result  #print out the first 500byte on screen)
infile.seek(5001, 0) #move the pointer to 5001 bytes
result = infile.read(199) #read 199byte into memory
outfile.write(result) #write it into outfile
infile.close()
outfile.close()
print "\nFinish" 
exit

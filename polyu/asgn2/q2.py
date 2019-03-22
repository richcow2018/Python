import anydbm
import re
import string

# variable delcaration
counter = 0
inFilePath = "/Users/jimmychu/Documents/PythonProgram/asgn2/omim.txt"
outFilePath = "/Users/jimmychu/Documents/PythonProgram/asgn2/q1c"


wordSearch = raw_input("Please enter the word to search in txt: ")

#main logic of find out the number of occurrences 
with open(inFilePath) as fp:
    for line in fp:
        returnWords = re.sub("[^0-9a-zA-Z']+", ' ', line).rstrip()
        result = returnWords.split()
          for word in result:
            if word.lower() == wordSearch.lower():
                counter += 1


if counter > 0:
    print "\nFound,", counter
else:
    print "\nNot Found"

print "\nfinish"

exit

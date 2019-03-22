def find_longest_words(para):
    print "the para value is ", para
    longestVar = 0
    for a in para:
        print "length of para", len(a)
        tempVar = len(a)        
        if tempVar > longestVar: 
            longestVar = tempVar 
            longestWord = a
    return longestWord

list = ['physics', 'chemistry', 'school', 'genius', 'Polyulibrary']
longestWord = find_longest_words(list)
print "longest is ", longestWord 
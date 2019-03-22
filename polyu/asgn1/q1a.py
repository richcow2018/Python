var1 = raw_input("Please input single character?")
varLength=len(var1)
print "the length or input variable -", var1, "is ", varLength
if varLength > 1:
    print "False and it is not single character."
elif varLength < 1:
    print "False and empty character is not acceptable."
else:
    print "True and thanks."

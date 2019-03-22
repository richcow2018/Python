def quiz(score):
    counting, score1, score2, score3 = 0, 0, 0, 0
    print "Please answer the following questions:"
    print        
    while counting < 5:
        print "Question 1"
        print
        print "What is the ICD-9 code for Diabetes Mellitus?"
        print "a. 248"
        print "b. 249"
        print "c. 250"
        answer = raw_input("Make your choice: ")
        if answer.lower() == 'c':
            print "Correct"
            score1 += 1
            break
        else:
            print "Wrong, please retry"
            counting += 1

    while counting < 5:
        print "Question 2"
        print
        print "What is the ICD-9 code for Nutritional Marasmus?"
        print "a. 261"
        print "b. 262"
        print "c. 253"
        answer = raw_input("Make your choice: ")
        if answer.lower() == 'a':
            print "Correct" 
            score2 += 1
            break
        else:
            print "Wrong, please retry"
            counting += 1
                    
    while counting < 5:
        print "Question 3"
        print
        print "What is the ICD-9 code for Disorders of lipoid metabolism?"
        print "a. 271"
        print "b. 272"
        print "c. 273"
        answer = raw_input("Make your choice: ")
        if answer.lower() == 'b':
            print "Correct" 
            score3 += 1
            break
        else:
            print "Wrong, please retry"
            counting += 1

    resultVar = score1 + score2 + score3
    
    if counting > 4:    
        print "Sorry, your limit is reached 5 times"
              
    return resultVar

finalResult = quiz(0)

print "You final score is ", finalResult
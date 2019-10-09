import tweepy #For interacting with twitter
from re import findall #For string matching
from time import sleep

def readLastSeenID(fileName):
    """
    Opens a given file that is expected to contain only an integer.
    This integer corresponds to the ID of the last seen tweet.
    This allows to bot to only repond to new tweets.
    """
    
    idFile = open(fileName, 'r')
    lastSeenID = int(idFile.read().strip())
    idFile.close()
    return lastSeenID


def writeLastSeenID(fileName, lastSeenID):
    """
    Write a given integer to a given file.
    This integer corresponds to the ID of the last seen tweet.
    This allows to bot to keep track of which tweets its already seen and reponded to so it only responds to new tweets.
    """
    
    idFile = open(fileName, 'w')
    idFile.write(str(lastSeenID))
    idFile.close()

def replyToTweets():
    """
    This contains the main logic of the bot.
    It uses the API to get all new tweets that @ mentioned the bot.
    The bot will then look for a second mentioned user and begin generating a report of that user's bad words.
    The bot will then respond to the tweet with its findings.
    """
    
    print("Getting and replying to tweets")
    lastSeen= readLastSeenID(FILE_NAME)
    print("Last seen id is {}".format(lastSeen))

    #List of all unresponded @ mentions (oldest first)
    atMentions = reversed(api.mentions_timeline(lastSeen+1, tweet_mode='extended'))
    print("Got most recent @ mentions")

    for mention in atMentions:
        print(mention.id) #ID of new tweet that we haven't seen before
        writeLastSeenID(FILE_NAME, mention.id) #Write this new tweet to the last seen file

        tweetMentions = findall("@[a-z0-9]+", mention.full_text.lower()) #List of users mentioned in tweet.
        queryingUser = mention.user.name    #Screen name (not handle) of user who sent the request
        targetUser = tweetMentions[1]       #Handle of user the querying user wants to find a report about

        if mention.id == lastSeen:  #Extra error check to make sure we are only responding to new queries
            print("We've already seen this tweet")
        elif queryingUser == "@badwordcount" or targetUser == "@badwordcount": #If the bot generates a report on itself, it causes an infite loop of tweets
            print("The bot can't query or be queried")
        elif len(tweetMentions) > 1: #If the tweet mentions two users, we can generate the report
            print("Generating report on {0} for {1}".format(targetUser,queryingUser))

            targetTimeline = api.user_timeline(targetUser, tweet_mode='extended', include_rts=False, count=100)
            targetTweets = [tweet.full_text for tweet in targetTimeline] #List of the text of the 100 most recent tweets of the targeted user

            #Count the frequency of bad words in the tweets
            count = badWordsMap(targetTweets) #returns a dictionary key=word, value=frequency sorted by frequency high to low
            print("Report Generated")

            #Generate the report as text, keeping it within the character limit of a tweet
            reply = "{0} Report for {1}'s last 100 tweets\n".format(queryingUser, targetUser)
            idx = 0
            while (idx < len(count)) and (len(reply) < 250): #We choose 250 so we don't hit the 280 limit
                reply += "{0} - {1}\n".format(count[idx][0],count[idx][1])
                idx+=1

            #Send the report as a reply to the user's tweet
            api.update_status(reply, mention.id)
            print("Finished writing tweet\n")


def badWordsMap(tweets):
    """
    Given list of strings, this function will look through each word in each list.
    If the word is in the list of bad words, then it is put in the dictionary as a key with value 1.
    If the word is already in the dictionary, the value is incremented.
    The dictionary is returned sorted by value, high to low.
    """
    
    badWordsMap = {} #dictionary key=word, value=frequency

    for tweet in tweets: #Each tweet in the list
        for word in findall(r'[\w]+', tweet.lower()): #Each word in each tweet
            stringWord = word.strip().encode("ascii") #The deplyment tool automatically will put strings as single-element list, so we have to get the value inside
            if stringWord in badWords: #If the word is a bad word, add or increment it in the map
                badWordsMap[stringWord] = badWordsMap.setdefault(stringWord,0)+1
    
    return sorted(badWordsMap.items(), key=lambda x: x[1], reverse=True)


def makeProfanity(fileName):
    """
    Given the path to a text file containing one word per line, this function will return a list of all words.
    This function should only be called once at program start.
    The list represents the order in which the words were read.
    """
    
    print("Creating bad words list")
    profanity = open(fileName,'r')
    badWords = [word.encode("ascii").strip() for word in profanity.read().split('\n')]
    
    return badWords


#Account specific variables
CONSUMER_KEY =      #REDACTED
CONSUMER_SECRET =   #REDACTED
ACCESS_KEY =        #REDACTED
ACCESS_SECRET =     #REDACTED

FILE_NAME = 'last_seen_id.txt'      #File path of last seen id file
PROFANITY_FILE = 'profanity.txt'    #File path of profanity list
badWords = makeProfanity(PROFANITY_FILE)    #List of bad words in profanity file

if not "fuck" in badWords: #Test that the list is populated and working correctly
    raise ValueError("something is wrong with the list")

#Set up auth and API objects
auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)
api = tweepy.API(auth)

#Run the program, checking for new tweets every 10 seconds
while True:
    replyToTweets()
    print("\nSLEEPING\n")
    sleep(10)

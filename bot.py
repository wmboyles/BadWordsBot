import tweepy #For interacting with twitter
from re import findall #For string matching
#from os import environ
#from expletives import badwords #For having a list of bad words
from time import sleep

def readLastSeenID(fileName):
    idFile = open(fileName, 'r')
    lastSeenID = int(idFile.read().strip())
    idFile.close()
    return lastSeenID

def writeLastSeenID(fileName, lastSeenID):
    idFile = open(fileName, 'w')
    idFile.write(str(lastSeenID))
    idFile.close()

def replyToTweets():
    print("Getting and replying to tweets")
    lastSeen= readLastSeenID(FILE_NAME)
    print("Last seen id is {}".format(lastSeen))
    atMentions = reversed(api.mentions_timeline(lastSeen+1, tweet_mode='extended')) #List of all unresponded @ mentions (oldest first)
    print("Got most recent @ mentions")

    for mention in atMentions:
        print(mention.id)
        writeLastSeenID(FILE_NAME, mention.id)

        tweetMentions = findall("@[a-z0-9]+", mention.full_text.lower())
        queryingUser = mention.user.name
        targetUser = tweetMentions[1]

        if mention.id == lastSeen:
            print("We've already seen this tweet")
        elif queryingUser == "@badwordcount" or targetUser == "@badwordcount":
            print("You the bot can't be queried or be queried")
        elif len(tweetMentions) > 1: #If it mentioned the bot and another user
            print("Generating report on {0} for {1}".format(targetUser,queryingUser))

            targetTimeline = api.user_timeline(targetUser, tweet_mode='extended', include_rts=False, count=100)
            targetTweets = [tweet.full_text for tweet in targetTimeline]

            count = badWordsMap(targetTweets)
            print("Report Generated")

            reply = "{0} Report for {1}'s last 100 tweets\n".format(queryingUser, targetUser)
            idx = 0
            while (idx < len(count)) and (len(reply) < 250): #We choose 250 so we don't hit the 280 limit
                reply += "{0} - {1}\n".format(count[idx][0],count[idx][1])
                idx+=1

            #print(reply)
            api.update_status(reply, mention.id)
            print("Finished writing tweet\n")

def badWordsMap(tweets):
    badWordsMap = {} #dictionary word word-->frequency

    for tweet in tweets:
        for word in findall(r'[\w]+', tweet.lower()):
            stringWord = word.strip().encode("ascii")
            if stringWord in badWords:
                badWordsMap[stringWord] = badWordsMap.setdefault(stringWord,0)+1
    return sorted(badWordsMap.items(), key=lambda x: x[1], reverse=True)

#Create list of profanity
def makeProfanity(fileName):
    print("Creating bad words list")
    profanity = open(fileName,'r')
    badWords = [word.encode("ascii").strip() for word in profanity.read().split('\n')]
    return badWords

#Account specific variables
CONSUMER_KEY = #REDACTED
CONSUMER_SECRET = #REDACTED
ACCESS_KEY = #REDACTED
ACCESS_SECRET = #REDACTED

#File name of .txt file storing last seen id so we don't repond multiple times
FILE_NAME = 'last_seen_id.txt'
PROFANITY_FILE = 'profanity.txt'
badWords = makeProfanity(PROFANITY_FILE)
if not "fuck" in badWords:
    raise ValueError("something is wrong with the list")

#Set up auth and API objects
auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)
api = tweepy.API(auth)

#Run the program, checking for new tweets every 15 seconds
while True:
    replyToTweets()
    print("\nSLEEPING\n")
    sleep(10)

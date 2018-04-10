import praw
from datetime import datetime
from time import sleep

r = praw.Reddit(client_id='xgSjGvaWE2xFRw',
                client_secret='CMYdDBYcnWCSlRFd13fsmZXziD8',
                redirect_uri='http://localhost:8888',
                user_agent='BrigadeSpotterTest')

print(r.auth.url(['privatemessages read identity history modposts'], 'testing', 'permanent'))

string = r.auth.authorize('N6U6M2WJqTm-8zLYbaOvpYDLdFE')

switch = 0 #toggles between 1 and 0 to ensure the script only runs max once per minute
recipeints = ['old_gold_mountain'] #for a subreddit, just enter e.g. '/r/reddit.com'
weight1 = 1 #weights can be increased or decreased to influence the importance of the various subreddits below, which affect the 'index' value
weight2 = 1
weight3 = 1
flagsubs = {'tier1':['The_Donald','ShitPoliticsSays', 'TheRedPill', 'aznidentity', 'subredditcancer'], 'tier2':['KotakuInAction', 'conspiracy', 'TumblrInAction']}
localsubs = {'tier1':['sanfrancisco', 'bayarea'], 'tier2':['oakland'], 'tier3':['California']}
weights = {'tier1': weight1, 'tier2': weight2, 'tier3':weight3}
target_sub = 'sanfrancisco'

sendtime = (18, 34) #time the script will be triggered, e.g. 5:30 AM = (5, 30), 8:05 PM = (20, 5)
resettime = (23, 59) #time that the switch above will be reset from 1 to 0

outstring = """
Author|Flagged Subs|Most Recent Flagged Comment|Flagged|Local|Index|/r/"""+target_sub+""" comments
:--|:--|:--|:--|:--|:--|:--
""" #header row for the reddit table

while True:
    if (datetime.now().hour, datetime.now().minute) == sendtime and switch == 0:
        switch = 1
        comments = {}
        subindex = 0
        #Scrub front page of the target subreddit for all contributors in the comments
        for submission in r.subreddit(target_sub).hot(limit=25):
            numcomments = 0
            subindex += 1
            submission.comments.replace_more(limit=None)
            comment_queue = submission.comments[:]  # Seed with top-level
            while comment_queue:
                comment = comment_queue.pop(0)
                numcomments += 1
                try:
                    user = comment.author.name
                except AttributeError:
                    user = 'deleted'
                if user in comments and len(comments[user]) < 6:
                    comments[user].append(comment.permalink)
                elif user in comments and len(comments[user]) > 5:
                    pass
                else:
                    comments[user] = [comment.permalink]
                comment_queue.extend(comment.replies)
            print('Thread'+str(subindex)+':', numcomments, 'comments scanned')


        authorscore = {}
        flagged_posters = []
        details = {}
        index = 0
        #Parse the past 100 comments for the users scrubbed above
        for author in comments:
            authorscore[author] = {}
            if author == 'deleted':
                pass
            else:
                for comment in r.redditor(author).comments.new(limit=100):
                    sub = comment.subreddit.display_name
                    if sub in authorscore[author]:
                        authorscore[author][sub] += 1
                    else:
                        authorscore[author][sub] = 1
                    if sub in flagsubs['tier1'] or sub in flagsubs['tier2']:
                        if author in flagged_posters:
                            pass
                        else:
                            flagged_posters.append(author)
                            details[author] = {'Subreddit':comment.subreddit.display_name, 'Comment':comment.body, 'Score':comment.score, 'Permalink':comment.permalink}
            index += 1
            print('Scanning user '+str(index)+' of '+str(len(comments)))

        #collect permalinks for comments in flagged subreddits
        flagged_comments = {}
        for user in flagged_posters:
            if user in flagged_comments:
                flagged_comments[user].append(comment.permalink)
            else:
                flagged_comments[user] = [comment.permalink]

        #build a reddit table
        rows = []
        for user in flagged_comments:
            row = ''
            total = 0.0
            flag = 0.0
            local = 0.0
            flagged_subs = ''
            for subreddit in authorscore[user]:
                total += authorscore[user][subreddit]
                if subreddit in flagsubs['tier1']:
                    flag += authorscore[user][subreddit] / weights['tier1']
                    flagged_subs += subreddit+', '
                if subreddit in flagsubs['tier2']:
                    flag += authorscore[user][subreddit] / weights['tier2']
                    flagged_subs += subreddit+', '
                if subreddit in localsubs['tier1']:
                    local += authorscore[user][subreddit] / weights['tier1']
                if subreddit in localsubs['tier2']:
                    local += authorscore[user][subreddit] / weights['tier2']
                if subreddit in localsubs['tier3']:
                    local += authorscore[user][subreddit] / weights['tier3']
            flagged_subs = flagged_subs[:-2]
            if details[user]['Score'] in [1, -1]:
                conj = 'pt'
            else:
                conj = 'pts'
            if local == 0.0:
                indexcell = '0/100 past comments in local sub'
            else:
                indexcell = str(round(flag/local, 2))[:4]
            if user == 'deleted':
                pass
            else:
                Authorcell = '['+user+'](http://reddit.com/u/'+user+')'
                Subscell = flagged_subs
                Commentcell = '**['+details[user]['Subreddit']+']('+details[user]['Permalink']+')** '+'_('+str(details[user]['Score'])+' '+conj+')_: '+details[user]['Comment'].replace('\n', '   ').replace('|', ';')
                flagcell = str(int(flag))
                localcell = str(int(local))
                divider = '|'
                row = Authorcell+divider+Subscell+divider+Commentcell+divider+flagcell+divider+localcell+divider+indexcell+divider
                index = 1
                for comment in comments[user]:
                    row += '['+str(index)+'](http://reddit.com'+comment+'), '
                    index += 1
                rows.append(row[:-2])

        for row in rows:
            outstring += row+"""
"""

        for recipient in recipeints:
            if len(rows):
                r.redditor(recipient).message('Flag Report', outstring)
            else:
                r.redditor(recipient).message('Flag Report', 'No flagged users found')

    if (datetime.now().hour, datetime.now().minute) == resettime and switch == 1:
        switch = 0
    sleep(30)

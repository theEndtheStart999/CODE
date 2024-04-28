from flask import Flask, render_template, request, session
import re
import praw
from prawcore.exceptions import NotFound
import datetime
from datetime import timezone
import time 
import praw.exceptions

app = Flask(__name__)
app.secret_key = 'jo7UwNUXScIX-359RHSUAZWSmoEK8g'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_KEY_PREFIX'] = 'Cyber App'
my_user = "Designer_Goose3398"
my_pass = "ElephantFloor44"
my_useragent = "MyClient/0.1 by MyName"
client_id = 'JNuwcf0O2kjif9Llc9lXaA'
client_secret = 'jo7UwNUXScIX-359RHSUAZWSmoEK8g'
reddit = None
LIMIT = 999999
CROP = 999999
output_list = []
POSTS_PER_PAGE = 9999999

my_subreddits = [
    "cybersecurity", "ethicalhacking", "malware", "threatintel", "blueteamsec",
    "netsec", "AskNetsec", "computerforensics", "homelab", "privacy",
    "crypto", "SocialEngineering", "hacking", "sysadmin", "networking", 
    "information_Security","MalwareAnalysis", "bugbounty", "ReverseEngineering",
    "Passwords","websec", "osint", "OPSEC", "SecurityCTF", "privacytoolsIO",
    "hardwarehacking", "Malwarebytes", "antivirus",     
]

def process_feedback(feedback):
    print("Received Feedback:", feedback)

def authenticate_reddit():
    global reddit
    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        password=my_pass,
        user_agent=my_useragent,
        username=my_user,
        check_for_async=False
    )
   
def check_submission_time(submission, time_range):
    current_time = datetime.datetime.now(timezone.utc)
    submission_time = datetime.datetime.fromtimestamp(submission.created_utc, timezone.utc)
    
    if time_range == 'hour':
        return current_time - submission_time <= datetime.timedelta(hours=1)
    elif time_range == 'day':
        return current_time - submission_time <= datetime.timedelta(days=1)
    elif time_range == 'week':
        return current_time - submission_time <= datetime.timedelta(weeks=1)
    elif time_range == 'month':
        return current_time - submission_time <= datetime.timedelta(days=30)
    elif time_range == 'year':
        return current_time - submission_time <= datetime.timedelta(days=365)
    else:
        return True 

def process_submission(i, submission):
    if not hasattr(submission.author, 'name') or submission.stickied:
     
        return ""

    entry = f"\n\nProcessing submission [{submission.permalink}]"
    entry += f"\n---\nRedditor: {submission.author.name if hasattr(submission.author, 'name') else ''}"
    entry += f"\nSubmission: {str(i)}: {submission.title}, " \
             f"score: {str(submission.score)}, " \
             f"upvote_ratio: {str(submission.upvote_ratio)}, " \
             f"num comments: {str(submission.num_comments)}"

    return entry
@app.route('/', methods=['GET', 'POST'])
def index():
    selected_subreddits = request.form.getlist('subreddit')
    filter_term_str = request.form.get('filter', '')
    filter_terms = [term.strip() for term in filter_term_str.split(',') if term.strip()]

    action = None

    if request.method == 'POST':
        action = request.form.get('action', '')

        if action == 'run_script':
            sort_method = request.form.get('sort_method', '')  
            session['sort_method'] = sort_method  
            session['selected_subreddits'] = selected_subreddits

        elif action == 'submit_feedback':
            feedback = request.form.get('feedback', '') 
            process_feedback(feedback)  
            return render_template('index.html', output_list=output_list)

        session['output_list'] = []
        time_range = request.form.get('time_range', '')  

        
        run_script(selected_subreddits, filter_terms, time_range, session.get('sort_method', ''))
        print("Session Output List:", session['output_list'])

    elif action == 'apply_filter':
        apply_filter(filter_terms)  

    page = int(request.args.get('page', 1))
    start = (page - 1) * POSTS_PER_PAGE
    end = start + POSTS_PER_PAGE

    return render_template(
        'index.html',
        selected_subreddits=selected_subreddits,
        output_list=session.get('output_list', [])[start:end],
        page=page,
        POSTS_PER_PAGE=POSTS_PER_PAGE
    )




def apply_filter(filter_terms):
    print(f"Applying filter: {filter_terms}")
    session['filter_terms'] = filter_terms
    session['output_list'] = []  

def run_script(selected_subreddits, filter_terms, time_range, sort_method):
    global reddit
    global output_list

    if reddit is None:
        authenticate_reddit()

    output_list = [] 

    try:
        for selected_subreddit in selected_subreddits:
            p = 0

            subreddit = reddit.subreddit(selected_subreddit)
            i = 0

            output_list.append(f"\n\nSubreddit: {selected_subreddit}")

            submissions = subreddit.hot(limit=LIMIT)

           
            if sort_method == 'comments':
                submissions = sorted(submissions, key=lambda x: x.num_comments, reverse=True)
            elif sort_method == 'score':
                submissions = sorted(submissions, key=lambda x: x.score, reverse=True)
            elif sort_method == 'date':
                submissions = sorted(submissions, key=lambda x: x.created_utc, reverse=True)

            for submission in submissions:
                p = p + 1
                entry = f"[{p}] "
                if (
                    hasattr(submission.author, 'name') and
                    not submission.stickied and
                    (not filter_terms or any(re.search(filter_term, submission.title) for filter_term in filter_terms))
                    and
                    (not time_range or check_submission_time(submission, time_range))
                ):
                    i = i + 1
                    entry += process_submission(i, submission)
                    output_list.append(entry)  

                    if i == CROP:
                        break

            time.sleep(2)  

        output_list.append("\nScript completed.")
        output_list.append("\n")
        output_list.append("\n")
    except praw.exceptions.RedditAPIException as e:
        output_list.append(f"Reddit API Exception occurred: {str(e)}")
    except Exception as e:
        output_list.append(f"Error occurred: {str(e)}")

    print("Output List:", output_list)

    return output_list




if __name__ == "__main__":
    app.run(debug=True)
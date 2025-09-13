
import os
import warnings
os.environ["PYTHONWARNINGS"] = "ignore"
import sys
import argparse
from dotenv import load_dotenv

try:
  base_path = os.path.abspath((os.path.dirname(__file__)))
except:
  base_path = os.path.join(os.getcwd())

print(f"Base Path: {base_path}")
sys.path.append(base_path)
from NewsFinder import NewsFinder
parser = argparse.ArgumentParser(description="To run a specific job in pipeline")
parser.add_argument('--job', type=str, required=True,
                    choices=['test-llm','get-all-data','verify-email','get-urls','get-summary','test-agent'],
                    help='Jobs to execute')

args = parser.parse_args()

load_dotenv(dotenv_path=os.path.join(base_path,".env"))
groq_api = os.getenv('GROQ_API_KEY')
open_api = os.getenv('OPEN_API_KEY')
newFindr_Obj = NewsFinder(base_path,groq_api)

if groq_api is None:
  raise ValueError("GROQ_API_KEY not found in .env file")

if open_api is None:
  raise ValueError("OPEN_API_KEY not found in .env file")


if args.job == 'test-llm':
  userQuery = input("Enter your query:")
  newFindr_Obj.Load_LLM(userQuery)

elif args.job == 'get-all-data':
  emailID = input("Enter your email ID: ")
  result = newFindr_Obj.Get_Customer_Details(emailID)
  
elif args.job == 'verify-email':
  emailID = input("Enter your email ID: ")
  interset = newFindr_Obj.Verify_Customer_Email(emailID)
  print(f"interset: {interset}")

elif args.job == 'get-urls':
  newFindr_Obj.SQLAgents()
  emailID = input("Enter your Email ID")
  no_of_urls = int(input("Enter the number of URLs required"))
  news_urls = newFindr_Obj.Fetch_News_URLs(emailID,no_of_urls)
  print(f"News URLs: {news_urls}")

elif args.job == 'get-summary':
  newFindr_Obj.SQLAgents()
  emailID = input("Enter your Email ID")
  no_of_urls = int(input("Enter the number of URLs required"))
  news_urls = newFindr_Obj.Fetch_News_URLs(emailID,no_of_urls)
  news_summary = newFindr_Obj.Generate_News_Summaries(news_urls)
  for interest, summary in news_summary.items():
    print('-'*50)
    print(f"Summary for {interest}:\n\n {summary}")

elif args.job == 'test-agent':
  newFindr_Obj.SQLAgents()
  query = input(f"Enter the query:")
  print(f"Query: {query}")
  result = newFindr_Obj.agent.run(query)
  print(f"Result: {result}")
  print('-'*50)
    





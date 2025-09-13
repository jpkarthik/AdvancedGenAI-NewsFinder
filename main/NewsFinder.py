import os
import traceback
import sqlite3
import warnings
import json
import re
from groq import Groq
from langchain_groq.chat_models import ChatGroq
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits.sql.base import create_sql_agent
from langchain_community.tools import DuckDuckGoSearchRun


warnings.filterwarnings("ignore",category=Warning,module="langchain.*")

class NewsFinder:
  def __init__(self,base_path,groq_api):
    self.agent = None
    self.grok_api_key = groq_api
    self.base_path = base_path
    self.sql_DB = SQLDatabase.from_uri(f"sqlite:///{os.path.join(self.base_path,"Database","customer.db")}")

    self.SystemMessage = "You are a helpful assistant to assistant designed to respond to user queries with accurate and concise information"
    self.model = "llama-3.3-70b-versatile"
    #self.model = 'llama-3.1-8b-instant'

#model="llama-3.3-70b-versatile",
  def Load_LLM(self,userQuery):
    try:
      client = Groq(api_key=self.grok_api_key)
      completion = client.chat.completions.create(
        model=self.model,
        messages=[
            {"role": "system", "content": self.SystemMessage},
            {"role": "user","content": userQuery}

        ],
        temperature = 0.1,
        max_completion_tokens=None,
        top_p=1,
        stream=True,
        stop=None )

      full_response = ""
      for chunk in completion:
        content = chunk.choices[0].delta.content or ""
        full_response += content
        print(content, end ="")
      print(f"\n Complete LLM response: {full_response}")
      return full_response
    except Exception as ex:
      print(f"Exception: {ex}")
      print(traceback.print_exc())

  def SQLAgents(self):
    try:

      llm_Obj = ChatGroq(api_key=self.grok_api_key,
                         model_name = self.model)

      toolkit = SQLDatabaseToolkit(db=self.sql_DB, llm=llm_Obj)

      self.agent = create_sql_agent(llm= llm_Obj,
                                    toolkit=toolkit,
                                    verbose=True)
      return self.agent

    except Exception as ex:
      print(f"Exception: {ex}")
      print(traceback.print_exc())

  def Get_Customer_Details(self,emailID):
    try:
      if emailID is None or not emailID.strip():
          raise ValueError("Email ID is not provided")
      if self.agent is None:
        self.SQLAgents()

      email_list = [email.strip() for email in emailID.split(',')]

      emailID_list = ", ".join(f" '{email}' " for email in email_list)
      print(emailID_list)
      query = f"SELECT * FROM customers  WHERE email IN ({emailID_list})"
      result = self.agent.run(query)
      if result is "I don't know":
        result = f"Email ID {emailID} not found in DB"
      print(f"Raw Result: {result}")
      return result
    except Exception as ex:
      print(f"Exception: {ex}")
      print(traceback.print_exc())

  def Verify_Customer_Email(self,emailID):
    try:
      if emailID is None or not emailID.strip():
          raise ValueError("Email ID is not provided")
      if self.agent is None:
        self.SQLAgents()

      email_list = [email.strip() for email in emailID.split(',')]

      emailID_list = ", ".join(f" '{email}' " for email in email_list)
      print(emailID_list)
      query = f"SELECT interests FROM customers WHERE email IN ({emailID_list})"
      result = self.agent.run(query)

      print(f"Raw Result: {result}")
      print(type(result))
      interests = {}
      if isinstance(result,str):
        try:
          result_patters = re.findall(r'\["[^"\]]*(?:"[^"\]]*"[^"\]]*)*"\]', result)
          for indx, interest_string in enumerate(result_patters):
            if indx < len(email_list):
              cleaned_strings = interest_string.strip('[]')
              items = re.findall(r'"([^"]*)"',cleaned_strings)
              interests[email_list[indx]] = items
        except Exception as ex:
          print(f"Exception: {ex}")
          print(traceback.print_exc())
      
      return interests

    except Exception as ex:
      print(f"Exception: {ex}")
      print(traceback.print_exc())
      return {}

  def Search_News(self,interests,no_of_urls):
    try:
      search_tool = DuckDuckGoSearchRun()

      filtered_URLS = {}

      for email,interest_list in interests.items():
        for indvidual_interest in interest_list:
          expand_query = f"latest news article on {indvidual_interest} after:2025-01-01 site:bbc.com OR site:reuters.com OR site:nytimes.com OR site:apnews.com OR site:theguardian.com"

          search_results = search_tool.run(expand_query)
          #print(f"Search Results for {interest}")

          filter_query = f"From the following search search results, extract 3-5 trustworthy news URLs(not homepage) relevant to '{indvidual_interest}' published after December 31 2024. Priortize recent, credible source like BBC, Reuters, NYT, AP, Guardian. List only the URLs: \n {search_results}"

          query_results = self.Load_LLM(filter_query)

          #print(f"Query Results: {query_results}")
          urls = re.findall(r'https?://[^\s]+',query_results)

          urls = list(dict.fromkeys(url for url in urls if url.strip().startswith("http")))

          filtered_URLS[indvidual_interest] = urls[:no_of_urls]
      #print(f"Final Filtered URLs {filtered_URLS}")
      return filtered_URLS

    except Exception as ex:
      print(f"Exception: {ex}")
      print(traceback.print_exc())

  def Fetch_News_URLs(self, emailIDs,no_of_urls):
    try:
      results_intersets = self.Verify_Customer_Email(emailIDs)
      news_urls = self.Search_News(results_intersets,no_of_urls)
      print(f"Filtered news URLs for {emailIDs}:{news_urls}")
      return news_urls
    except Exception as ex:
      print(f"Exception: {ex}")
      print(traceback.print_exc())
      return {}
      
  def Get_News_Summary(self, urls, interest):
    try:
      summary = f"Relevant Latest news on {interest}"

      citation_id =1
      for indx,url in enumerate(urls[:4],1):
        content_query = f"Extract a concise summary (4-5 sentence) of the latest news from {url}. focus only on key facts and relevance to {interest}. Return the response in format \n\n\n Title:[title] \n\n Key Points:[points] \n\n Source: [source] \n\n Date: [date] \n\n Summary:[summary]\n\n URL:[url]"

        summary_content = self.Load_LLM(content_query)

        summary += f"\n\n{summary_content}\n\n"

        # print(f"summary for {interest} Item {indx} {summary_content}")

      return summary
    except Exception as ex:
      print(f"Exception: {ex}")
      print(traceback.print_exc())
      return f"No Summary Available for {interest}"

  def Generate_News_Summaries(self, news_urls):
    try:
      news_summary = {}
      for interest, urls in news_urls.items():
        news_summary[interest] = self.Get_News_Summary(urls,interest)
        #print(f"News Summary: {news_summary}")
        return news_summary
    except Exception as ex:
      print(f"Exception: {ex}")
      print(traceback.print_exc())
  

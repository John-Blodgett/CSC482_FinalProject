import numpy as np
import pandas as pd
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import contractions

class_df = pd.read_excel("classDf.xlsx")
prof_df = pd.read_excel("profDf.xlsx")

class_df['CourseName'] = class_df['CourseName'].astype(str)
class_df['CourseName'] = class_df['CourseName'].str.replace("|", ",").str.replace("[", "").str.replace("]", "").str.split(",")
class_df["Start Time"] = pd.to_datetime(class_df[class_df["Start"] != '\xa0']["Start"])
class_df["End Time"] = pd.to_datetime(class_df[class_df["End"] != '\xa0']["End"])
 

def get_question_and_not(keyword_dict, query_tokenized):
  question_words = ["what", "where", "who", "when", "which"]
  first_question_words = ["is", "will", "does"]
  if query_tokenized[0].lower() in first_question_words:
    keyword_dict["question"] = "is"
  else:
    for i in query_tokenized:
      if i.lower() in question_words:
        keyword_dict["question"] = i.lower()
        break
  if "how" in query_tokenized and "many" in query_tokenized:
    keyword_dict["question"] = "how many"

  keyword_dict["not"] = False
  not_words = ["not"]
  for i in query_tokenized:
    if i.lower() == "not":
      keyword_dict["not"] = True
  if "question" not in keyword_dict:
    keyword_dict["question"] = "what"
  if "number" in query_tokenized or "amount" in query_tokenized:
    if keyword_dict["question"] == "what":
      keyword_dict["question"] = "how many"
      
def get_keywords(query, class_df, prof_df):
    # 
  keyword_dict = {}

  query = contractions.fix(query)
  query_tokenized = word_tokenize(query)
  get_question_and_not(keyword_dict, query_tokenized)
  stop_words = set(stopwords.words('english'))
  query_tokenized = [w for w in query_tokenized if not w.lower() in stop_words]

  courses_list = class_df['Course'].unique()
  courses_list_nums = [course.split()[-1] for course in courses_list]
  courses_list = class_df['Course'].unique()
  courses_list_code = [course.split()[0].lower() for course in courses_list]

  courses_list_code = set(courses_list_code)
  course_names = class_df[["CourseName", "Course"]]
  course_names_map = {}
  for i in range(len(course_names)):
    course_names_map[course_names.iloc[i][1]] = [j.strip() for j in course_names.iloc[i][0]]

  sections = [i.replace(u'\xa0', u'') for i in class_df["Sect"].unique()]

  time_of_day = class_df['Start'].unique()
  time_of_day = [i for i in time_of_day if len(i) > 1]
  time_of_day = [i[1] if i[0] == '0' else i[:2] for i in time_of_day]
  time_of_day = set(time_of_day)

  prof_list = prof_df['Name'].unique()
  prof_lastnames_list = [name.split(',')[0].lower() for name in prof_list]
  prof_firstnames_list = [name.split(',')[-1].lower()[1:] for name in prof_list]

  last_name_keyword = [token.lower() for token in query_tokenized if token.lower() in prof_lastnames_list]
  first_name_keyword = [token.lower() for token in query_tokenized if token.lower() in prof_firstnames_list]
  not_list = []
  raw = [i.lower() for i in word_tokenize(query)]
  if len(last_name_keyword) != 0 or len(first_name_keyword) != 0:
    keyword_dict['person'] = (last_name_keyword, first_name_keyword)
    if "not" in raw:
      if raw.index("not") < raw.index(last_name_keyword[0]):
        not_list.append(last_name_keyword)
        not_list.append(first_name_keyword)

  nums_keywords = [token for token in query_tokenized if token.isnumeric() and token in courses_list_nums]
  if len(nums_keywords) != 0:
    keyword_dict['course'] = nums_keywords[0]
    if "not" in raw:
      if raw.index("not") < raw.index(nums_keywords[0]):
        not_list.append(nums_keywords[0])

  code_keyword = [token.lower() for token in query_tokenized if token.lower() in courses_list_code]
  if len(code_keyword) != 0:
    keyword_dict['code'] = code_keyword[0]
    if "not" in raw:
      if raw.index("not") < raw.index(code_keyword[0]):
        not_list.append(code_keyword[0])

  for course in course_names_map:
    for val in course_names_map[course]:
      if " " + val.lower() + " " in query.lower() or \
       " " + val.lower() + "." in query.lower() or \
       " " + val.lower() + "?" in query.lower():
        keyword_dict['course'] = course.split()[1]
        keyword_dict['code'] = course.split()[0].lower()
        if "not" in raw:
          if raw.index("not") < raw.index(course.split()[0].lower()):
            not_list.append(course.split()[1])
            not_list.append(course.split()[0].lower())

  sections_keyword = [token for token in query_tokenized if token.isnumeric() and token in sections]
  if len(sections_keyword) != 0:
    keyword_dict['sections'] = sections_keyword
    if "not" in raw:
      if raw.index("not") < raw.index(sections_keyword):
        not_list.append(sections_keyword)

  time_keyword = [token for token in query_tokenized if ':' in token and token.replace(':', '').isnumeric()]
  if len(time_keyword) != 0:
    keyword_dict['time'] = time_keyword[0]
    if "not" in raw:
      if raw.index("not") < raw.index(time_keyword[0]):
        not_list.append(time_keyword[0])

  days_of_week = {"monday": "m", "tuesday": "t", "wednesday": "w", "thursday": "tr", "friday": "f", "saturday": "s", "sunday": "s"}
  days_keyword = [token for token in query_tokenized if token.lower() in list(days_of_week.keys())]
  if len(days_keyword) != 0:
    keyword_dict["day"] = days_of_week[days_keyword[0].lower()]
    if "not" in raw:
      if raw.index("not") < raw.index(days_of_week[days_keyword[0].lower()]):
        not_list.append(days_of_week[days_keyword[0].lower()])
  return keyword_dict, not_list

# keywords: days, week, indiv days (like Thursday), also stuff like MWF

from nltk.corpus import wordnet as wn
from nltk.stem import PorterStemmer
def get_answer_word(query):
    # 
  query_tokenized = word_tokenize(query)
  stop_words = set(stopwords.words('english'))
  query_tokenized = [w for w in query_tokenized if not w.lower() in stop_words]
  porter = PorterStemmer()
  keywords = ["time", "location", "day", "section", "phone", "credits", 'courses', 'credit', "prerequisite", "classes", "unique", "distinct", "building", "title", "office"]
  keywords = [porter.stem(i) for i in keywords]
  prof_keywords = ["professor", "professors", "faculty", "teacher", "teachers", "profs"]
  answers = []
  for i in query_tokenized:
    stemmedWord = porter.stem(i.lower())
    if stemmedWord in keywords:
      answers.append(stemmedWord)
    if stemmedWord in prof_keywords or i.lower() in prof_keywords:
      answers.append("professor")
  return answers
def time_in_range(start, end, x):
    """Return true if x is in the range [start, end]"""
    if start <= end:
        return start <= x <= end
    else:
        return start <= x or x <= end
      
def filter_df(df, col, value, how='exact'):
  if how == 'exact':
    return df[df[col] == value]
  elif how == 'contains':
    return df[df[col].str.contains(value)]
  elif how == "time":
    times_df = df[df["Start"] != '\xa0']
    if 700 <= int(value.replace(":", "")) <= 1159:
      value = value + " am"
    else:
      value = value + " pm"
    value = pd.Timestamp(value)

    keep = []
    for i in range(len(times_df)):
      if time_in_range(times_df.iloc[i]["Start Time"], times_df.iloc[i]["End Time"], value):
        keep.append(i)
    return times_df.iloc[keep]


def get_course(keyword_dict):
    # 
  if 'course' in keyword_dict and 'code' in keyword_dict:
    return keyword_dict['code'] + " " + keyword_dict['course']
  else:
    print("ERROR: NOT ENOUGH INFO TO EXTRACT COURSE")
    
def get_answer(keyword_dict, class_df_2, prof_df_2, answers, not_list):
      # add in filtering by sections here somewhere (keyword_dict["sections"])
  print(keyword_dict, answers, not_list)

  class_df = class_df_2.copy()
  prof_df = prof_df_2.copy()
  prof_df["Name"] = prof_df["Name"].str.lower()
  class_df["Name"] = class_df["Name"].str.lower()
  class_df["Course"] = class_df["Course"].str.lower()
  class_df["Days"] = class_df["Days"].str.lower()
  # class_df["CourseName"] = class_df["CourseName"].str.lower()

  if keyword_dict["not"] == False:
    if keyword_dict["question"] == "where":
      if "person" in keyword_dict and "course" not in keyword_dict:
        if "locat" in answers or "offic":
          if len(keyword_dict["person"][0]) > 0:
            prof_df = filter_df(prof_df, "Name", keyword_dict["person"][0][0], how='contains')
          if len(keyword_dict["person"][1]) > 0:
            prof_df = filter_df(prof_df, "Name", keyword_dict["person"][1][0], how='contains')
          if len(prof_df) == 0:
            return("The person specified is not a faculty member at Cal Poly.")
            
          if prof_df.iloc[0]["Office"] == '\xa0':
            return("We do not have information on where " + prof_df.iloc[0]["Name"] + "'s office is.")
            
          return(prof_df.iloc[0]["Name"] + "'s office is " + prof_df.iloc[0]["Office"] + ".")
        else:
          # assuming question is asking where does prof teach this quarter (all classes)
          if len(keyword_dict["person"][0]) > 0:
            class_df = filter_df(class_df, "Name", keyword_dict["person"][0][0], how='contains')
          if len(keyword_dict["person"][1]) > 0:
            class_df = filter_df(class_df, "Name", keyword_dict["person"][1][0], how='contains')
          if len(class_df) == 0:
            return("The person specified is not teaching this quarter.")
            
          class_df = filter_df(class_df, "Name", class_df.iloc[0]["Name"])
          locs = class_df["Location"].unique()
          locs = [loc for loc in locs if loc != '\xa0']
          return(class_df.iloc[0]["Name"] + " is teaching classes in the following locations: " + ', '.join(locs))
      elif "person" in keyword_dict and "course" in keyword_dict:
        course = get_course(keyword_dict)
        class_df = filter_df(class_df, 'Course', course)
        if len(class_df) == 0:
          return("The person specified does not teach " + course + ".")
          
        if len(keyword_dict["person"][0]) > 0:
          class_df = filter_df(class_df, "Name", keyword_dict["person"][0][0], how='contains')
        if len(keyword_dict["person"][1]) > 0:
          class_df = filter_df(class_df, "Name", keyword_dict["person"][1][0], how='contains')
        if len(class_df) == 0:
          return("The person specified does not teach " + course + ".")
          
        if class_df.iloc[0]["Location"] == '\xa0':
          return("There is no specified location for " + class_df.iloc[0]["Name"] + "'s " + course + " class.")
          
        return(class_df.iloc[0]["Name"] + " teaches " + course + " at " + ", ".join(class_df["Location"].unique()))
      elif "course" in keyword_dict:
        course = get_course(keyword_dict)
        class_df = filter_df(class_df, 'Course', course)
        
        if len(class_df) == 0:
          return("The specified course " + course + " is not a valid course.")
        return(course + " is being taught at the following locations: " + ", ".join(class_df["Location"].unique()))
      else:
        return("ERROR: CANNOT RECOGNIZE QUESTION.")

    elif keyword_dict["question"] == "when":
      if "person" in keyword_dict:
        if len(keyword_dict["person"][0]) > 0:
          class_df = filter_df(class_df, "Name", keyword_dict["person"][0][0], how='contains')
        if len(keyword_dict["person"][1]) > 0:
          class_df = filter_df(class_df, "Name", keyword_dict["person"][1][0], how='contains')
      if "day" in keyword_dict:
        class_df = filter_df(class_df, "Days", keyword_dict["day"], how='contains')
      if "course" in keyword_dict:
        course = get_course(keyword_dict)
        class_df = filter_df(class_df, 'Course', course)
      if "day" in answers:
        return("The days of the week are " + ", ".join(set(i.upper() for i in class_df["Days"])))
      else:
        s = ""

        for index, row in class_df.iterrows():
          if row["Start"] != '\xa0':
            s += (row["Course"] + "-" + row["Sect"] + "taught by " + row["Name"] + " starts at " + row["Start"] + " and ends at " + row["End"]) + " on " + row["Days"] + "\n"
        return s
    elif keyword_dict["question"] == "what":
      if "person" in keyword_dict:
        if len(keyword_dict["person"][0]) > 0:
          class_df = filter_df(class_df, "Name", keyword_dict["person"][0][0], how='contains')
          prof_df = filter_df(prof_df, "Name", keyword_dict["person"][0][0], how='contains')
        if len(keyword_dict["person"][1]) > 0:
          class_df = filter_df(class_df, "Name", keyword_dict["person"][1][0], how='contains')
          prof_df = filter_df(prof_df, "Name", keyword_dict["person"][1][0], how='contains')
      if "day" in keyword_dict:
        class_df = filter_df(class_df, "Days", keyword_dict["day"], how='contains')
      if "course" in keyword_dict:
        course = get_course(keyword_dict)
        class_df = filter_df(class_df, 'Course', course)
      if len(answers) == 0 and set(keyword_dict.keys()) == set(["code", "course", "question", "not"]):
        return(class_df.iloc[0]["CourseName"][0].strip())
      elif "day" in answers:
        return("The days of the week are " + ", ".join(set(i.upper() for i in class_df["Days"])))
      elif "prerequisit" in answers and "course" in keyword_dict:
        return(class_df["Prerequisites"].iloc[0])
      elif "time" in answers:
        s = ""
        for index, row in class_df.iterrows():
          if row["Start"] != '\xa0':
            s += (row["Course"] + "-" + row["Sect"] + " taught by " + row["Name"] + " starts at " + row["Start"] + " and ends at " + row["End"]) + "\n"
        return s
      elif ("build" in answers or "locat" in answers or "offic" in answers) and "course" in keyword_dict:
        s = ""
        for index, row in class_df.iterrows():
          if row["Location"] != '\xa0':
            s += (row["Course"] + "-" + row["Sect"] + "taught by " + row["Name"] + " is located in building " + row["Location"] ) + "\n"
        return s
      elif ("build" in answers or "locat" in answers or "offic" in answers) and "course" not in keyword_dict:
        return("The office is " + prof_df.iloc[0]["Office"])
      elif "titl" in answers:
        s = ""
        for index, row in prof_df.iterrows():
          if row["Title"] != '\xa0':
            s += (row["Name"] + " has the title: " + row["Title"] ) + "\n"
        return s
      elif "professor" in answers:
        return("The professors are " + " | ".join(class_df["Name"].unique()))
      elif "phone" in answers:
        return("The phone number is " + prof_df.iloc[0]["Phone"])
      elif "class" in answers:
        return("The classes are " + ', '.join(class_df["Course"].unique()))
      elif "section" in answers:
        secs = [sec.strip() for sec in class_df["Sect"].unique()]
        return("The sections are " + ', '.join(secs))

    elif keyword_dict["question"] == "who":
      if "time" in keyword_dict:
        class_df = filter_df(class_df, "Time", keyword_dict["time"][1][0], how='contains')
      if "day" in keyword_dict:
        class_df = filter_df(class_df, "Days", keyword_dict["day"], how='contains')
        return("On " + keyword_dict["day"] + ", here are prfessors: " + class_df["Name"].unique())
      if "course" in keyword_dict:
        course = get_course(keyword_dict)
        class_df = filter_df(class_df, 'Course', course)
        return("Here are the professors who teach " + course + ": " + " | ".join(class_df["Name"].unique()))
      
    elif keyword_dict["question"] == "how many":
      if "person" in keyword_dict:
        if len(keyword_dict["person"][0]) > 0:
          class_df = filter_df(class_df, "Name", keyword_dict["person"][0][0], how='contains')
          prof_df = filter_df(prof_df, "Name", keyword_dict["person"][0][0], how='contains')
        if len(keyword_dict["person"][1]) > 0:
          class_df = filter_df(class_df, "Name", keyword_dict["person"][1][0], how='contains')
          prof_df = filter_df(prof_df, "Name", keyword_dict["person"][1][0], how='contains')
      if "day" in keyword_dict:
        class_df = filter_df(class_df, "Days", keyword_dict["day"], how='contains')
      if "course" in keyword_dict:
        course = get_course(keyword_dict)
        class_df = filter_df(class_df, 'Course', course)
      if "credit" in answers:
        class_df = filter_df(class_df, "Credits", answers["credit"])
      if "time" in keyword_dict:
        class_df = filter_df(class_df, "Start", keyword_dict["time"], how="time")

      if "professor" in answers and "day" not in keyword_dict and "course" not in keyword_dict and \
        "credit" not in answers and "time" not in keyword_dict:
        # total csc faculty this quarter
        return("There are " + str(len(prof_df)) + " such professors.")
      elif "professor" in answers:
        # how many total professors
        return("There are " + str(len(class_df["Name"].unique())) + " such professors.")
      elif "class" in answers:
        # how many total/unique classes
        if "unique" in answers or "distinct" in answers:
          return("There are " + str(len(class_df["Course"].unique())) + " such courses.")
        else:
          return("There are " + str(len(class_df.groupby(["Course", "Sect"]).size())) + " such courses.")
      elif "section" in answers:
        # how many total sections
        return("There are " + str(len(class_df.groupby(["Course", "Sect"]).size())) + " such sections.")
      # number of prereqs is not a meaningful question to ask bc it varies for each course anyway
      return("ERROR: RESPONSE NOT RECOGNIZED.")
    elif keyword_dict["question"] == "is":
      if "person" in keyword_dict:
        if len(keyword_dict["person"][0]) > 0:
          class_df = filter_df(class_df, "Name", keyword_dict["person"][0][0], how='contains')
          prof_df = filter_df(prof_df, "Name", keyword_dict["person"][0][0], how='contains')
        if len(keyword_dict["person"][1]) > 0:
          class_df = filter_df(class_df, "Name", keyword_dict["person"][1][0], how='contains')
          prof_df = filter_df(prof_df, "Name", keyword_dict["person"][1][0], how='contains') 
      if "day" in keyword_dict:
        class_df = filter_df(class_df, "Days", keyword_dict["day"], how='contains')
      if "course" in keyword_dict:
        course = get_course(keyword_dict)
        class_df = filter_df(class_df, 'Course', course)
      if "credit" in answers:
        class_df = filter_df(class_df, "Credits", answers["credit"])
      if "time" in keyword_dict:
        class_df = filter_df(class_df, "Start", keyword_dict["time"], how="time")
      if len(class_df) < len(class_df_2) and len(class_df) > 0:
        return "Yes!"
      else:
        return "No"
        
  else:
    pass
  
  
# query = "Where is John Seng teaching ai this quarter?"
# query = "where is planck teaching classes this quarter"
# query = "where is kurfess's office located?"
# query = "when does migler teach on Friday?"
# query = "how many professors teach algorithms?"
# query = "where is csc 349 being taught?"
# query = "how many classes of cpe 315 are taught during 9:34?" # FIX: NOT FILTERING COURSE
# query = "in what building is CSC 480 taught" 
# query = "When is Andrew Migler done teaching?"
# query = "Can you tell me the location of csc 580"
# query = "What is the title of andrew migler"
# query = "what is the amount of professors teaching csc 400"
# query = "is nlp being taught by migler"
# query = "is nlp being taught by foaad"
# query = "Does James Franko teach at Cal Poly?"
# query = "Will NLP be taught by John Clements"
# query = "Is CPE 315 being taught on Saturday?"
# query = "Is cpe 315 being taught at 7:10?"
query = "who is cpe 203 taught by?"
# query = "how many sections of csc 369 are taught by anderson"
query = "who teaches grad ai?"
# query = "What is the time at which algorithms is taught"
# query = "What days is data structures taught by jones"
# query = "What are the ai professors"
# query = "What are the algorithms professors"
# query = "What is fooad's phone"
# query = "where is foaad's office"
# query = "what is foaad's office"
# query = "What is the location of cpe 202"
# query = "Is irene teaching on wednesday"
# query = "When is irene teaching"
# query = "What classes are being taught by seng"
# query = "What is csc 430"
# query = "What sections of algorithms is migler teaching"

def getAnswer(query):

  keyword_dict, not_list = get_keywords(query, class_df, prof_df)
  answers = get_answer_word(query)
  try:
    answer = get_answer(keyword_dict, class_df, prof_df, answers, not_list)
    if not answer:
      answer = "Invalid query, try another one!"
  except:
    answer = "Invalid query, try another one!"
  return (answer)


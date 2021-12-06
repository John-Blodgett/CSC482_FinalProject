import numpy as np
import pandas as pd
import nltk
from nltk.corpus import stopwords


from bs4 import BeautifulSoup
import requests

f = open('orig_data.txt', 'r')
new_lines = []
for line in f.readlines():
  if not ('stat' in line.lower() and 'csse' not in line.lower()):
    new_lines.append(line)

f_out = open('processed_data.txt', 'w')
f_out.write(''.join(new_lines))
f_out.close()

f_sched = open('schedules.html', 'r')
soup = BeautifulSoup(f_sched, 'html.parser')
rows = soup.find_all('tr')


i = 0
j = 0
final_i = 0
for row in rows:
  vals = row.find_all('th')
  # vals2 = row.find_all('td')
  # print(vals, vals2)
  i += 1
  j += 1
  if len(vals) > 0:
    if vals[0]['class'] == ['termFall'] and vals[0].text == 'CENG-Computer Science & Software Engineering':
      final_i = i
    if vals[0].text == 'CENG-Computer Engineering':
      break

rows_subset = rows[final_i:j]

def getContents(row):
  if row.renderContents().decode("utf-8")[0] == "<":
    if row.find("abbr"):
      return row.find("abbr").renderContents().decode("utf-8")
    elif row.find("a"):
      return row.find("a").renderContents().decode("utf-8")
    else:
      return row.find("span").renderContents().decode("utf-8")
  else:
    return row.renderContents().decode("utf-8")
  
vals = rows_subset[0].find_all('th')
headers = []
for i in vals:
  headers.append(getContents(i))
profHeaders = headers[:5]
classHeaders = headers[5:]
prof_df = pd.DataFrame(columns=profHeaders)
class_df = pd.DataFrame(columns=classHeaders)
i = 0
curProf = ""
for row in rows_subset[1:]:
  vals2 = row.find_all('td')
  if len(vals2) > 0:
    profDict = {}
    classDict = {}
    if vals2[0]["class"][0] == "courseName":
      courseOnly = True
    for i in vals2:
      if i["class"][0] == "personName":
        curProf = getContents(i)
        profDict["Name"] = getContents(i)
      elif i["class"][0] == "personAlias":
        profDict["Alias"] = getContents(i)
      elif i["class"][0] == "personTitle":
        profDict["Title"] = getContents(i)
      elif i["class"][0] ==  "personPhone":
        profDict["Phone"] = getContents(i)
      elif i["class"][0] == "personLocation":
        profDict["Office"] = getContents(i)
      if "courseName" in i["class"][0]:
        classDict["Course"] = getContents(i)
        classDict["Name"] = curProf
      elif i["class"][0] == "personOfficeHours":
        classDict["Office Hours"] = getContents(i)
      elif i["class"][0] == "courseName":
        classDict["Course"] = getContents(i)
      elif i["class"][0] == "courseSection":
        classDict["Sect"] = getContents(i)
      elif i["class"][0] == "courseType":
        classDict["Type"] = getContents(i)
      elif i["class"][0] == "courseDays":
        classDict["Days"] = getContents(i)
      elif i["class"][0] == "startTime":
        classDict["Start"] = getContents(i)
      elif i["class"][0] == "endTime":
        classDict["End"] = getContents(i)
      elif i["class"][0] == "location":
        classDict["Location"] = getContents(i)
    if len(profDict) > 1:
      prof_df = prof_df.append(profDict, ignore_index = True)
    if len(classDict) > 1:
      class_df = class_df.append(classDict, ignore_index = True)


class_df = class_df[class_df['Course'] != 'DEV11 E800 <span class="sessionCode" title="October 18, 2021 to December 11, 2021">CEU</span> <span class="instructorCount" title="DEV11-E800-01-2218 has two instructors">/2</span>']
class_df.reset_index(inplace=True)

csv = pd.read_csv("foo.csv", header=None, names=["Course", "CourseName", "Prerequisites", "Credits"])
class_df = class_df.merge(csv, how="left", on="Course")
for i in class_df:
  print(i)
class_df.to_excel(r'./classDf.xlsx', index = False)
prof_df.to_excel(r'./profDf.xlsx', index = False)
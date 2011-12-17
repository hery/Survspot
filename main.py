#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License

import cgi
import os
import datetime
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.api import users
import random
import string

def userPassesScreeningQuestion(thisSurvey, userAnswerToScreeningQuestions):
	i = 0
	while i < len(userAnswerToScreeningQuestions):
		if str(thisSurvey.rightAnswer[i]) != str(userAnswerToScreeningQuestions[i].rstrip()):
			return False
		i += 1
	return True
		
def displayScreeningQuestions(currentSurvey):
	formString = '''
		<table border="1" id="surveyList">
			<tr>
				<th>Questions</th>			
				<th>Answers</th>			
			</tr>'''
	i = 0
	for i in range(len(currentSurvey.questions)):
		if fetchQuestion(currentSurvey.questions[i])[0] == "1":
			answerType = str(fetchAnswer(currentSurvey.answers[i])[0])
			answerInput = ""
			if answerType == "1":
				answerInput += '<input type="textfield" name="answer' + str(i) + '" />'
			elif answerType == "2":
				j=0
				answerList = createSingleAnswerList(fetchAnswer(currentSurvey.answers[i])[1])
				for j in range(len(answerList)):
					answerInput += '<input type="radio" name="answer' + str(i) + '" value="' + answerList[j] + '" />' + answerList[j]
			else:
				answerList = createSingleAnswerList(fetchAnswer(currentSurvey.answers[i])[1])
				for j in range(len(answerList)):
					answerInput += '<input type="checkbox" name="answer' + str(i) + '" value="' + answerList[j] + '" />' + answerList[j]
			if i%2==0:
				formString += '<tr><td>' + fetchQuestion(currentSurvey.questions[i])[1] + '</td><td>' + answerInput + "</td></tr>"
			else:
				formString += '<tr class="alt"><td>' + fetchQuestion(currentSurvey.questions[i])[1] + '</td><td>' + answerInput + "</td></tr>"			
	formString += "</table>"			 
	return formString

def userIsTarget(surv, user):
	surveyInformation = surv.target
	if (surveyInformation[1] != ""):
		if (int(user.age) > int(surveyInformation[1])):
			return False
	else:
		conditionIsSatisfied = True
	#--
	if (surveyInformation[0] != ""):
		if (int(user.age) < int(surveyInformation[0])):
			return False
	else:
		conditionIsSatisfied = True
	#--
	if (surveyInformation[2] != ""):
		if (str(user.gender) != str(surveyInformation[2])):
			return False
	else:
		conditionIsSatisfied = True
	#--
	if (surveyInformation[3] != "" and surveyInformation[4] != ""):
		if (int(user.familySize) > int(surveyInformation[4]) or int(user.familySize) < int(surveyInformation[3])):
			return False
	else:
		conditionIsSatisfied = True
	#--
	if (surveyInformation[5] != "" and surveyInformation[6] != ""):
		if (int(user.numberOfChildren) > int(surveyInformation[6]) or int(user.numberOfChildren) < int(surveyInformation[5])):
			return False
	else:
		conditionIsSatisfied = True
	#--
	if (surveyInformation[7] != ""):
		maritalStatus = []
		myItem = ""
		for someChar in surveyInformation[7]:
			if someChar != ";":
				myItem += someChar
			else:
				maritalStatus.append(myItem)
				myItem = ""
		if (str(user.maritalStatus) in maritalStatus):
			conditionIsSatisfied = True
		else:
			return False
	else:
		conditionIsSatisfied = True
	#--
	if (surveyInformation[9] != "" and surveyInformation[8] != ""):
		if (user.householdIncome > float(surveyInformation[9]) or user.householdIncome < float(surveyInformation[8])):
			return False
	else:
		conditionIsSatisfied = True
	#--	
	if (surveyInformation[10] != ""):
		education = []
		myItem = ""
		for someChar in surveyInformation[10]:
			if someChar != ";":
				myItem += someChar
			else:
				education.append(myItem)
				myItem = ""
		if (str(user.education) in education):
			conditionIsSatisfied = True
		else:
			return False
	else:
		conditionIsSatisfied = True
		#--
	if (surveyInformation[11] != ""):
		ethnicity = []
		myItem = ""
		for someChar in surveyInformation[11]:
			if someChar != ";":
				myItem += someChar
			else:
				ethnicity.append(myItem)
				myItem = ""
		if (str(user.ethnicity) in ethnicity):
			conditionIsSatisfied = True
		else:
			return False
	else:
		conditionIsSatisfied = True
		#--
	if (surveyInformation[12] != ""):
		religion = []
		myItem = ""
		for someChar in surveyInformation[12]:
			if someChar != ";":
				myItem += someChar
			else:
				religion.append(myItem)
				myItem = ""
		if (str(user.religion) in religion):
			conditionIsSatisfied = True
		else:
			return False
	else:
		conditionIsSatisfied = True
	#--
	if surveyInformation[13] != "":
		occupation = []
		myItem = ""
		for someChar in surveyInformation[13]:
			if someChar != ";":
				myItem += someChar
			else:
				occupation.append(myItem)
				myItem = ""
		if (str(user.occupation) in occupation):
			conditionIsSatisfied = True
		else:
			return False
	else:
		conditionIsSatisfied = True
	#--
	return True

def profileIsComplete(thisUser):
	for item in thisUser.targetProfile:
		if item == False:
			return False
	return True
	

def numberOfUsersWhoTookSurvey(surveyId):
	allUsers = db.GqlQuery("SELECT * FROM User")
	i = 0
	for aUser in allUsers:
		for k in aUser.surveysTaken:
			if (k == surveyId):
				i += 1
				break
	return i

def surveyFromCompany(thisSurveys, surv):
	for i in range(len(thisSurveys)):
		if (str(thisSurveys[i]) == str(surv.surveyId)):
			return True
	return False
	
def createLoginUrl(self):
	user = users.get_current_user()
	if user:
		urlLogin = users.create_logout_url(self.request.uri)
		urlLoginText = 'Logout'
	else:
		urlLogin = users.create_login_url(self.request.uri)
		urlLoginText = 'Login'
	login = [urlLogin, urlLoginText, user]
	return login

def addNewUser():
	user = users.get_current_user()
	members = db.GqlQuery("SELECT * FROM User")
	knownUser = False
	for member in members:
		if member.userId == str(user.user_id()):
			knownUser = True
			break
	if knownUser == False:
		newUser = User(name = user.nickname(),
						nick = user.nickname(),
						inscriptionDate = datetime.datetime.now().date(),
						userId = str(user.user_id()),
						email = user.email(),
						nickemail = user.email(),
						company = False,
						credit = 0.0,
						targetProfile = [False, False, False, False, False, False, False, False, False, False]
						)
		newUser.put()

def duplicateQuestionFailed(thisQuestions, answerList, duplicateQuestion, duplicateAnswer):
	for i in range(len(thisQuestions)):
		if str(thisQuestions[i][1:]) == str(duplicateQuestion):
			if str(duplicateAnswer[1:]) == str(answerList[i][1:]):
				return False
			else:
				return True

			
		
def addNewCompany():
	user = users.get_current_user()
	members = db.GqlQuery("SELECT * FROM Company")
	knownCompany = False
	for member in members:
		if member.companyId == str(user.user_id()):
			knownCompany = True
			break
	if knownCompany == False:
		newCompany = Company(name = user.nickname(),
						nick = user.nickname(),
						inscriptionDate = datetime.datetime.now().date(),
						companyId = str(user.user_id()),
						email = user.email(),
						nickemail = user.email(),
						verified = False
						)
		newCompany.put()
		
def getTargetArray(self):
	ageLowerBound = str(self.request.get("ageLowerBound"))
	ageUpperBound = str(self.request.get("ageUpperBound"))
	gender = str(self.request.get("gender"))
	familySizeLowerBound = str(self.request.get("familySizeLowerBound"))
	familySizeUpperBound = str(self.request.get("familySizeUpperBound"))
	numberOfChildrenUpperBound = str(self.request.get("childrenUpperBound"))
	numberOfChildrenLowerBound = str(self.request.get("childrenLowerBound"))
	maritalStatus0 = self.request.get_all("maritalStatus")
	maritalStatus = ""
	for stat in maritalStatus0:
		maritalStatus += stat + ";"
	householdIncomeLowerBound = str(self.request.get("householdIncomeLowerBound"))
	householdIncomeUpperBound = str(self.request.get("householdIncomeUpperBound"))
	education0 = self.request.get_all("education")
	education = ""
	for educ in education0:
		education += educ + ";"
	ethnicity0 = self.request.get_all("ethnicity")
	ethnicity = ""
	for eth in ethnicity0:
		ethnicity += eth + ";"
	religion0 = self.request.get_all("religion")
	religion = ""
	for rel in religion0:
		religion += rel + ";"
	occupation0 = self.request.get_all("occupation")
	occupation = ""
	for occ in occupation0:
		occupation += occ + ";"
	targetArray = [ageLowerBound, ageUpperBound, gender, familySizeLowerBound, familySizeUpperBound, numberOfChildrenLowerBound, numberOfChildrenUpperBound, maritalStatus, householdIncomeLowerBound, householdIncomeUpperBound, education, ethnicity, religion, occupation]
	return targetArray
	
def pickSurvey(thisSurveyId):
	allSurveys = db.GqlQuery("SELECT * FROM Survey")
	for anySurvey in allSurveys:
		if int(thisSurveyId) == anySurvey.surveyId:
			mySurvey = anySurvey
			break
	return mySurvey	

def pickUser(thisUserId):
	allUsers = db.GqlQuery("SELECT * FROM User")
	for anyUser in allUsers:
		if str(thisUserId) == anyUser.userId:
			thisUser = anyUser
			return thisUser
	
def pickCompany(thisCompanyId):
	allCompany = db.GqlQuery("SELECT * FROM Company")
	for anyCompany in allCompany:
		if str(thisCompanyId) == anyCompany.companyId:
			myCompany = anyCompany
			break
	return myCompany
	
def encodeSurveyAnswer(surveyId, answerList):
	encodedAnswer = ""
	encodedAnswer += str(surveyId) + ":"
	answerString = ""
	for i in range(len(answerList)):
		answerString += str(answerList[i]) + ";"
	encodedAnswer += answerString
	return encodedAnswer #str
	
def decodeSurveyAnswer(answerString):
	decodedAnswer = []
	indexOfSeparation = answerString.find(":")
	decodedAnswer = [answerString[0:indexOfSeparation],answerString[indexOfSeparation:]]
	return decodedAnswer #[surveyId,answerString] where answerString is a1; a2...
	
def surveyWillDuplicate(someSurveyId, encodedUserAnswers): #encodedUserAnswers: ["id1:a1;a2;a3","id2:b1,b2"]
	 													   #decodedAnswer: [id, "a1;a2;a3"]
	duplicate = False
	i = 0
	for i in range(len(encodedUserAnswers)):
		decodedAnswer = decodeSurveyAnswer(encodedUserAnswers[i])
		if decodedAnswer[0] == someSurveyId:
			duplicate = True
	return duplicate	

class News(db.Model):
	content = db.StringProperty(required=True)
	date = db.DateProperty()
	author = db.StringProperty()
	
class Company(db.Model):
	name = db.StringProperty(required=True)
	nick = db.StringProperty(required=True)	
	email = db.EmailProperty(required=True)
	nickemail = db.EmailProperty(required=True)
	surveys = db.ListProperty(int)
	inscriptionDate = db.DateProperty()
	verified = db.BooleanProperty()
	companyId = db.StringProperty()

class User(db.Model):
	name = db.StringProperty(required=True)
	nick = db.StringProperty(required=True)	
	email = db.EmailProperty(required=True)
	userId = db.StringProperty()
	nickemail = db.EmailProperty(required=True)
	inscriptionDate = db.DateProperty()
	company = db.BooleanProperty()
	admin = db.BooleanProperty()
	profil = db.ListProperty(str)
	surveysTaken = db.ListProperty(int)
	credit = db.FloatProperty()
	targetProfile = db.ListProperty(bool)
	answerToSurveys = db.ListProperty(str)
	TOS = db.BooleanProperty()
	profileComplete = db.BooleanProperty()
	#--
	age = db.IntegerProperty()
	gender = db.StringProperty()
	familySize = db.IntegerProperty()
	numberOfChildren = db.IntegerProperty()
	maritalStatus = db.StringProperty()
	householdIncome = db.FloatProperty()
	education = db.StringProperty()
	ethnicity = db.StringProperty()
	religion = db.StringProperty()
	occupation = db.StringProperty()
	#--
	
class Target(db.Model):
	age = db.ListProperty(str)
	gender = db.ListProperty(str)
	familySize = db.ListProperty(str)
	numberOfChildren = db.ListProperty(str)
	maritalStatus = db.ListProperty(str)
	householdIncome = db.ListProperty(str)
	education = db.ListProperty(str)
	ethnicity = db.ListProperty(str)
	religion = db.ListProperty(str)
	occupation = db.ListProperty(str)

class Survey(db.Model):
	title = db.StringProperty(required=True)
	surveyId = db.IntegerProperty(required=True)
	creationDate = db.DateProperty()
	company = db.StringProperty(required=True)
	questions = db.ListProperty(str, required=True) # Step 2
	answers = db.ListProperty(str, required=True) # Step 2
	rightAnswer = db.ListProperty(str) # Step 2
	limit = db.StringProperty(required=True)
	incentive = db.StringProperty(required=True)
	target = db.ListProperty(str)
	takers = db.ListProperty(str) #identify users who take surveys by their userId property
	UserAnswers = db.ListProperty(str) #identify user answers by their index in the array; separate answers by :::
	totalPrice = db.FloatProperty()
	surveyIsComplete = db.BooleanProperty()
	code = db.StringProperty()
	screeningIndexes = db.ListProperty(int)
	
def fetchQuestion(encodedQuestion): #question is a string
	questionType = encodedQuestion[0]
	question = encodedQuestion[1:]
	thisQuestion = [questionType, question]
	return thisQuestion #thisQuestion is a list of strings
	
def fetchAnswer(encodedAnswer): #answer is a string
	AnswerType = encodedAnswer[0]
	answer = encodedAnswer[1:]
	thisAnswer = [AnswerType, answer]
	return thisAnswer #thisAnswer is a list of strings
	
def createSingleAnswerList(answerString): #from "a1; a2" to ["a1","a2"]
	i = 0
	singleAL = []
	myAnswer = ""
	while (i < len(answerString)):
		if answerString[i]!="\n" and i != len(answerString):
			myAnswer += answerString[i]
			i += 1
			if (i == len(answerString)):
				singleAL.append(myAnswer)
		else:
			i += 1
			singleAL.append(myAnswer)
			myAnswer = ""
	return singleAL
	
def createAnswerOutput(singleAL): #from ["a1","a2"] to "1.a1. 2.a2..."
	outputString = ""
	i=0
	for i in range(len(singleAL)):
		outputString += str(i+1) + ". " + singleAL[i] + ". "
	return outputString	
	
def createTargetString(targetIndexes):
	targetString = ""
	targetString += "<br />Age: from " + targetIndexes[0] + " to " + targetIndexes[1] + " years old.<br />"
	targetString += "Gender: " + targetIndexes[2] + "<br />"
	targetString += "Family size: from " + targetIndexes[3] + " to " + targetIndexes[4] + "<br />"
	targetString += "Number of children: from " + targetIndexes[5] + " to " + targetIndexes[6] + "<br />"
	targetString += "Marital status: "
	targetString += targetIndexes[7]
	targetString += "<br />Household Income: from " + targetIndexes[8] + " to " + targetIndexes[9] + "<br />"
	targetString += "Education: "
	targetString += targetIndexes[10]
	targetString += "<br />Ethnicity: "
	targetString += targetIndexes[11]
	targetString += "<br />Religion: "
	targetString += targetIndexes[12]
	targetString += "<br />Occupation: "
	targetString += targetIndexes[13]
	return targetString

	
def generateSurveyForm(currentSurvey):
	formString = '''
		<table border="1" id="surveyList">
			<tr>
				<th>Questions</th>			
				<th>Answers</th>			
			</tr>'''
	i=0
	#duplicate a random question to prevent random answering
	questionKey = int(random.random()*len(currentSurvey.questions))
	currentSurvey.questions.append(currentSurvey.questions[questionKey])
	currentSurvey.answers.append(currentSurvey.answers[questionKey])
	formString += '<input type=hidden name="duplicateQuestion" value="' + currentSurvey.questions[questionKey][1:] + '">'
	for i in range(len(currentSurvey.questions)):
		if fetchQuestion(currentSurvey.questions[i])[0] == "0":
			answerType = str(fetchAnswer(currentSurvey.answers[i])[0])
			answerInput = ""
			if answerType == "1":
				answerInput += '<input type="textfield" name="answer' + str(i) + '" />'
			elif answerType == "2":
				j=0
				answerList = createSingleAnswerList(fetchAnswer(currentSurvey.answers[i])[1])
				for j in range(len(answerList)):
					answerInput += '<input type="radio" name="answer' + str(i) + '" value="' + answerList[j] + '" />' + answerList[j]
			else:
				answerList = createSingleAnswerList(fetchAnswer(currentSurvey.answers[i])[1])
				for j in range(len(answerList)):
					answerInput += '<input type="checkbox" name="answer' + str(i) + '" value="' + answerList[j] + '" />' + answerList[j]
			if i%2==0:
				formString += '<tr><td>' + fetchQuestion(currentSurvey.questions[i])[1] + '</td><td>' + answerInput + "</td></tr>"
			else:
				formString += '<tr class="alt"><td>' + fetchQuestion(currentSurvey.questions[i])[1] + '</td><td>' + answerInput + "</td></tr>"			
	formString += "</table>"			 
	return formString
	
def createAnswerString(singleAL, answerType): #parameter is a list: ["a1,a2,a3" ]
	answerString = ""
	for i in range(len(singleAL)):
		if int(answerType)==1:
			answerString += '<input type="textfield" name="answer" value="' + singleAL[i] + '">'
			break
		else:
			answerString += "prout"
			continue
		return answerString

#class myHandler(webapp.RequestHandler):
#	def get(self):
#		path = os.path.join(os.path.dirname(__file__),'index.html')
#		self.response.out.write(template.render(path, path)) */ 
		
class myHandler(webapp.RequestHandler):
	def get(self):
		user = users.get_current_user()
		if user:
			addNewUser()
			pageTitle = "Home"
			currentUserFromDb = pickUser(str(user.user_id()))
			credit = currentUserFromDb.credit
			allSurveys = db.GqlQuery("SELECT * FROM Survey")
			surveyForm = '''
			<br><table border="1" id="surveyList"><tr><td>Available Surveys</td></tr></table>
			<table border="1" id="surveyList">
				<tr>
					<form method="post" action="userSurveyList">
						<th>
							<input type="submit" name="surveySent" value="Title">
						</th>
						<th>
							<input type="submit" name="surveySent" value="Company">
						</th>
						<th>
							<input type="submit" name="surveySent" value="Reward">
						</th>
						<th>
							Estimated Time (mn)
						</th>
						<th>
							Already Taken?
						</th>
						<th>
							Go!
						</th>
					</form>
				</tr>'''
			i=0
			for surv in allSurveys:
			### TARGET FILTER HERE ###
				if userIsTarget(surv, currentUserFromDb):
					if i%2==0:
						surveyForm += '<tr><td>'
					else:
						surveyForm += '<tr class="alt"><td>'
					surveyForm += surv.title
					surveyForm += '</td><td>'
					surveyForm += surv.company
					surveyForm += '</td><td>$'
					surveyForm += str(len(surv.questions)*float(surv.incentive)*0.5)
					surveyForm += '</td><td>'
					surveyForm += str(len(surv.questions))
					surveyForm += 'mn</td><td>'
					if surveyWillDuplicate(str(surv.surveyId), currentUserFromDb.answerToSurveys):
						surveyForm += "Yes"
					else:
						surveyForm += "No"
					surveyForm += '</td><td>'
					surveyForm += '<input type="submit" name="surveySent" value="'
					surveyForm += str(surv.surveyId)
					surveyForm += '"></td></tr>'
					i+=1
			surveyForm += '</table>'

			news = db.GqlQuery("SELECT * FROM News")
			ONews = '<table border="1" id="surveyList"><tr><th>News</th></tr>'
			for piece in news:
				ONews += "<tr><td>" + piece.content + "</td></tr>"
			ONews += "</table>"
			alert = []	
			if (profileIsComplete(currentUserFromDb) == False):
				alert.append('You must <a href="userGeneralInformation">complete your profile</a>.')
			if (currentUserFromDb.TOS != True):
				alert.append('You need to accept the <a href="userCat">Terms and Conditions</a>')
			if ((len(alert)) == 0):
				alert.append('There is no alert at the moment.')
			OAlert = '<table border="1" id="surveyList"><tr><th>Alerts</th></tr>'
			for i in range(len(alert)):
				OAlert += "<tr><td>" + alert[i] + "</td></tr>"
			OAlert += "</table>"
			tValues = {'credit': credit,'urlLogin': createLoginUrl(self)[0],'urlLoginText': createLoginUrl(self)[1],
				'user': createLoginUrl(self)[2], 'pageTitle': pageTitle, 'surveyForm': surveyForm, 'alert':OAlert, 'news':ONews}
			path = os.path.join(os.path.dirname(__file__),'index_user.html')
			self.response.out.write(template.render(path, tValues))
		else:
			message = "please login."
			tValues = {'message':message,'urlLogin': createLoginUrl(self)[0],'urlLoginText': createLoginUrl(self)[1]}
			path = os.path.join(os.path.dirname(__file__),'index_user.html')
			self.response.out.write(template.render(path, tValues))



class indexCompany(webapp.RequestHandler):
	def get(self):
		user = users.get_current_user()
		if user:
			addNewCompany()
			thisCompany = pickCompany(user.user_id())
	#		if thisCompany.verified:
			pageTitle = "Home"
			tValues = {'urlLogin': createLoginUrl(self)[0],'urlLoginText': createLoginUrl(self)[1],
				'user': createLoginUrl(self)[2], 'pageTitle': pageTitle}
			path = os.path.join(os.path.dirname(__file__),'index_company.html')
			self.response.out.write(template.render(path, tValues))
	#		else:
	#			pageTitle = "Unverified Account"
	#			tValues = {'urlLogin': createLoginUrl(self)[0],'urlLoginText': createLoginUrl(self)[1],
	#				'user': createLoginUrl(self)[2], 'pageTitle': pageTitle}
	#			path = os.path.join(os.path.dirname(__file__),'company_unverified.html')
	#			self.response.out.write(template.render(path, tValues))
		else:
			pageTitle = "Login"
			tValues = {'urlLogin': createLoginUrl(self)[0],'urlLoginText': createLoginUrl(self)[1],
				'user': createLoginUrl(self)[2], 'pageTitle': pageTitle}
			path = os.path.join(os.path.dirname(__file__),'index_company.html')
			self.response.out.write(template.render(path, tValues))
							
class userSurveyList(webapp.RequestHandler):
	def get(self):
		pageTitle = "Surveys"
		user = users.get_current_user()
		currentUserFromDb = pickUser(str(user.user_id()))
		allSurveys = db.GqlQuery("SELECT * FROM Survey")
		surveyForm = '''
		<table border="1" id="surveyList">
			<tr>
				<form method="post" action="userSurveyList">
					<th>
						<input type="submit" name="surveySent" value="Title">
					</th>
					<th>
						<input type="submit" name="surveySent" value="Company">
					</th>
					<th>
						<input type="submit" name="surveySent" value="Reward">
					</th>
					<th>
						Estimated Time (mn)
					</th>
					<th>
						Already Taken?
					</th>
					<th>
						Go!
					</th>
				</form>
			</tr>'''
		i=0
		for surv in allSurveys:
			if i%2==0:
				surveyForm += '<tr><td>'
			else:
				surveyForm += '<tr class="alt"><td>'
			surveyForm += surv.title
			surveyForm += '</td><td>'
			surveyForm += surv.company
			surveyForm += '</td><td>$'
			surveyForm += str(len(surv.questions)*float(surv.incentive)*0.5)
			surveyForm += '</td><td>'
			surveyForm += str(len(surv.questions))
			surveyForm += 'mn</td><td>'
			if surveyWillDuplicate(str(surv.surveyId), currentUserFromDb.answerToSurveys):
				surveyForm += "Yes"
			else:
				surveyForm += "No"
			surveyForm += '</td><td>'
			surveyForm += '<input type="submit" name="surveySent" value="'
			surveyForm += str(surv.surveyId)
			surveyForm += '"></td></tr>'
			i+=1
		surveyForm += '</table>'
		#--
		tValues = {'urlLogin': createLoginUrl(self)[0],'urlLoginText': createLoginUrl(self)[1],
			'user': createLoginUrl(self)[2], 'pageTitle': pageTitle, 'surveyForm': surveyForm}
		path = os.path.join(os.path.dirname(__file__),'user_survey_list.html')
		self.response.out.write(template.render(path, tValues))
		

									
class userAccount(webapp.RequestHandler):
	def get(self):
		pageTitle = "Account Information"
		tValues = {'urlLogin': createLoginUrl(self)[0],'urlLoginText': createLoginUrl(self)[1],
			'user': createLoginUrl(self)[2], 'pageTitle': pageTitle}
		path = os.path.join(os.path.dirname(__file__),'user_account.html')
		self.response.out.write(template.render(path, tValues))
		
class companyAccount(webapp.RequestHandler):
	def get(self):
		pageTitle = "Account Information"
		user = users.get_current_user()
		thisCompany = pickCompany(user.user_id())
		companyName = thisCompany.name
		tValues = {'urlLogin': createLoginUrl(self)[0],'urlLoginText': createLoginUrl(self)[1],
			'user': createLoginUrl(self)[2], 'pageTitle': pageTitle, 'companyName':companyName}
		path = os.path.join(os.path.dirname(__file__),'company_account.html')
		self.response.out.write(template.render(path, tValues))

class companyCreateSurvey(webapp.RequestHandler):
	def get(self):
		pageTitle = "Create a New Survey"
		tValues = {'urlLogin': createLoginUrl(self)[0],'urlLoginText': createLoginUrl(self)[1],
			'user': createLoginUrl(self)[2], 'pageTitle': pageTitle}
		path = os.path.join(os.path.dirname(__file__),'company_create_survey.html')
		self.response.out.write(template.render(path, tValues))

class userCredit(webapp.RequestHandler):
	def get(self):
		pageTitle = "Credit"
		tValues = {'urlLogin': createLoginUrl(self)[0],'urlLoginText': createLoginUrl(self)[1],
			'user': createLoginUrl(self)[2], 'pageTitle': pageTitle}
		path = os.path.join(os.path.dirname(__file__),'user_credit.html')
		self.response.out.write(template.render(path, tValues))

class userWithdrawal(webapp.RequestHandler):
	def get(self):
		pageTitle = "Withdrawal"
		tValues = {'urlLogin': createLoginUrl(self)[0],'urlLoginText': createLoginUrl(self)[1],
			'user': createLoginUrl(self)[2], 'pageTitle': pageTitle}
		path = os.path.join(os.path.dirname(__file__),'user_withdrawal.html')
		self.response.out.write(template.render(path, tValues))
		
class userReferral(webapp.RequestHandler):
	def get(self):
		pageTitle = "Referral"
		tValues = {'urlLogin': createLoginUrl(self)[0],'urlLoginText': createLoginUrl(self)[1],
			'user': createLoginUrl(self)[2], 'pageTitle': pageTitle}
		path = os.path.join(os.path.dirname(__file__),'user_referral.html')
		self.response.out.write(template.render(path, tValues))
		
class userCat(webapp.RequestHandler):
	def get(self):
		user = users.get_current_user()
		pageTitle = "Condition and Terms"
		currentUser = pickUser(user.user_id())
		if (currentUser.TOS):
			status = "You've read and accepted the Term and Conditions."
		else:
			status = '''By clicking on "Accept", I agree that I have read and accept the Terms and Conditions above.
			<input type="submit" name="TOS" value="Accept">'''
		tValues = {'urlLogin': createLoginUrl(self)[0],'urlLoginText': createLoginUrl(self)[1],
			'user': createLoginUrl(self)[2], 'pageTitle': pageTitle, 'status':status}
		if user:
			path = os.path.join(os.path.dirname(__file__),'user_cat_logged.html')
			self.response.out.write(template.render(path, tValues))
		else:
			path = os.path.join(os.path.dirname(__file__),'user_cat.html')
			self.response.out.write(template.render(path, tValues))
				
class companyCat(webapp.RequestHandler):
	def get(self):
		pageTitle = "Condition and Terms"
		tValues = {'urlLogin': createLoginUrl(self)[0],'urlLoginText': createLoginUrl(self)[1],
			'user': createLoginUrl(self)[2], 'pageTitle': pageTitle}
		user = users.get_current_user()
		if user:
			path = os.path.join(os.path.dirname(__file__),'company_cat_logged.html')
			self.response.out.write(template.render(path, tValues))
		else:
			path = os.path.join(os.path.dirname(__file__),'company_cat.html')
			self.response.out.write(template.render(path, tValues))
			
class userGeneralInformation(webapp.RequestHandler):
	def get(self):
		pageTitle = "General Information"
		thisUser = users.get_current_user()
		thisUser = pickUser(thisUser.user_id())
		
		age = thisUser.age
		gender = thisUser.gender
		familySize = thisUser.familySize
		numberOfChildren = thisUser.numberOfChildren
		maritalStatus = thisUser.maritalStatus
		householdIncome = thisUser.householdIncome
		education = thisUser.education
		ethnicity = thisUser.ethnicity
		religion = thisUser.religion
		occupation = thisUser.occupation
		
		tValues = {'urlLogin': createLoginUrl(self)[0],'urlLoginText': createLoginUrl(self)[1],
			'user': createLoginUrl(self)[2], 'pageTitle': pageTitle, 'age':age, 'gender':gender, 'familySize':familySize, 'numberOfChildren':numberOfChildren, 'maritalStatus':maritalStatus, 'householdIncome':householdIncome,'education':education,'ethnicity':ethnicity,'religion':religion,'occupation':occupation}
		path = os.path.join(os.path.dirname(__file__),'user_general_information.html')
		self.response.out.write(template.render(path, tValues))


class mobileRequest(webapp.RequestHandler):
	def get(self):
		myName = self.request.get("myName");
		myStatus = self.request.get("myStatus");
		tValues = {'myName': myName, 'myStatus': myStatus}
#		tValues = {}
		path = os.path.join(os.path.dirname(__file__),'mobile_request.html')
		self.response.out.write(template.render(path, tValues))
		
class companyStepOne(webapp.RequestHandler): #set title and create survey
	def post(self):
		user = users.get_current_user()
		pageTitle = "Create a New Survey"
		thisSurveyTitle = self.request.get("title")		### try this ###
		thisSurveyCompany = user.nickname()
		thisCompany = pickCompany(user.user_id())
		allSurveys = db.GqlQuery("SELECT * FROM Survey")
		counter = 0
		for surv in allSurveys:
			counter += 1
		thisSurveyId = counter
		thisSurvey = Survey(title = thisSurveyTitle, company = thisSurveyCompany, 
							surveyId = thisSurveyId, creationDate = datetime.datetime.now().date(),
							questions = [], answers = [], limit = "0", incentive = "0", surveyIsComplete = False)
		thisCompany.surveys.append(thisSurveyId)
		thisCompany.put()
		thisSurvey.put()
		tValues = {'urlLogin': createLoginUrl(self)[0],'urlLoginText': createLoginUrl(self)[1],
			'user': createLoginUrl(self)[2], 'pageTitle': pageTitle, 'thisSurveyTitle': thisSurveyTitle, 'thisSurveyId': thisSurveyId}
		path = os.path.join(os.path.dirname(__file__),'company_step1.html')
		self.response.out.write(template.render(path, tValues))
		
class companyStepTwo(webapp.RequestHandler): #set targets
	def post(self):
		pageTitle = "Create a New Survey"
		State = self.request.get("stepTwoPost")
		if State=="Next":
			thisSurveyId = self.request.get("thisSurveyId")
			thisSurvey = pickSurvey(thisSurveyId)
			targetArray=getTargetArray(self) #store target results into the target array
			thisSurvey.target = targetArray
			thisSurvey.put()
			tValues = {'urlLogin': createLoginUrl(self)[0],'urlLoginText': createLoginUrl(self)[1],
				'user': createLoginUrl(self)[2], 'pageTitle': pageTitle, 'thisSurveyId': thisSurveyId}
			path = os.path.join(os.path.dirname(__file__),'company_step2.html')
			self.response.out.write(template.render(path, tValues))
		else:
			tValues = {'urlLogin': createLoginUrl(self)[0],'urlLoginText': createLoginUrl(self)[1],
				'user': createLoginUrl(self)[2], 'pageTitle': pageTitle, 
				'thisSurveyId': thisSurveyId}
			path = os.path.join(os.path.dirname(__file__),'index_user.html')
			self.response.out.write(template.render(path, tValues))
			
class companyStepThree(webapp.RequestHandler): #post QA
	def post(self):
		pageTitle = "Create a New Survey"
		State = self.request.get("stepThreePost")
		if State=="Next":
			thisSurveyId = self.request.get("thisSurveyId")
			tValues = {'urlLogin': createLoginUrl(self)[0],'urlLoginText': createLoginUrl(self)[1],
				'user': createLoginUrl(self)[2], 'pageTitle': pageTitle, 'thisSurveyId': thisSurveyId}
			path = os.path.join(os.path.dirname(__file__),'company_step3.html')
			self.response.out.write(template.render(path, tValues))
		elif State=="Add Question":
			#identify and select current survey
			thisSurveyId = self.request.get("thisSurveyId")
			thisSurvey = pickSurvey(thisSurveyId)
			#select question and encode it with its type
			thisQuestion = self.request.get("question")
			thisQuestionType = self.request.get("questionType")
			thisEncodedQuestion = thisQuestionType + thisQuestion
			#select answer and encode it with its type
			thisAnswer = self.request.get("answer") 				#input is a string: "a1; a2; a3"
			thisAnswerType = self.request.get("answerType")
			thisEncodedAnswer = thisAnswerType + thisAnswer
			#select right answer
			thisRightAnswer = self.request.get("rightAnswer")
			#update survey properties
			thisSurvey.questions.append(thisEncodedQuestion)
			thisSurvey.answers.append(thisEncodedAnswer) 		#thisSurvey.answer = ["a1;a2","b1;b2"]
			thisSurvey.rightAnswer.append(thisRightAnswer)
			user = users.get_current_user()
#			thisUser = pickUser(user.user_id())
#			thisUser.surveysTaken.append(int(thisSurveyId))
#			thisUser.put()
			thisSurvey.put()
			tValues = {'urlLogin': createLoginUrl(self)[0],'urlLoginText': createLoginUrl(self)[1],
				'user': createLoginUrl(self)[2], 'pageTitle': pageTitle, 'thisSurveyId': thisSurveyId}
			path = os.path.join(os.path.dirname(__file__),'company_step2.html')
			self.response.out.write(template.render(path, tValues))
		else:
			tValues = {'urlLogin': createLoginUrl(self)[0],'urlLoginText': createLoginUrl(self)[1],
				'user': createLoginUrl(self)[2], 'pageTitle': pageTitle, 
				'thisSurveyId': thisSurveyId}
			path = os.path.join(os.path.dirname(__file__),'company_step1.html')
			self.response.out.write(template.render(path, tValues))
		
class companyStepFour(webapp.RequestHandler): #post limit+incentive
	def post(self):
		pageTitle = "Create a New Survey"
		State = self.request.get("stepFourPost")
		if State=="Next":
			#update limit and incentive
			thisLimit = self.request.get("limit")
			thisIncentive = self.request.get("incentive")
			thisSurveyId = self.request.get("thisSurveyId")
			currentSurvey = pickSurvey(thisSurveyId) 
			if (thisLimit==""):
				thisLimit = "No Limit"
			currentSurvey.limit = thisLimit #survey limit
			if (thisIncentive==""):
				thisIncentive="0"
			currentSurvey.incentive = thisIncentive #survey incentive
			#currentSurvey.put()	#Later
			#Create target string
			targetIndexes = currentSurvey.target #get target array of indexes
			targetString = createTargetString(targetIndexes)
			#need to display a table with QA to send to next step
			i = 0; j = 0; screeningIndexes = []
			myForm = '<table border="1"><tr><th>Screening Question</th><th>Question</th><th>Answer Type</th><th>Answer</th><th>If Screening Question, Right Answer is</th></tr>'
			for i in range(len(currentSurvey.questions)):
				thisQuestion = fetchQuestion(currentSurvey.questions[i])[1]
				thisQuestionType = fetchQuestion(currentSurvey.questions[i])[0]
				if thisQuestionType == "1":
					screeningIndexes.append(j)
				j += 1
				thisAnswer = fetchAnswer(currentSurvey.answers[i])[1] #string: "a1;a2"
				singleAnswerList = createSingleAnswerList(thisAnswer) #thisAnswer ^
				thisAnswer = createAnswerOutput(singleAnswerList)
				thisAnswerType = fetchAnswer(currentSurvey.answers[i])[0]
				thisRightAnswer = currentSurvey.rightAnswer[i]
				if (int(thisQuestionType)==0):
					thisQuestionType = "No"
				else:
					thisQuestionType = "Yes"
				if (int(thisAnswerType)==1):
					thisAnswerType = "Text Field"
				elif (int(thisAnswerType)==2):
					thisAnswerType = "Radio Boxes"
				elif (int(thisAnswerType)==3):
					thisAnswerType = "Check Boxes"
				else:
					thisAnswerType = "Pictures"
				myForm += '<tr><td>'
				myForm += thisQuestionType
				myForm += '</td><td>'
				myForm += thisQuestion
				myForm += '</td><td>'
				myForm += thisAnswerType
				myForm += '</td><td>'
				myForm += thisAnswer
				myForm += '</td><td>'
				myForm += thisRightAnswer
				myForm += '</td></tr>'
			currentSurvey.screeningIndexes = screeningIndexes
			currentSurvey.put()
			myForm += '</table>'
			#---
			tValues = {'urlLogin': createLoginUrl(self)[0],'urlLoginText': createLoginUrl(self)[1],
				'user': createLoginUrl(self)[2], 'pageTitle': pageTitle, 
				'thisSurveyId': thisSurveyId, 'thisSurveyLimit':thisLimit,'thisSurveyIncentive': thisIncentive, 'thisSurveyTarget': targetString, 'myForm': myForm}
			path = os.path.join(os.path.dirname(__file__),'company_step4.html')
			self.response.out.write(template.render(path, tValues))
		else:
			tValues = {'urlLogin': createLoginUrl(self)[0],'urlLoginText': createLoginUrl(self)[1],
				'user': createLoginUrl(self)[2], 'pageTitle': pageTitle, 
				'thisSurveyId': thisSurveyId}
			path = os.path.join(os.path.dirname(__file__),'company_step2.html')
			self.response.out.write(template.render(path, tValues))
			
class companyStepFive(webapp.RequestHandler): #preview
	def post(self):
		pageTitle = "Create a New Survey"
		thisSurveyId = self.request.get("thisSurveyId")
		currentSurvey = pickSurvey(thisSurveyId)
		numberOfQuestions = len(currentSurvey.questions)
		price = currentSurvey.incentive
		total = numberOfQuestions*float(price)
		currentSurvey.price = total
		currentSurvey.put()
		State = self.request.get("stepFivePost")
		if State=="Next":
			tValues = {'urlLogin': createLoginUrl(self)[0],'urlLoginText': createLoginUrl(self)[1],
				'user': createLoginUrl(self)[2], 'pageTitle': pageTitle, 'numberOfQuestions': numberOfQuestions, 'incentive':price, 'addFees':"0",'total':total}
			path = os.path.join(os.path.dirname(__file__),'company_step5.html')
			self.response.out.write(template.render(path, tValues))
		else:
			tValues = {'urlLogin': createLoginUrl(self)[0],'urlLoginText': createLoginUrl(self)[1],
				'user': createLoginUrl(self)[2], 'pageTitle': pageTitle}
			path = os.path.join(os.path.dirname(__file__),'company_step3.html')
			self.response.out.write(template.render(path, tValues))
			
class companySurveyComplete(webapp.RequestHandler):
	def post(self):
		pageTitle = "Create a New Survey"
		State = self.request.get("postComplete")
		if State=="Pay and Upload Survey":
			tValues = {'urlLogin': createLoginUrl(self)[0],'urlLoginText': createLoginUrl(self)[1],
				'user': createLoginUrl(self)[2], 'pageTitle': pageTitle}
			path = os.path.join(os.path.dirname(__file__),'company_survey_sent.html')
			self.response.out.write(template.render(path, tValues))
		else:
			tValues = {'urlLogin': createLoginUrl(self)[0],'urlLoginText': createLoginUrl(self)[1],
				'user': createLoginUrl(self)[2], 'pageTitle': pageTitle}
			path = os.path.join(os.path.dirname(__file__),'company_step4.html')
			self.response.out.write(template.render(path, tValues))
			
class userChooseSurvey(webapp.RequestHandler):
	def post(self):
		pageTitle = "Take a Survey"
		State = self.request.get("surveySent")
		if State=="Submit":
			tValues = {'urlLogin': createLoginUrl(self)[0],'urlLoginText': createLoginUrl(self)[1],
				'user': createLoginUrl(self)[2], 'pageTitle': pageTitle}
			path = os.path.join(os.path.dirname(__file__),'user_take_survey.html')
			self.response.out.write(template.render(path, tValues))
		elif State=="Title":
			pageTitle = "Surveys"
			user = users.get_current_user()
			currentUserFromDb = pickUser(str(user.user_id()))
			title = ""
			allSurveys = db.GqlQuery("SELECT * FROM Survey ORDER BY title")
			surveyForm = '''
			<table border="1" id="surveyList">
				<tr>
					<form method="post" action="userSurveyList">
						<th>
							<input type="submit" name="surveySent" value="Title">
						</th>
						<th>
							<input type="submit" name="surveySent" value="Company">
						</th>
						<th>
							<input type="submit" name="surveySent" value="Reward">
						</th>
						<th>
							Estimated Time (mn)
						</th>
						<th>
							Already Taken?
						</th>
						<th>
							Go!
						</th>
					</form>
				</tr>'''
			i=0
			for surv in allSurveys:
				if i%2==0:
					surveyForm += '<tr><td>'
				else:
					surveyForm += '<tr class="alt"><td>'
				surveyForm += surv.title
				surveyForm += '</td><td>'
				surveyForm += surv.company
				surveyForm += '</td><td>$'
				surveyForm += str(len(surv.questions)*float(surv.incentive)*0.5)
				surveyForm += '</td><td>'
				surveyForm += str(len(surv.questions))
				surveyForm += 'mn</td><td>'
				if surveyWillDuplicate(str(surv.surveyId), currentUserFromDb.answerToSurveys):
					surveyForm += "Yes"
				else:
					surveyForm += "No"
				surveyForm += '</td><td>'
				surveyForm += '<input type="submit" name="surveySent" value="'
				surveyForm += str(surv.surveyId)
				surveyForm += '"></td></tr>'
				i+=1
			surveyForm += '</table>'
			#--
			tValues = {'urlLogin': createLoginUrl(self)[0],'urlLoginText': createLoginUrl(self)[1],
				'user': createLoginUrl(self)[2], 'pageTitle': pageTitle, 'surveyForm': surveyForm}
			path = os.path.join(os.path.dirname(__file__),'user_survey_list.html')
			self.response.out.write(template.render(path, tValues))
		elif State=="Company":
			pageTitle = "Surveys"
			user = users.get_current_user()
			currentUserFromDb = pickUser(str(user.user_id()))
			company = ""
			allSurveys = db.GqlQuery("SELECT * FROM Survey ORDER BY company")
			surveyForm = '''
			<table border="1" id="surveyList">
				<tr>
					<form method="post" action="userSurveyList">
						<th>
							<input type="submit" name="surveySent" value="Title">
						</th>
						<th>
							<input type="submit" name="surveySent" value="Company">
						</th>
						<th>
							<input type="submit" name="surveySent" value="Reward">
						</th>
						<th>
							Estimated Time (mn)
						</th>
						<th>
							Already Taken?
						</th>
						<th>
							Go!
						</th>
					</form>
				</tr>'''
			i=0
			for surv in allSurveys:
				if i%2==0:
					surveyForm += '<tr><td>'
				else:
					surveyForm += '<tr class="alt"><td>'
				surveyForm += surv.title
				surveyForm += '</td><td>'
				surveyForm += surv.company
				surveyForm += '</td><td>$'
				surveyForm += str(len(surv.questions)*float(surv.incentive)*0.5)
				surveyForm += '</td><td>'
				surveyForm += str(len(surv.questions))
				surveyForm += 'mn</td><td>'
				if surveyWillDuplicate(str(surv.surveyId), currentUserFromDb.answerToSurveys):
					surveyForm += "Yes"
				else:
					surveyForm += "No"
				surveyForm += '</td><td>'
				surveyForm += '<input type="submit" name="surveySent" value="'
				surveyForm += str(surv.surveyId)
				surveyForm += '"></td></tr>'
				i+=1
			surveyForm += '</table>'
			#--
			tValues = {'urlLogin': createLoginUrl(self)[0],'urlLoginText': createLoginUrl(self)[1],
				'user': createLoginUrl(self)[2], 'pageTitle': pageTitle, 'surveyForm': surveyForm}
			path = os.path.join(os.path.dirname(__file__),'user_survey_list.html')
			self.response.out.write(template.render(path, tValues))	
		elif State=="Reward":
			pageTitle = "Surveys"
			user = users.get_current_user()
			currentUserFromDb = pickUser(str(user.user_id()))
			incentive = ""
			allSurveys = db.GqlQuery("SELECT * FROM Survey ORDER BY incentive")
			surveyForm = '''
			<table border="1" id="surveyList">
				<tr>
					<form method="post" action="userSurveyList">
						<th>
							<input type="submit" name="surveySent" value="Title">
						</th>
						<th>
							<input type="submit" name="surveySent" value="Company">
						</th>
						<th>
							<input type="submit" name="surveySent" value="Reward">
						</th>
						<th>
							Estimated Time (mn)
						</th>
						<th>
							Already Taken?
						</th>
						<th>
							Go!
						</th>
					</form>
				</tr>'''
			i=0
			for surv in allSurveys:
				if i%2==0:
					surveyForm += '<tr><td>'
				else:
					surveyForm += '<tr class="alt"><td>'
				surveyForm += surv.title
				surveyForm += '</td><td>'
				surveyForm += surv.company
				surveyForm += '</td><td>$'
				surveyForm += str(len(surv.questions)*float(surv.incentive)*0.5)
				surveyForm += '</td><td>'
				surveyForm += str(len(surv.questions))
				surveyForm += 'mn</td><td>'
				if surveyWillDuplicate(str(surv.surveyId), currentUserFromDb.answerToSurveys):
					surveyForm += "Yes"
				else:
					surveyForm += "No"
				surveyForm += '</td><td>'
				surveyForm += '<input type="submit" name="surveySent" value="'
				surveyForm += str(surv.surveyId)
				surveyForm += '"></td></tr>'
				i+=1
			surveyForm += '</table>'
			#--
			tValues = {'urlLogin': createLoginUrl(self)[0],'urlLoginText': createLoginUrl(self)[1],
				'user': createLoginUrl(self)[2], 'pageTitle': pageTitle, 'surveyForm': surveyForm}
			path = os.path.join(os.path.dirname(__file__),'user_survey_list.html')
			self.response.out.write(template.render(path, tValues))
		else:
			thisSurveyId = State
			currentSurvey = pickSurvey(thisSurveyId)
			currentSurveyTitle = currentSurvey.title
			#Generate Form to Take Survey
			#myForm = generateSurveyForm(currentSurvey)
			### Substitute myForm by Screening Questions Form ###
			myForm = displayScreeningQuestions(currentSurvey)
			tValues = {'urlLogin': createLoginUrl(self)[0],'urlLoginText': createLoginUrl(self)[1],
				'user': createLoginUrl(self)[2], 'pageTitle': pageTitle, 'currentSurveyTitle':currentSurveyTitle, 'myForm': myForm, 'surveyId':thisSurveyId}
			path = os.path.join(os.path.dirname(__file__),'user_take_survey1.html')
			self.response.out.write(template.render(path, tValues))

class userSubmitSurvey(webapp.RequestHandler):
	def post(self):
		pageTitle = "Take a Survey"
		State = self.request.get("surveySent")
		duplicateQuestion = self.request.get("duplicateQuestion")
		if State=="Submit":
			i = 0
			answerList = []
			thisSurveyId = self.request.get("thisSurveyId")
			currentSurvey = pickSurvey(thisSurveyId)
			while (i <len(currentSurvey.questions)):
				answerType = str(fetchAnswer(currentSurvey.answers[i])[0])
				currentAnswer = "answer" + str(i)
				myAnswer = self.request.get(currentAnswer)
				answerList.append(myAnswer)
				i += 1
			answerKey = "answer" + str(i)
			duplicateAnswer = self.request.get(answerKey)	##CHECK HERE###
			thisQuestions = currentSurvey.questions
			currentIncentive = currentSurvey.incentive
			numberOfQuestions = len(currentSurvey.questions)
			moneyEarned = float(currentIncentive)*numberOfQuestions
			thisTitle = currentSurvey.title
			thisCompany = currentSurvey.company
			#at this point, need to compare thisSurveyId to surveyId's in User.answerToSurveys before uploading to datastore.
			user = users.get_current_user()
			thisUser = pickUser(str(user.user_id()))
			#Check should go here.
			if (surveyWillDuplicate(thisSurveyId,thisUser.answerToSurveys) or duplicateQuestionFailed(thisQuestions, answerList, duplicateQuestion, duplicateAnswer)):
				message = "Sorry, "
				if surveyWillDuplicate(thisSurveyId,thisUser.answerToSurveys):
					message += "You already took this survey, so you can't take it again. "
				if duplicateQuestionFailed(thisQuestions, answerList, duplicateQuestion, duplicateAnswer):
					message += "You didn't answer the questions properly."
			#----------
			else:
				thisUser.answerToSurveys.append(encodeSurveyAnswer(thisSurveyId, answerList))
				message = '$' + str(moneyEarned) + ' will be added to your account.'
				if thisUser.credit == "0":
					thisUser.credit = moneyEarned
				else:
					thisUser.credit += moneyEarned
				thisUser.surveysTaken.append(int(thisSurveyId))
				thisUser.put()
			#----------
			myForm = '<table border="1" id="surveyList"><th>Question</th><th>Answer</th>'
			i=0
			for i in range(len(currentSurvey.questions)):
				if fetchQuestion(currentSurvey.questions[i])[0] == "0":
					if i%2==0:
						myForm += '<tr><td>' + fetchQuestion(currentSurvey.questions[i])[1] + '</td><td>' + answerList[i] + '</td></tr>'
					else:
						myForm += '<tr class="alt"><td>' + fetchQuestion(currentSurvey.questions[i])[1] + '</td><td>' + answerList[i] + '</td></tr>'
					i+=1
			myForm += '</table>'
						
			tValues = {'urlLogin': createLoginUrl(self)[0],'urlLoginText': createLoginUrl(self)[1],
				'user': createLoginUrl(self)[2], 'pageTitle': pageTitle, 'myForm': myForm, 'message':message,
				'thisTitle':thisTitle,'thisCompany':thisCompany}
			path = os.path.join(os.path.dirname(__file__),'user_survey_complete.html')
			self.response.out.write(template.render(path, tValues))
		else: #GO BACK TO THE LIST OF SURVEYS
			pageTitle = "Surveys"
			allSurveys = db.GqlQuery("SELECT * FROM Survey")
			surveyForm = '''
			<table border="1" id="surveyList">
				<tr>
					<form method="post" action="userSurveyList">
						<th>
							<input type="submit" name="surveySent" value="Title">
						</th>
						<th>
							<input type="submit" name="surveySent" value="Company">
						</th>
						<th>
							<input type="submit" name="surveySent" value="Reward">
						</th>
						<th>
							Estimated Time (mn)
						</th>
						<th>
							Already Taken?
						</th>
						<th>
							Go!
						</th>
					</form>
				</tr>'''
			i=0
			for surv in allSurveys:
				if i%2==0:
					surveyForm += '<tr><td>'
				else:
					surveyForm += '<tr class="alt"><td>'
				surveyForm += surv.title
				surveyForm += '</td><td>'
				surveyForm += surv.company
				surveyForm += '</td><td>$'
				surveyForm += str(len(surv.questions)*float(surv.incentive)*0.5)
				surveyForm += '</td><td>'
				surveyForm += str(len(surv.questions))
				surveyForm += 'mn</td><td>'
				if surveyWillDuplicate(str(surv.surveyId), currentUserFromDb.answerToSurveys):
					surveyForm += "Yes"
				else:
					surveyForm += "No"
				surveyForm += '</td><td>'
				surveyForm += '<input type="submit" name="surveySent" value="'
				surveyForm += str(surv.surveyId)
				surveyForm += '"></td></tr>'
				i+=1
			surveyForm += '</table>'
			#--
			tValues = {'urlLogin': createLoginUrl(self)[0],'urlLoginText': createLoginUrl(self)[1],
				'user': createLoginUrl(self)[2], 'pageTitle': pageTitle, 'surveyForm': surveyForm}
			path = os.path.join(os.path.dirname(__file__),'user_survey_list.html')
			self.response.out.write(template.render(path, tValues))
	
class userAnswerScreeningQuestions(webapp.RequestHandler):
	def post(self):
		pageTitle = "Taking Survey - Part 2/2"
		thisSurveyId = self.request.get("thisSurveyId")
		thisSurvey = pickSurvey(thisSurveyId)
		currentSurveyTitle = thisSurvey.title
		
		# Process screening questions here #
		userAnswerToScreeningQuestions = []
		# Need to get them by using the screeningIndexes property of the Survey class.
		screeningIndexes = thisSurvey.screeningIndexes
		# Need to get answers to screening questions from users
		i=0
		while (i<len(screeningIndexes)):
			currentAnswer = "answer" + str(screeningIndexes[i])
			myAnswer = self.request.get(currentAnswer)
			userAnswerToScreeningQuestions.append(myAnswer)
			i += 1
		# Compare them in order to the value of the rightAnswers list property of the Survey class.
		if userPassesScreeningQuestion(thisSurvey, userAnswerToScreeningQuestions) == False:
			message = "Sorry, you don't qualify for this survey. <br />"
			State = self.request.get("surveySent")
			if (State == "Submit"):
				myForm = ""
				tValues = {'message': message,'ats':userAnswerToScreeningQuestions, 'urlLogin': createLoginUrl(self)[0],'urlLoginText': createLoginUrl(self)[1],
					'user': createLoginUrl(self)[2], 'pageTitle': pageTitle, 'myForm': myForm, 'surveyId':thisSurveyId, 'currentSurveyTitle':currentSurveyTitle}
				path = os.path.join(os.path.dirname(__file__),'user_take_survey2.html')
				self.response.out.write(template.render(path, tValues))
		else:			
		# Create a function ?
		# If function return True, move on. Otherwise, mark survey as taken and display error message.
			State = self.request.get("surveySent")
			if (State == "Submit"):
				myForm = generateSurveyForm(thisSurvey)
				tValues = { 'ats':userAnswerToScreeningQuestions, 'urlLogin': createLoginUrl(self)[0],'urlLoginText': createLoginUrl(self)[1],
					'user': createLoginUrl(self)[2], 'pageTitle': pageTitle, 'myForm': myForm, 'surveyId':thisSurveyId, 'currentSurveyTitle':currentSurveyTitle}
				path = os.path.join(os.path.dirname(__file__),'user_take_survey2.html')
				self.response.out.write(template.render(path, tValues))
			
class userUpdateProfile(webapp.RequestHandler):
	def post(self):
		pageTitle = "Profil Updated"
		State = self.request.get("surveySent")
		age = self.request.get("age")
		gender = self.request.get("gender")
		familySize = self.request.get("familySize")
		numberOfChildren = self.request.get("numberOfChildren")
		maritalStatus = self.request.get("maritalStatus")
		householdIncome = self.request.get("householdIncome")
		education = self.request.get("education")
		ethnicity = self.request.get("ethnicity")
		religion = self.request.get("religion")
		occupation = self.request.get("occupation")
		thisUser = users.get_current_user()
		thisUser = pickUser(thisUser.user_id())
		if age != '':
			thisUser.age = int(age)
			thisUser.targetProfile[0] = True
		thisUser.gender = gender
		if gender != "":
			thisUser.targetProfile[1] = True
		if familySize != '':
			thisUser.familySize = int(familySize)
			thisUser.targetProfile[2] = True
		if numberOfChildren != '':
			thisUser.numberOfChildren = int(numberOfChildren)
			thisUser.targetProfile[3] = True
		if householdIncome != '':
			thisUser.householdIncome = float(householdIncome)
			thisUser.targetProfile[4] = True
		thisUser.maritalStatus = maritalStatus
		if maritalStatus != "":
			thisUser.targetProfile[5] = True
		thisUser.education = education
		if education != "":
			thisUser.targetProfile[6] = True
		thisUser.ethnicity = ethnicity
		if ethnicity != "":
			thisUser.targetProfile[7] = True
		thisUser.religion = religion
		if religion != "":
			thisUser.targetProfile[8] = True
		thisUser.occupation = occupation
		if occupation != "":
			thisUser.targetProfile[9] = True
		thisUser.put()
		tValues = {'urlLogin': createLoginUrl(self)[0],'urlLoginText': createLoginUrl(self)[1],
			'user': createLoginUrl(self)[2], 'pageTitle': pageTitle, 'age': age, 'gender':gender, 'familySize':familySize, 'numberOfChildren':numberOfChildren, 'maritalStatus':maritalStatus, 'householdIncome':householdIncome, 'education': education, 'ethnicity': ethnicity, 'religion': religion, 'occupation':occupation}
		path = os.path.join(os.path.dirname(__file__),'user_general_information.html')
		self.response.out.write(template.render(path, tValues))
		
class userTOS(webapp.RequestHandler):
	def post(self):
		user = users.get_current_user()
		thisUser = pickUser(str(user.user_id()))
		thisUser.TOS = True
		thisUser.put()
		status = "You've read and accepted the Term and Conditions."
		path = os.path.join(os.path.dirname(__file__),'user_cat_logged.html')
		tValues = {'status':status}
		self.response.out.write(template.render(path, tValues))

class adminCreateNews(webapp.RequestHandler):
	def get(self):
		user = users.get_current_user()
		thisUser = pickUser(str(user.user_id()))
#		if (thisUser.admin != True):
#			path = os.path.join(os.path.dirname(__file__),'index.html')
#			self.response.out.write(template.render(path, ''))
#		else:
		myNewsForm = '''
					<u>ADMINISTRATOR DASHBOARD</u></br><br/>
					Post some news:<br />
					<form method="post" action="uploadNews">
					Content: <input type="text" size="100" name="content">
					<input type="submit" value="Submit">'''
		path = os.path.join(os.path.dirname(__file__),'admin_create_news.html')
		tValues = {'myNewsForm':myNewsForm}
		self.response.out.write(template.render(path, tValues))
		
class uploadNews(webapp.RequestHandler):
	def post(self):
		thisContent = self.request.get("content")
		newPost = News(content = thisContent)
		newPost.put()
		myNewsForm = '''Post some news:<br /><br />
					<form method="post" action="uploadNews">
					Content: <input type="text" size="100" name="content">
					<input type="submit" value="Submit">'''
		path = os.path.join(os.path.dirname(__file__),'admin_create_news.html')
		tValues = {'myNewsForm':myNewsForm}
		self.response.out.write(template.render(path, tValues))
		
class companySurveys(webapp.RequestHandler):
	def get(self):
		user = users.get_current_user()
		if user:
			thisCompany = pickCompany(user.user_id())
			thisSurveys = thisCompany.surveys
			allSurveys = db.GqlQuery("SELECT * FROM Survey")
			surveyForm = '''
			<table border="1" id="surveyList">
				<tr>
					<form method="post" action="companySelectSurvey">
					<th>Name</th>
					<th>Number of Inputs</th> 
					<th>See/Export Answers</th>
				</tr>'''
			i=0
			for surv in allSurveys:
				if (surveyFromCompany(thisSurveys, surv)):
					if i%2==0:
						surveyForm += '<tr><td>'
					else:
						surveyForm += '<tr class="alt"><td>'
					surveyForm += surv.title
					surveyForm += '</td><td>'
					surveyForm += str(numberOfUsersWhoTookSurvey(surv.surveyId))
					surveyForm += '</td><td>'
					surveyForm += '<input type="submit" name="surveyId" value="' + str(surv.surveyId) + '">'
					surveyForm += '</td></tr>'
					i += 1
			surveyForm += '</form></table>'
		
			tValues = {'urlLogin': createLoginUrl(self)[0],'urlLoginText': createLoginUrl(self)[1],
				'user': createLoginUrl(self)[2], 'surveyForm': surveyForm}
			path = os.path.join(os.path.dirname(__file__),'companySurveys.html')
			self.response.out.write(template.render(path, tValues))
		else:
			pageTitle = "Login"
			tValues = {'urlLogin': createLoginUrl(self)[0],'urlLoginText': createLoginUrl(self)[1],
				'user': createLoginUrl(self)[2], 'pageTitle': pageTitle}
			path = os.path.join(os.path.dirname(__file__),'index_company.html')
			self.response.out.write(template.render(path, tValues))
			

class  companySelectSurvey(webapp.RequestHandler):
	def post(self):
		thisSurveyId = self.request.get("surveyId")
		thisSurvey = pickSurvey(thisSurveyId)
		allUsers = db.GqlQuery("SELECT * FROM User")
		surveyForm = ""
		
		for k in range(len(thisSurvey.questions)):
			surveyForm += '<table border="1" id="surveyList"><tr><th>Question</th><th>Answers</th></tr>'
			surveyForm += '<tr><td>' + fetchQuestion(thisSurvey.questions[k])[1] + '</td><td></td></tr>'
			for aUser in allUsers:
				#select survey answer list in User
				for thisAnswer in aUser.answerToSurveys:
					if (decodeSurveyAnswer(thisAnswer)[0] == thisSurveyId):
						surveyForm += '<tr id="nick"><td>'
						surveyForm += aUser.nick
						surveyForm += '</td><td>' 
						if (createSingleAnswerList(decodeSurveyAnswer(thisAnswer)[1])[k][0] == ":"):
							surveyForm += createSingleAnswerList(decodeSurveyAnswer(thisAnswer)[1])[k][1:]
						else:
							surveyForm += createSingleAnswerList(decodeSurveyAnswer(thisAnswer)[1])[k]
						surveyForm += '</td></tr>'
						break
						
				
			surveyForm += '</table><br />'
			
		tValues = {'urlLogin': createLoginUrl(self)[0],'urlLoginText': createLoginUrl(self)[1],
			'user': createLoginUrl(self)[2], 'surveyForm': surveyForm}
		path = os.path.join(os.path.dirname(__file__),'company_survey_results.html')
		self.response.out.write(template.render(path, tValues))		
	

application = webapp.WSGIApplication( 
									[('/', myHandler), 
#									('/indexUser', indexUser),
									('/indexCompany', indexCompany),
									('/userSurveyList', userSurveyList),
									('/userAccount', userAccount),
									('/companyAccount', companyAccount),
									('/companyCreateSurvey', companyCreateSurvey),
									('/userCat', userCat),
									('/companyCat', companyCat),
									('/userCredit', userCredit),
									('/userWithdrawal', userWithdrawal),
									('/userReferral', userReferral),
									('/userGeneralInformation', userGeneralInformation),
									('/companyStepOne', companyStepOne),
									('/companyStepTwo', companyStepTwo),
									('/companyStepThree', companyStepThree),
									('/companyStepFour', companyStepFour),
									('/companyStepFive', companyStepFive),
									('/userChooseSurvey', userChooseSurvey),
									('/userSubmitSurvey', userSubmitSurvey),
									('/userUpdateProfile', userUpdateProfile),
									('/TOS', userTOS),
									('/CreateNews', adminCreateNews),
									('/uploadNews', uploadNews),
									('/companySurveys', companySurveys),
									('/companySelectSurvey', companySelectSurvey),
									('/userAnswerScreeningQuestions', userAnswerScreeningQuestions),
									('/companySurveyComplete', companySurveyComplete),
									('/mobileRequest', mobileRequest)],
									debug=True)

def main():
	run_wsgi_app(application)

if __name__ == "__main__":
		main()
				
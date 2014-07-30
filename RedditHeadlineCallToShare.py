#! /Library/Frameworks/Python.framework/Versions/2.7/bin/python

# Matt Rkiouak, 4/19/2014, Phone Contact: 781 492 8024, Email Contact: rkiouak@me.com

# Script retrieves top headline from Reddit frontpage, formats onto a URL
# and uses twilio to call a phone number & read the headline using twimlets.com

# Dependencies for running this script requests, time, twilio.rest, lxml, argparse,
# sys, logging, urllib

#Currently scheduled via cronjob, will mail "Done" if script runs successfully

import requests, time, argparse, logging, sys
from twilio.rest import TwilioRestClient
from lxml import html
from httplib2 import httplib2
from urllib import urlencode

def testUrlAndReturnPage(urlToTest, numbersToNotify):
# Function for testing URLs and handling errors. Does not gracefully handle poorly formed
# urls and other rare errors, but takes care of the beyond administrator's control error
# if a outside url becomes unavailable because of WAN/Internet/remote host failure.
	try:
		page = requests.get(urlToTest)
		return page
	except requests.ConnectionError: # Send SMS notifying users of error
		for x in numbersToNotify:
			message = client.messages.create(body=("Matt's laptop failed to reach %s. "
												   "Error text sent to you & Matt"
												    % (urlToTest,)),
			to=x,
			from_=phoneNumberToCallFrom)
	
		# Log error to file	
		logging.basicConfig(filename='RedditCallLog.log',level=logging.DEBUG)
		logging.error(str(time.asctime(time.localtime(time.time())))+" "+"Critical Error: "
			"Failed to reach: %s " % (urlToTest,))
		sys.exit(1)

if __name__ == "__main__":
# Program accepts commandline arguments for phone number to place call to, website to 
# scrape, the xpath location to pull string from, the twilio account sid and the twilio
# auth token. All arguments are optional

parser = argparse.ArgumentParser(prog='RedditHeadlineCall', usage=("Program used to "
																   "place a call to a " 
																   "phone number and "
																   "read a headline from "
																   "a specified " 
																   "xml.xpath scraped "
																   "from a website"))
																   
parser.add_argument("--phone-to-call", type=str, help=("The phone # to call w/ scraped "
													   "string"), 
					default="")
													 
parser.add_argument("--website-to-query", type=str, help=("The website to scrape string "
														   "from. MUST start http:// "
														   "i.e. a fully qualified url"),
					default ="http://www.reddit.com")

parser.add_argument("--xpath-to-say", type=str, help=("The xpath location of the string "
													  "to read"), 
					default="//*[@id='siteTable']/div[1]/div[2]/p[1]/a/text()")
 
parser.add_argument("--account-sid", type=str, help="The twilio account id to use", 
					default="ACbe930b1493894647f69ac1c37d5a04f8")

parser.add_argument("--auth-token", type=str, help = "The twilio auth_token to use",
 					default="780b46e00098205b4fa6b230ae337c8e")

args = parser.parse_args()

account_sid = args.account_sid
auth_token = args.auth_token

# Instantiates twilio REST client with account credentials

client = TwilioRestClient(account_sid, auth_token)

#Phone numbers used in Twilio call

phoneNumberToCall = args.phone_to_call
phoneNumberToCallFrom = "" # Taken from Twilio Account
administratorPhoneNumber = "" # Used to SMS when errors occur

numbersToNotifyIfError = (phoneNumberToCall, administratorPhoneNumber)

# URL location of string to be read over twilio phone call
######### MUST RETURN XML FOR CURRENT IMPLEMENTATION TO FUNCTION

urlToRequest = args.website_to_query

#XPath within retrieved XML document of string to be read on call

xpathToSay = args.xpath_to_say

# Uses requests module to retreive html/xml located at specified url. Will handle 
# connectionError by sending text message & writing to file if url is down.

page = testUrlAndReturnPage(urlToRequest, numbersToNotifyIfError)
	
# Uses lxml html module to parse webpage into tree/hierarchical format
# Allowing for use of .xpath to retrieve specific attribute, element

tree = html.fromstring(page.text)

headline = tree.xpath(xpathToSay)

#headline to send via SMS if twimlets request fails

headlineString = headline.pop()

# Append formatted reddit headline to twimlets simple message URL
######### A DIFFERENT IMPLEMENTATION COULD QUERY URL SERVING 'TwiML' FORMATTED DOCUMENT--
######### THIS IMPLEMENTATION WOULD HAVE STRING INSERTED INTO appropriate XML/'TwiML' 
######### LOCATION ON WEBSERVER
# requests.post(url, data=headlineString) was not working within the twilio 
# client.calls.create() line [And it isn't clear to me that it's intended to, though this
# would seem an elegant way for delivering text to read. There may be a method similar to
# the TwiML <Say> markup that would cause it to recognize post messages with strings, but
# at this time the Twilio documentation was insufficient for the developer to implement
# this.

urlMessage=("http://twimlets.com/message?Message%5B0%5D=Call%20Script%20Written%20By%20"
			"Matt%20Are%20Key%20Walk%20.The%20Top%20Reddit%20Headline%20Right%20Now%20Is:"
			"%20"+urlencode(headlineString))

# Confirm http://twimlets.com/message... is up and reachable
testUrlAndReturnPage(urlMessage, numbersToNotifyIfError)

# Place Twilio call, 'error handling' is done after the fact by writing to flat file
##### AREAS FOR FURTHER INVESTIGATION IF SCRIPT IS TO BE EXPANDED: Programmatically 
# sending the administrator notifications if Twilio was unable to retrive TwiML at
# specified URL, and handling other Twilio exceptions from 
# Twilio notifications.get(call.sid) log. Example error that occurred during development 
# of this script is Twilio Error:111000 
# www.twilio.com/user/account/developer-tools/app-monitor/errors/11100

call = client.calls.create(to=phoneNumberToCall,  # Any phone number
                          from_=phoneNumberToCallFrom, # Must be a valid Twilio number
                                                   url=urlMessage)

#Simple logging to confirm twilio calls.create executed and 
#Twilio has record of call to expected number

logging.basicConfig(filename='CallLog.log', format="%(asctime)s %(message)s", level=logging.DEBUG)
logging.debug(str(time.asctime(time.localtime(time.time())))+" redditHeadlineCall.py "+
headlineString+" "+urlMessage+" call.sid: "+call.sid+" call placed to: "+call.to)

print "Done"

import os
import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from flask import Flask, request
from apiclient.discovery import build
from httplib2 import Http
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import requests
import random
import gspread
import ast
import time

scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('Mproject se-d9c1fa9d894f.json', scope)
client = gspread.authorize(creds)

app = Flask(__name__)
bot_id= os.environ.get('BOT_ID')
API_ACCESS_TOKEN= os.environ.get('API_ACCESS_TOKEN')

images=['img/vibes/7wp4gql9aes31.jpg','img/vibes/962r4t81n7l31.jpg','img/vibes/kbrzhelrcqt31.jpg']
nuke=['nuke/nuke1.gif','nuke/nuke2.gif','nuke/nuke3.gif','nuke/nuke4.gif','nuke/nuke5.gif','nuke/nuke6.gif','nuke/nuke7.gif']
# Called whenever the app's callback URL receives a POST request
# That'll happen every time a message is sent in the group
@app.route('/', methods=['POST'])
def webhook():
	
	# 'message' is an object that represents a single GroupMe message.
	message = request.get_json()
	currentuser= message['user_id']
	currentmessage = message['text'].lower().strip()


	if (currentuser == os.getenv('BOT_ID')):
		return

	commands = map_strings_to_functions()

	command_function_requested = commands.get(currentmessage)

	if (command_function_requested) is not None:
		command_function_requested(currentuser)
	else:
		parse_normal_user_message(currentmessage,currentuser)

	sheet = client.open("Information").sheet1
	if '/help' == message['text'].lower() and not sender_is_bot(message):
		reply('General commands \r\n /t - gives info on club events/tournaments \r\n /help - gives help about using the bot \r\n /flipcoin - flips a coin') 
	if message['text'].lower() == '/t' and not sender_is_bot(message):
		reply(sheet.cell(2,1).value)
	if message['text'].lower() == '/meme' and not sender_is_bot(message):
		send('ok','img/rip.png')
	if message['text'].lower() == '/flipcoin' and not sender_is_bot(message):
		flip()
	if message['text'].lower() == '/numb' and not sender_is_bot(message):
		reply(currentuser)

	return "ok", 200

def map_strings_to_functions():

    all_commands = {**common_commands(), **privileged_commands()}
    return all_commands

def common_commands():

    common_commands = {'!commands' : commands, '!privcommands' : privcommands}
    return common_commands

def privileged_commands():


    priv_commands = {'!list' : listusers, '!alertall' : alertall, '!nuke' : kaboom, '!globalannouncement' : globalannouncement, '!repannouncement' : repannouncement}

    return priv_commands

def repannouncement(user):
	sheet = client.open("Information").sheet1
	if user_is_privileged(user):
		send_message(sheet.cell(2,1).value)
		alertall(user)
 
def globalannouncement(user):
	sheet = client.open("Information").sheet1
	if user_is_privileged(user):
		send_message(sheet.cell(2,2).value)
		alertall(user)

def listusers(user):
    if user_is_privileged(user):
        group_members = get_group_members()
        send_message(str(group_members))

def long():
    # gets current json representation of the group
    members_json =  get_group_members_json()

    # create dictionary that maps from member usernames to their userid's
    members_dict = create_members_dict(members_json)

    # msg      = the message string to be sent with the mentions
    #               i.e -- '@trent @john @etc...'
    # loci     = nested list where each list contains the start location of the mention
    #            and the length of the mention
    #               i.e -- [[0, 10], [10, 20], ...]
    # user_ids = a list of the user_ids we want to mention
    #               i.e -- [1234, 5678, ...]
    msg = ''
    loci = []
    user_ids = []

    # loops through all current members and builds the message and
    # the loci / user_ids lists for mentioning all users in a single message
    current_pos_in_string = 0
    for member in members_dict:
        msg += '@' + member + ' '
        loci.append([current_pos_in_string, current_pos_in_string + len(msg)])
        user_ids.append(members_dict.get(member))
        current_pos_in_string += len(msg)

    url = 'https://api.groupme.com/v3/bots/post'

    # mentions are sent as attachments to the text
    payload = {
        'attachments' : [
                {
                'type': 'mentions',
                'loci': loci,
                'user_ids': user_ids
                }
            ],
        'bot_id' : os.getenv('BOT_ID'),
        'text' : msg
        }

    r = requests.post(url, json = payload)




def alertall(user):
    if user_is_privileged(user):
        # gets current json representation of the group
        members_json =  get_group_members_json()

        # create dictionary that maps from member usernames to their userid's
        members_dict = create_members_dict(members_json)

        # msg      = the message string to be sent with the mentions
        #               i.e -- '@trent @john @etc...'
        # loci     = nested list where each list contains the start location of the mention
        #            and the length of the mention
        #               i.e -- [[0, 10], [10, 20], ...]
        # user_ids = a list of the user_ids we want to mention
        #               i.e -- [1234, 5678, ...]
        msg = ''
        loci = []
        user_ids = []

        # loops through all current members and builds the message and
        # the loci / user_ids lists for mentioning all users in a single message
        current_pos_in_string = 0
        for member in members_dict:
            msg += '@' + member + ' '
            loci.append([current_pos_in_string, current_pos_in_string + len(msg)])
            user_ids.append(members_dict.get(member))
            current_pos_in_string += len(msg)

        url = 'https://api.groupme.com/v3/bots/post'

        # mentions are sent as attachments to the text
        payload = {
            'attachments' : [
                    {
                    'type': 'mentions',
                    'loci': loci,
                    'user_ids': user_ids
                    }
                ],
            'bot_id' : os.getenv('BOT_ID'),
            'text' : msg
            }

        r = requests.post(url, json = payload)

def commands(user):
 
    common_commands_str = (', '.join('"' + command + '"' for command in common_commands()))

    # spacing for message sending
    msg = ('Current commands are as follows:          %s' % common_commands_str)
    send_message(msg)

def privcommands(user):

    priv_commands_str = (', '.join('"' + command + '"' for command in privileged_commands()))

    msg = ('Current privileged commands are as follows: %s --  please note use of '
           'these commands require elevated privileges granted by the administrator '
           'of this bot' % priv_commands_str)
    send_message(msg)


def command_not_recognized():
    # HIDDEN COMMAND
    #
    # sends a message letting a user know their command was not recognized
    # then sends what the current commands are

    msg = 'Sorry, your command was not recognized, use !commands to see valid user commands'
    send_message(msg)

def user_not_privileged():
    # HIDDEN COMMAND
    #
    # helper function that sends a message explaining the user does not have sufficient
    # permissions to perform a requested command

    msg = "Sorry, you don't have sufficient privileges to perform the requested command"
    send_message(msg)

def send_message(msg):
    # sends a POST request to the GroupMe API with the message to be sent by the bot
    #
    # @Param msg : message to be sent to GroupMe chat

    url = 'https://api.groupme.com/v3/bots/post'

    payload = {
            'bot_id' : os.getenv('BOT_ID'),
            'text' : msg
           }

    response = requests.post(url, json = payload)

def parse_normal_user_message(message, user):
    # parse a normal user message so we can look for invalid command attempts and perform
    # joke responses if we so wish
    #
    # @Param user_message : message to parse
    # @Param user : the user_id of the user requesting to perform this command

    # check for invalid commands
    if message[0] == '!':
        command_not_recognized()

    # check for joke responses, can be toggled on/off in 'parse_for_joke_responses'
    else:
        parse_for_joke_responses(message, user)

def parse_for_joke_responses(user_message, user):
    joke_responses_enabled = False


def get_group_members():
    members_json = get_group_members_json()

    # creates a list of all user's current nicknames in chat
    members = []
    for member in members_json:
        members.append(member.get("nickname"))

    return sorted(members)

def get_group_members_json():
    # returns a json representation of all members in the chat

    url = 'https://api.groupme.com/v3/groups/' + os.getenv('GROUPME_GROUP_ID')

    data = {
            'token' : os.getenv('API_ACCESS_TOKEN')
           }

    response = requests.get(url, params = data)

    # retrieves the json format of all members currently in the chat
    members_json = response.json().get("response").get("members")

    return members_json

def create_members_dict(members_json):

    members_dict = {}
    for member in members_json:
        members_dict[member.get("nickname")] = member.get("user_id")

    return members_dict

def user_is_privileged(user):

    # list of current user_ids with elevated privileges
    priv_users = ast.literal_eval(os.getenv('PRIV_USERS'))

    if user in priv_users:
        return True
    else:
        # user not privileged, send message saying so and return false
        user_not_privileged()
        return False



def flip():
	a = random.randint(0, 1)
	if a == 0:
		v= 'Heads'
	else:
		v= 'Tails'
	reply(v)


# Send a message in the groupchat
def reply(msg):
	url = 'https://api.groupme.com/v3/bots/post'
	data = {
		'bot_id'		: bot_id,
		'text'			: msg
	}
	request = Request(url, urlencode(data).encode())
	json = urlopen(request).read().decode()

def send(message, image_path=None):

    data = { "bot_id": bot_id, "text": message[:990] }

    if image_path is not None:
        with open(image_path, "rb") as image_data:
            r = requests.post(url="https://image.groupme.com/pictures",
                    data=image_data,
                    headers={ "X-Access-Token": API_ACCESS_TOKEN,
                        "Content-Type": "application/png" })
        uploaded_url = r.json()["payload"]["picture_url"]

        data["attachments"] = [ { "type": "image", "url": uploaded_url } ]

    requests.post("https://api.groupme.com/v3/bots/post", json=data)


# Checks whether the message sender is a bot
def sender_is_bot(message):
	return message['sender_type'] == "bot"


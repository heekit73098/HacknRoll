import logging
import random

from telegram import Update, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, dispatcher, CommandHandler, ConversationHandler, Filters, MessageHandler
from telegram.ext.callbackcontext import CallbackContext
from telegram.replykeyboardmarkup import ReplyKeyboardMarkup
from math import radians
# import psycopg2
# from psycopg2 import sql
import urllib.parse as urlparse
import os
import matplotlib.pyplot as plt
import threading
from math import sin, cos, sqrt, atan2
import telegram
import time
import geopy

PORT = int(os.environ.get('PORT', 8443))
TOKEN = '5024172952:AAGh3xT0qcJiPjJQ6tbW3kfRXZN_VcFSRHI'

playersId = {}
playersLocation = {}
startGame = False
gameStarted = False
groupId = -787830379
catcher = 0
runners = []
initLocation = 0
radius = 1000
playersIndex = {}
bot = telegram.Bot(token=TOKEN)
catcherChances = 3

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


def startingGame(groupId):
    global dispatcher
    time.sleep(30)
    bot.sendMessage(chat_id=groupId, text="Starting Game...")
    choose_catcher()
    print(playersId)
    print(playersLocation)
    print(runners)
    for id in playersId.keys():
        dist_dict = {}
        if catcher == id:
            bot.sendMessage(chat_id=id, text="You're the catcher.\nType /show to show the coordinates of all the runners!.\nHowever, you only have 3 chances! Use wisely!")
        else:
            bot.sendMessage(chat_id=id, text="You're the runner. You need to run away from the catcher! But who is the catcher?")
        for others in playersId.keys():
            if others != id:
                value = calc_dist(playersLocation[id], playersLocation[others])
                dist_dict[others] = value
                bot.sendMessage(chat_id=id, text=f"Distance from Player {playersIndex[others]}: {value}")
    while True:
        time.sleep(15)
        playId_copy = playersId.keys()
        for id in playId_copy:
            if (id in runners or id == catcher):
                count = 1
                for others in playId_copy:
                    if others != id and (others in runners or others == catcher):
                        value = calc_dist(playersLocation[id], playersLocation[others])
                        dist_dict[others] = value
                        bot.sendMessage(chat_id=id, text=f"Distance from Player {playersIndex[others]}: {value}")



def start(update: Update, context: CallbackContext):
    if len(context.args) == 1:
        global radius
        radius = float(context.args[0])
    global startGame
    startGame = True
    global groupId
    startGameThread = threading.Thread(target=startingGame, args=(groupId,))
    startGameThread.start()
    keyboard = [[InlineKeyboardButton('Join', url='http://t.me/trial73098bot'), ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        text="Press Join to join game",
        reply_markup=reply_markup
    )

def choose_catcher():
    global gameStarted
    global startGame
    index = 1
    if not gameStarted:
        gameStarted = True
        if playersId:
            print(list(playersId.keys()))
            id = random.choice(list(playersId.keys()))
            global catcher
            catcher = id
            global initLocation
            initLocation = playersLocation[catcher]
            playersIndex[catcher] = index
            index += 1
            playId_copy = playersId.keys()
            for playerid in playId_copy:
                if playerid != catcher:
                    playersIndex[playerid] = index
                    runners.append(playerid)
                    index += 1
        


def calc_dist(player1_loc, player2_loc):
    R = 6373.0

    lat1 = radians(player1_loc.latitude)
    lon1 = radians(player1_loc.longitude)
    lat2 = radians(player2_loc.latitude)
    lon2 = radians(player2_loc.longitude)

    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = (sin(dlat/2))**2 + cos(lat1) * cos(lat2) * (sin(dlon/2))**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance = R * c

    return distance * 1000

def location(update:Update, context:CallbackContext):
    global gameStarted
    if startGame: 
        message = None
        # print(f"id: {update.edited_message.chat.id},{update.edited_message.location.longitude},{update.edited_message.location.latitude}")
        if update.edited_message:
            message = update.edited_message
            playersLocation[update.edited_message.chat.id] = update.edited_message.location
            user = message.from_user
            userid = user.id
            playersId[userid] = user.first_name
        else:
            message = update.message
            playersLocation[update.message.chat.id] = update.message.location
            user = update.message.from_user
            userid = user.id
            playersId[userid] = user.first_name
        print(playersId)
    if gameStarted:
        playId_copy = playersId.keys()
        for player in playId_copy:
            if player in runners or player == catcher:
                if calc_dist(playersLocation[player], initLocation) > radius:
                    print("Out of bounds")
                    runners.remove(player)
                    if len(runners) == 0:
                        bot.sendMessage(chat_id=groupId, text=f"Everyone has been caught. Catchers win")
                    else:
                        bot.sendMessage(chat_id=groupId, text=f"{playersId[player]} is out of bounds. {len(runners)} players are left.")
            if player != catcher and player in runners:
                print(calc_dist(playersLocation[player], playersLocation[catcher]))
                if calc_dist(playersLocation[player], playersLocation[catcher]) < 2.0:
                    print("too slow")
                    runners.remove(player)
                    if len(runners) == 0:
                        bot.sendMessage(chat_id=groupId, text=f"Everyone has been caught. Catchers win")
                    else:
                        bot.sendMessage(chat_id=groupId, text=f"{playersId[player]} has been caught. {len(runners)} players are left.")
        
                

def showCoordinates(update:Update, context:CallbackContext):
    global catcherChances
    if gameStarted and update.message.from_user.id == catcher and catcherChances > 0:      
        catcherChances -= 1
        bot.sendMessage(chat_id=catcher, text=f"You have {catcherChances} chances left") 
        run_copy = runners
        for (i, player) in enumerate(run_copy):
            bot.sendMessage(chat_id=catcher, text=f"Coordinates of player {playersIndex[player]}\nLatitude: {playersLocation[player].latitude}\nLongitude: {playersLocation[player].longitude} ")

def main():
    updater = Updater(token=TOKEN, use_context=True)
    global dispatcher
    dispatcher = updater.dispatcher
    start_handler = CommandHandler('begin', start, pass_args=True) 
    location_handler = MessageHandler(Filters.location, location)
    spell_handler = CommandHandler('show', showCoordinates)
    dispatcher.add_handler(spell_handler)
    dispatcher.add_handler(location_handler)
    dispatcher.add_handler(start_handler)
    updater.start_polling()


if __name__ == '__main__':
    main()

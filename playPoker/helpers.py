from . import poker,cfr
from django.conf import settings

def cardsToStringList(cards):
    """Takes a list of poker.Card objects and converts
    to a list of strings"""
    strList = []
    for card in cards:
        strList.append(str(card))
    return strList

def stringListToCards(strList):
    """Converts a string list to a list of card objects"""
    cardList = []
    for card in strList:
        #value
        if card[0] == "A":
            value = 14
        elif card[0] == "K":
            value = 13
        elif card[0] == "Q":
            value = 12
        elif card[0] == "J":
            value = 11
        elif card[0] == "1":
            value = 10
        else:
            value = int(card[0])

        #suit
        if card[-1] == "♣":
            suit = "c"
        elif card[-1] == "♠":
            suit = "s"
        elif card[-1] == "♥":
            suit = "h"
        elif card[-1] == "♦":
            suit = "d"
        else:
            suit = "badsuit"

        cardList.append(poker.Card(value,suit))

    return cardList


def cardImageURL(card):
    return "/static/playPoker/Images/Cards/"+card.simpleString()+".png"

def blankCardURL():
    return "/static/playPoker/Images/Cards/blank.png"

def AIURL(saveDir):
    return str(settings.BASE_DIR)+"/playPoker/static/playPoker/AI/"+saveDir
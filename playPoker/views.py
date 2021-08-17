from django.template import loader

# Create your views here.
from django.http import HttpResponse
from django.shortcuts import redirect
from . import poker,cfr,helpers
from copy import deepcopy
from .models import Game

def AISelect(request):
    """Allows a player to select the AI they want to play and stores
    it in the session"""
    #if option selected, redirect to game
    if request.method == "POST":
        request.session["AIType"] = request.POST.get("AI")
        return redirect("playPoker")
    else:
        context = {}
        AIs = [("Abstract1","An AI that remembers every action and has simplistic hand assessment"),
               ("Abstract2","An AI that remembers every action and has more complex hand assessment"),
               ("ForgetfulAbstract1","An AI that only remembers recent actions, with simple hand assessment"),
               ("ForgetfulAbstract2","An AI that only remembers recent actions, with more complex hand assessment"),
               ]
        context["AIs"] = AIs
        template = loader.get_template("playPoker/AISelect.html")
        return HttpResponse(template.render(context,request))
    
def skillSelect(request):
    """Allows a player to select their self-assessed skill level, also serves
    as default welcome page"""
    if request.method == "POST":
        request.session["playerSkill"] = request.POST.get("skill")
        return redirect("AISelect")
    else:
        context = {}
        template = loader.get_template("playPoker/skillSelect.html")
        return HttpResponse(template.render(context,request))
    

def playPoker(request):
    """Handles playing poker and related changes in session, submits data
    from completed rounds to a database"""
    bigBlind = 20
    limit = 4
    if "playerSkill" not in request.session or "AIType" not in request.session:
        return redirect("skillSelect")
    #checks if new round/game, evaluates left side first
    #if new round initialise game variables
    if "newRound" not in request.session or request.session["newRound"]:
        playerList = poker.Player.getPlayerList(2,500)
        
        #gets deck for initialising other cards
        deck = poker.Card.getDeck()
        
        #player cards
        playerCards = poker.drawX(2,deck)
        playerList[0].holeCards = playerCards
        request.session["playerCards"] = helpers.cardsToStringList(playerCards)
        
        #AI cards
        AICards = poker.drawX(2,deck)
        playerList[1].holeCards = AICards
        request.session["AICards"] = helpers.cardsToStringList(AICards)
        
        #stores modified deck
        request.session["deck"] = helpers.cardsToStringList(deck)
        
        #stores community cards and puts them in playerList
        commCards = []
        for p in playerList:
            p.communityCards = deepcopy(commCards)
        request.session["commCards"] = helpers.cardsToStringList(commCards)
        
        #sets history as blank
        history = []
        request.session["history"] = history
        
        #if completely new game, player goes first
        if "buttonPos" not in request.session:
            buttonPos = 0
            request.session["buttonPos"] = 0
        #if not retrieve button position passed from prior round
        else:
            buttonPos = request.session["buttonPos"]
        
        #sets button player as active and small blind/big blind bets
        activePlayer = buttonPos
        playerList[activePlayer].bet = int(bigBlind / 2)
        playerList[(activePlayer+1)%2].bet = bigBlind
        request.session["activePlayer"] = activePlayer
        
        #stores bets in session and updates player list
        request.session["AIBet"] = playerList[1].bet
        request.session["playerBet"] = playerList[0].bet
        playerBet = playerList[0].bet
        AIBet = playerList[1].bet
        
        #if not set, track player's current earnings/losses
        if "balance" not in request.session:
            request.session["balance"] = 0
            balance = 0
        else:
            balance = request.session["balance"]
        
        #if not set, track No. rounds player has played
        if "rounds" not in request.session:
            request.session["rounds"] = 0
            rounds = 0
        else:
            rounds = request.session["rounds"]
        
        #sets/resets the displayed history of actions
        request.session["actionLog"] = []
        actionLog = []
        
        #in future will no longer be a new round
        request.session["newRound"] = False
    
    #retrieves session variables
    else:
        deck = helpers.stringListToCards(request.session["deck"])
        playerCards = helpers.stringListToCards(request.session["playerCards"])
        AICards = helpers.stringListToCards(request.session["AICards"])
        commCards = helpers.stringListToCards(request.session["commCards"])
        playerBet = request.session["playerBet"]
        AIBet = request.session["AIBet"]
        buttonPos = request.session["buttonPos"]
        history = request.session["history"]
        activePlayer = request.session["activePlayer"]
        balance = request.session["balance"]
        rounds = request.session["rounds"]
        actionLog = request.session["actionLog"]
        AIType = request.session["AIType"]
        
        
        #puts variables into playerList
        playerList = poker.Player.getPlayerList(2,500)
        playerList[0].bet = playerBet
        playerList[0].holeCards = playerCards
        
        playerList[1].bet = AIBet
        playerList[1].holeCards = AICards
        
        for p in playerList:
            p.communityCards = deepcopy(commCards)
    
    #grabs session variables set by other pages
    AIType = request.session["AIType"]
    playerSkill = request.session["playerSkill"]
    
    #sets AI type
    playerList[1].AI = poker.CFRIntelligence
    if "1" in AIType:
        playerList[1].absLevel = 1
    elif "2" in AIType:
        playerList[1].absLevel = 2
        
    if "forgetful" in AIType.lower():
        playerList[1].forgetful = True
    else:
        playerList[1].forgetful = False
    
    AIinfo, trainingItrs = cfr.getMostRecentSave(helpers.AIURL(AIType))
    
    playerList[1].info = AIinfo
    
    #Gets human player choice if posted and adjusts their bet
    context = {}
    endRound = False
    if request.method == "POST":
        choice = request.POST.get("choice")
        
        if choice != "Next Round":
            history.append(choice)
            actionLog.append("You "+ choice.lower())
        
        if choice == "Raise":
            playerList[0].bet = playerList[1].bet + 20
        elif choice == "Call":
            playerList[0].bet = playerList[1].bet
    
    #if nothing posted, active player is human unless fresh round    
    else:
        if history == [] and buttonPos == 1:
            activePlayer = 1
        else:
            activePlayer = 0
    
    #handle betting, if active player is AI, do two iterations
    if activePlayer == 1:
        itrs = 2
    else:
        itrs = 1
    payoutFound = False
    buttonMoved = False
    roundEndMessage = ""
    for i in range(itrs):
        if cfr.isTerminal(history,playerList):
            
            #Inits database record of results
            data = Game(history = cfr.getHistoryString(history),
                        aiButton = bool(buttonPos),
                        result = 0,
                        aiType = AIType,
                        playerSkill = playerSkill,
                        aiCards = poker.Card.cardListToString(playerList[1].holeCards),
                        aiIterations = trainingItrs,
                        playerCards = poker.Card.cardListToString(playerList[0].holeCards),
                        commCards = poker.Card.cardListToString(playerList[0].communityCards)
                        )
            
            #if last player folded, current p gets pot
            if history[-1] == "Fold":
                if not payoutFound:
                    #player wins
                    if activePlayer == 0:
                        balance += playerList[1].bet
                        roundEndMessage = "AI folds. You win!"
                        data.result = -playerList[1].bet
                        data.save()
                    #AI wins
                    else:
                        balance -= playerList[0].bet
                        roundEndMessage = "You folded. You lose."
                        data.result = +playerList[0].bet
                        data.save()
                    rounds += 1
                    payoutFound = True
            #if final round, inner of showdown gets pot
            else:
                commCards = playerList[0].communityCards
                #gets both players best ranks
                rankList = [poker.getBest(p.holeCards,commCards) for p in playerList]
                winners = poker.getWinningHands(rankList)
                #gives payout
                if not payoutFound:
                    #if not a tie
                    if len(winners) < 2:
                        #if AI won
                        if winners[0] == 1:
                            balance -= playerList[0].bet
                            
                            roundEndMessage = "You lose against AI's "
                            roundEndMessage += poker.handRankToString(rankList[1])
                            roundEndMessage += " with your " + poker.handRankToString(rankList[0])
                            
                            data.result = playerList[0].bet
                            data.save()
                            
                        #if player won
                        else:
                            balance += playerList[1].bet
                            
                            roundEndMessage = "You win with your "
                            roundEndMessage += poker.handRankToString(rankList[0])
                            roundEndMessage += " against AI's " + poker.handRankToString(rankList[1])
                            
                            data.result = -playerList[1].bet
                            data.save()
                    #if tied        
                    else:
                        roundEndMessage = "You draw with "+poker.handRankToString(rankList[0])
                        
                        data.result = 0
                        data.save()
                        
                    rounds += 1
                    payoutFound = True
                    
            #start new round
            request.session["newRound"] = True
            request.session["balance"] = balance
            if endRound or history == ["Fold"]:
                if not buttonMoved:
                    buttonPos = (buttonPos + 1) % 2
                    buttonMoved = True
            request.session["buttonPos"] = buttonPos
            
            endRound = True
            
            
            
        
        elif cfr.roundOver(history):
            history+=["Round"]
            #flop
            if len(playerList[0].communityCards) < 3:
                newCards = poker.drawX(3,deck)
            #turn & river
            else:
                newCards = poker.drawX(1,deck)
    
            #updates com cards
            for p in playerList:
                p.communityCards += newCards
                
                
            #saves updated cards to session    
            commCards = p.communityCards
            request.session["commCards"] = helpers.cardsToStringList(commCards)
            request.session["deck"] = helpers.cardsToStringList(deck)
        
        #gets the valid actions a player/AI can take
        actions = []
        #if bet limit reached, ban raising
        if endRound:
            actions = []
        elif history[len(history) - limit : len(history)] == ["Raise"]*limit:
            actions = ["Call","Fold"]
        #prevents index error
        elif len(history) == 0:
            actions = ["Call","Fold","Raise"]
        #necessary response actions, fold removed when check is possible
        elif history[-1] == "Raise":
            actions = ["Call","Fold","Raise"]
        elif history[-1] == "Check" or history[-1] == "Call" or history[-1]=="Round":
            actions = ["Check","Raise"]
            
        context["formChoices"] = actions
        
        #performs AI's action based on infoset
        if activePlayer == 1 and len(actions)>0:
            playerList[1].history = history
            action,_ = playerList[1].AI(actions,playerList[1])            
            if action == "Raise":
                playerList[1].bet = playerList[0].bet + 20
            elif action == "Call":
                playerList[1].bet = playerList[0].bet
                
            history.append(action)
            actionLog.append("AI " + action.lower() + "s")
            
            
        
        activePlayer = (activePlayer + 1) % 2
    
    #puts the cards into context so they can be displayed
    #community cards
    for i in range(5):
        if i+1<=len(commCards):
            context["tableCard"+str(i+1)] = helpers.cardImageURL(commCards[i])
        else:
            context["tableCard"+str(i+1)] = helpers.blankCardURL()
    
    #displays player cards
    for i in range(2):
        context["playerCard"+str(i+1)] = helpers.cardImageURL(playerCards[i])
        
    #displays opponent cards, invisible if not showdown
    for i in range(2):
        if endRound:
            context["AICard"+str(i+1)] = helpers.cardImageURL(AICards[i])
        else:
            context["AICard"+str(i+1)] = helpers.blankCardURL()
    
    
    playerBet = playerList[0].bet
    AIBet = playerList[1].bet
    request.session["playerBet"] = playerBet
    request.session["AIBet"] = AIBet
    
    request.session["activePlayer"] = activePlayer
    request.session["rounds"] = rounds
    
    context["playerBet"] = playerBet
    context["AIBet"] = AIBet
    context["balance"] = balance
    context["rounds"] = rounds
    request.session["actionLog"] = actionLog
    if rounds > 0:
        context["mbbg"] = int(((balance/rounds)/bigBlind)*1000)
    else:
        context["mbbg"] = 0
    #log is reversed as log is displayed bottom up
    context["log"] = (actionLog + [roundEndMessage])[::-1]
    request.session["history"] = history
    

    
    
    template = loader.get_template("playPoker/playPoker.html")
    return HttpResponse(template.render(context,request))

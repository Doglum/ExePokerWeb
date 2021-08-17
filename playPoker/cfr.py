import random,pickle,time,os
from . import poker
from copy import deepcopy
class InfoSet():
    def __init__(self,actions):
        #cumulative regrets
        self.cumRegrets = [0 for i in range(len(actions))]
        #cumulative strategy for calc of average
        self.stratSum = [0 for i in range(len(actions))]
        
    def normaliseStrat(self, strat):
        """Turns regrets into probability distrubution strategy"""
        #removes negatives
        noNegatives = [max(x,0) for x in strat]
        normStrat = []
        if sum(noNegatives) > 0:
            for act in noNegatives:
                normStrat.append(act/sum(noNegatives))
                
        #if no strictly positive regrets exist, make uniform dis
        else:
            normStrat = [1/len(strat)]*len(strat)

        return normStrat

    def getStrat(self, reachProb):
        """Returns current strategy for this info set"""
        strat = self.cumRegrets.copy()
        strat = self.normaliseStrat(strat)

        #Updates strategy sum as strategy has been used
        for i in range(len(self.stratSum)):
            self.stratSum[i] += reachProb * strat[i]

        return strat

    def averageStrat(self):
        """Returns average of all used strategies, i.e.
        the approximate Nash equilibrium strategy"""
        return self.normaliseStrat(self.stratSum)

class Sets():
    """Object that stores, retrieves and creates information sets"""
    def __init__(self):
        self.sets = {}
    def getInfoSet(self,params,actions):
        if params not in self.sets:
            self.sets[params] = InfoSet(actions)
        return self.sets[params]

def getHistoryString(history):
    """Converts history list to string"""
    msg = ""
    for i in history:
        if i == "Check":
            msg+="X"
        elif i == "Fold":
            msg+="F"
        elif i == "Raise":
            msg+="R"
        elif i == "Call":
            msg+="C"
        elif i == "Round":
            msg+="_"
    return msg

def forgetfulHistory(history):
    """Converts history list to forgetful history string,
    one where only the actions of this round are remembered"""
    roundCount = len([act for act in history if act=="Round"])
    forgetful = ""
    
    #preflop
    if roundCount == 0:
        forgetful += "p"
        
    #flop
    elif roundCount == 1:
        forgetful += "f"
        
    #turn
    elif roundCount == 2:
        forgetful += "t"
        
    #river
    elif roundCount == 3:
        forgetful += "r"
        
    if roundCount <= 0:
        forgetful += getHistoryString(history)
    else:
        #gets all history after last round
        add = getHistoryString(history)
        addIndex = add.rindex("_")
        forgetful += add[addIndex+1::]
    return forgetful
    

def getCardAbstraction(holeCards,communityCards=[],abstractionLevel = 1,probabilistic = False):
    """Very simple abstraction, groups based on basic hand
    rank (e.g. flush) and nothing else, also abstracts
    preflop based on general attributes"""
    holeCards.sort(key = lambda card:card.value)
    #abstracts based on 4 key attributes for preflop
    if len(communityCards)<3:
        preflop = 1
        #multiplies by primes for unique values per combo
        #suited
        if holeCards[0].suit == holeCards[1].suit:
            preflop *= 2
        #pair
        if holeCards[0].value == holeCards[1].value:
            preflop *= 3
        #adjacent
        if holeCards[0].value + 1 == holeCards[1].value or \
           holeCards[0].value == 2 and holeCards[1].value == 14:
            preflop *= 5
        #XOR, one value is high
        if (holeCards[0].value > 10) != (holeCards[1].value > 10):
            preflop *= 7
        #two values are high
        elif holeCards[0].value > 10 and holeCards[1].value > 10:
            preflop *= 11
            
        return preflop
   
    else:
        if probabilistic:
            #returns probability of better hand rounded to nearest 10%
            prob = poker.betterHandProbability(holeCards,communityCards)
            return round(prob,1)
        else:
            if abstractionLevel == 1:
                return poker.getBest(holeCards,communityCards)[0]
            else:
                #rounds further values into three groups, low, med, high
                values = poker.getBest(holeCards,communityCards)[0:abstractionLevel]
                roundedValues = [values[0]]
                
                for val in values[1:abstractionLevel]:
                    if val >=2 and val<=9:
                        roundedValues.append(1)
                    elif val>=10 and val <=12:
                        roundedValues.append(2)
                    elif val>=13:
                        roundedValues.append(3)
    
                return tuple(roundedValues)
            

def isTerminal(history,players):
    """Returns True if game round is over"""
    if len(history) == 0:
        return False
    elif history[-1] == "Fold":
        return True
    if roundOver(history) and len(players[0].communityCards) == 5:
        return True
    
    return False

def roundOver(history):
    """Returns True if betting round is over"""
    last2 = history[len(history)-2:len(history)]
    end = [
        ["Call","Check"],
        ["Check","Check"],
        ["Raise","Call"]
        ]
    return last2 in end

def payoff(players):
    """Returns pot of inputted player list"""
    #consider doing just opponent bet TODO
    return sum([p.bet for p in players])

def trainCFR(deck,history,players,reachProbs,currentPlayer,sets,limit,absLevel,forgetful,probabilistic):
    """Performs CFR, recursive, on one betting round. Returns payoff and
    updates information sets with regrets as they are processed"""
    his = deepcopy(history)
    #if game over, return payoff and halt recursion
    if isTerminal(his,players):
        #if last player folded, current p gets pot
        if his[-1] == "Fold":
            return payoff(players)
        
        #if final round, winner of showdown gets pot
        else:
            commCards = players[0].communityCards
            #gets both players best ranks
            rankList = [poker.getBest(p.holeCards,commCards) for p in players]
            winners = poker.getWinningHands(rankList)

            #if tie, no payoff (both have bets returned)
            if len(winners) == 2:
                return 0

            #if current player won, get full payoff
            elif winners[0] == currentPlayer:
                return payoff(players)

            #return negative payoff if loser
            else:
                return -payoff(players)

    #----- non-terminal, game continuing -----

    #checks if previous betting round is over, draws new cards if so
    if roundOver(his):
        his+=["Round"]
        #flop
        if len(players[0].communityCards) < 3:
            newCards = poker.drawX(3,deck)
        #turn & river
        else:
            newCards = poker.drawX(1,deck)

        #updates com cards
        for p in players:
            p.communityCards += newCards

    #if bet limit reached, ban raising
    if his[len(his) - limit : len(his)] == ["Raise"]*limit:
        actions = ["Call","Fold"]
    #prevents index error
    elif len(his) == 0:
        actions = ["Call","Fold","Raise"]
    #necessary response actions, fold removed when check is possible
    elif his[-1] == "Raise":
        actions = ["Call","Fold","Raise"]
    elif his[-1] == "Check" or his[-1] == "Call" or his[-1]=="Round":
        actions = ["Check","Raise"]
        
    #converts cards for this player to number value
    if probabilistic: 
        cardValue = getCardAbstraction(players[currentPlayer].holeCards,players[0].communityCards,probabilistic=probabilistic)
    else:
        cardValue = getCardAbstraction(players[currentPlayer].holeCards,players[0].communityCards,absLevel)
    #calculates position of opponent (next player)
    opponent = (currentPlayer + 1) % 2
    
    #creates/gets infoset object for this game state and retrieves strategy
    if forgetful:
        iSet = sets.getInfoSet((forgetfulHistory(his),cardValue),actions)
    else:
        iSet = sets.getInfoSet((getHistoryString(his),cardValue),actions)
    strat = iSet.getStrat(reachProbs[currentPlayer])    

    #stores regrets for each possible action evaluated
    newRegrets = [0 for i in range(len(actions))]

    for i in range(len(actions)):
        #gets each action and its probability of being chosen
        actionProb = strat[i]
        action = actions[i]
        #modifies current player's reach probability
        newReachProbs = reachProbs.copy()
        newReachProbs[currentPlayer] *= actionProb

        #gets copy of players for each scenario
        pl = deepcopy(players)
        if action == "Raise":
            pl[currentPlayer].bet = pl[opponent].bet + 20
        elif action == "Call":
            pl[currentPlayer].bet = pl[opponent].bet

        d = deepcopy(deck)

        #recursive call, passes updated values after processing of this action
        newRegrets[i] = -trainCFR(d,his+[action],pl,newReachProbs,opponent,sets,limit,absLevel,forgetful,probabilistic)

    #value is regrets weighted by action probability
    nodeValue = 0
    for i in range(len(strat)):
        nodeValue += strat[i] * newRegrets[i]

    #updates cumulative regrets
    for i in range(len(strat)):
        iSet.cumRegrets[i] += reachProbs[opponent]*(newRegrets[i] - nodeValue)

    return nodeValue

def doTraining(sets,itr, limit=4, absLevel = 1,forgetful=False,probabilistic = False):
    """Does training on infoset dictionary sets for itr iterations
    bet limit is 4 by default, for quick demo use limit=1"""
    for i in range(itr):
        #creates fresh player list and deck
        playerList = poker.Player.getPlayerList(2,300)
        deck = poker.Card.getDeck()
        history = []
        #gives both players their cards
        for p in playerList:
            p.holeCards=poker.drawX(2,deck)
        #sets first player as small blind, second as big
        playerList[0].bet = 10
        playerList[1].bet = 20
        #performs 1 iteration of training
        value = trainCFR(deck,history,playerList,[1,1],0,sets,limit,absLevel,forgetful,probabilistic)
    return value

class CustomUnpickler(pickle.Unpickler):
    """Required because of import shenanigans and pickle needing file
    definitions and attempting to find them in __main__ where they do not
    exist"""
    def find_class(self, module, name):
        if name == 'Sets':
            return Sets
        if name == "InfoSet":
            return InfoSet
        return super().find_class(module, name)

def loadSets(filename):
    """Returns loaded Sets object from file"""
    return CustomUnpickler(open(filename,"rb")).load()
def saveSets(sets,filename):
    """Saves Sets object to file"""
    pickle.dump(sets,open(filename,"wb"))

def trainFor(sets,mins,startItr,limit=4,saveDir="Saves",saveInterval=100,absLevel = 1,forgetful = False, probabilistic = False):
    """Performs training on sets object for mins minutes,
    will save every saveInterval iterations and at end"""
    info = sets
    start = time.time()
    itrs = startItr
    #while still time
    while (time.time() - start)/60 <= mins:
        itrs += 1
        doTraining(info,1,limit,absLevel,forgetful,probabilistic)
        if itrs % saveInterval == 0:
            saveSets(info,saveDir+"/sets"+str(itrs)+".p")
    end = time.time()
            
    saveSets(info,saveDir+"/sets"+str(itrs)+".p")
    print("Did",itrs-startItr,"iterations, total iterations:",itrs)
    print((end-start)/(itrs-startItr),"seconds per iteration on average")

def getMostRecentSave(saveDir="Saves"):
    """Gets the most recent Sets object save from directory saveDir"""
    saves = os.listdir(saveDir)
    saves.sort(key = lambda x:int(x[4:len(x)-2]))
    itrs = saves[-1].replace("sets","")
    itrs = itrs.replace(".p","")
    return loadSets(saveDir+"/"+saves[-1]),int(itrs)

def newTrainingDirectory(saveDir):
    """Creates a directory saveDir and stores an empty Sets object
    in it called saves0.p"""
    existingFiles = os.listdir()
    if saveDir in existingFiles:
        print("This directory already exists")
        return

    os.mkdir(saveDir)
    info = Sets()
    saveSets(info,saveDir+"/sets0.p")
    
            
if __name__ == "__main__":
    whichTrain = input("Basic or advanced train?(b/a) Add f for forgetful. Put p for probabilistic\n")
    if whichTrain == "b":
        info,itrs = getMostRecentSave("Abstract1")
        print("Current itr:",itrs)
        mins = float(input("Train for how many mins?\n"))
        print("Processing...")
        trainFor(info,mins,itrs, saveDir = "Abstract1", saveInterval=1000)
        
    elif whichTrain == "a":
        info,itrs = getMostRecentSave("Abstract2")
        print("Current itr:",itrs)
        mins = float(input("Train for how many mins?\n"))
        print("Processing...")
        trainFor(info,mins,itrs,saveDir = "Abstract2",absLevel = 2, saveInterval=1000)

    elif whichTrain == "bf":
        info,itrs = getMostRecentSave("ForgetfulAbstract1")
        print("Current itr:",itrs)
        mins = float(input("Train for how many mins?\n"))
        print("Processing...")
        trainFor(info,mins,itrs,saveDir = "ForgetfulAbstract1",absLevel = 1, forgetful=True, saveInterval=1000)

    elif whichTrain == "af":
        info,itrs = getMostRecentSave("ForgetfulAbstract2")
        print("Current itr:",itrs)
        mins = float(input("Train for how many mins?\n"))
        print("Processing...")
        trainFor(info,mins,itrs,saveDir = "ForgetfulAbstract2",absLevel = 2, forgetful=True, saveInterval=1000)

    elif whichTrain == "p":
        info,itrs = getMostRecentSave("ForgetfulProbabilistic")
        print("Current itr:",itrs)
        mins = float(input("Train for how many mins?\n"))
        print("Processing...")
        trainFor(info,mins,itrs,saveDir = "ForgetfulProbabilistic", forgetful=True, probabilistic = True, saveInterval=1)


            
            
        
            
    
    
    
    

    
    







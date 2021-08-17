from django.db import models

# Create your models here.
class Game(models.Model):
    history = models.CharField(max_length=25) #history string of actions
    aiButton = models.BooleanField() #if ai was the button
    result = models.IntegerField(default=0) #winnings for AI +/-
    aiType = models.CharField(max_length=100) #the AI's type, e.g. Abstract1
    aiIterations = models.IntegerField(default=0) #the No. iterations
    playerSkill = models.CharField(max_length=100) #player's self declared skill
    aiCards = models.CharField(max_length=10) #the AI's cards
    playerCards = models.CharField(max_length=10) #the player's cards
    commCards = models.CharField(max_length=50) #the community cards
    
    def __str__(self):
        msg = ""
        msg += "AI Cards: " + self.aiCards
        msg += "| Player Cards: " + self.playerCards
        msg += "| Result: " + str(self.result)
        return msg
    
    
    
    

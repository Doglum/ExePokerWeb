from django import forms

class CallFoldRaise(forms.Form):
    choices = [("Call","Call"),("Fold","Fold"),("Raise","Raise")]
    choice = forms.ChoiceField(choices=choices,widget = forms.RadioSelect)
class CallFold(forms.Form):
    choices = [("Call","Call"),("Fold","Fold")]
    choice = forms.ChoiceField(choices=choices,widget = forms.RadioSelect)
class CheckRaise(forms.Form):
    choices = [("Check","Check"),("Raise","Raise")]
    choice = forms.ChoiceField(choices=choices,widget = forms.RadioSelect)
    
class NewRound(forms.Form):
    pass
    

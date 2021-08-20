# ExePokerWeb
>A self-learning Texas Hold'em AI

This is a final year project based primarily on the research done by the
[University of Alberta Computer Poker Research Group (UACPRG)](https://poker.cs.ualberta.ca/).
For some much more impressive AIs check out the UACPRG's [Deepstack](https://www.deepstack.ai/)
and [Cepheus](http://poker.srv.ualberta.ca/) AIs. ExePoker
is substantially simpler than these AIs and can be trained on a laptop,
no supercomputer required.

### How it works
Counterfactual regret minimization (CFR) is the technique used to train this AI.
This is a reinforcement learning technique that simulates a branching series
of possible scenarios in a game, with the AI using its collected information to
play against itself. The results of these games are recorded with a payoff
function (e.g. chips won/lost) that is used to determine the "regrets" of taking
each action based on how well taking it went. These regrets update the AI's
strategy for the next iteration of training. After many iterations the
strategy will converge upon a Nash equilibrium, a strategy that is theoretically
impossible to do better than. For specific details on how this technique works
I recommend [this paper](https://proceedings.neurips.cc/paper/2007/file/08d98638c6fcd194a4b1e6992063e944-Paper.pdf).
For the implementation used here I have a [detailed report available](https://drive.google.com/file/d/1EXAMA4b0KXujxeHn7e-Bdh7Y32hpc2RF/view?usp=sharing).

The web application itself is a simple Django project that allows players to
pick any of the 4 variants of AI to play against and tracks their winnings
with session variables. Anonymized game results are recorded to a simple
sqlite database. Players can select from 3 betting actions to act on. Folding
when a check is available is disallowed.

### The gameplay screen
![](https://i.imgur.com/74f7EQe.png)

### Running this project locally
1. If cloning this repository, a new secret key will need to be generated and placed
in "ExePokerWeb/settings.py" or create a new credentials.py file with one variable
named SECRET_KEY containing a string of your new key. You can create a new key
using a built in Django function like so:
```Python
    from django.core.management.utils import get_random_secret_key

    print(get_random_secret_key())
```
2. Perform a database migration. Navigate to the root directory of the project
in command prompt and enter this command:
```
    python manage.py migrate
```
3. Run the project on Django's built in web server using:
```
    python manage.py runserver
```
4. If you would like to view the results of recorded games these are viewable at
http://localhost:8000/admin/. You will need to create a new superuser to access
this. To create a new superuser, use command:
```
    python manage.py createsuperuser
```
5. The project should then be running at http://localhost:8000/playPoker/

### Versions
- Django 3.1.6
- Python 3.7

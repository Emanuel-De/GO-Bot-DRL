# Intent Based BartenderAgent with DRL

Based off of the code repo [TC-Bot](https://github.com/MiuLab/TC-Bot) and paper [End-to-End Task-Completion Neural Dialogue Systems](http://aclweb.org/anthology/I17-1074). The main difference is that will be used for a Bartender Environment currently currently covering the ordering of a specific drink at a specific size.
## Details

This shows how to train a simple DQN agent with deep reinforcement learning as a goal-oriented chatbot using a simple user simulator. The code is a simplified version of TC-Bot by MiuLab with the main difference being that this code does not include NLG or NLU components but just trains the dialogue manager. NL components are not necessary to understand how a GO chatbot is trained with DRL and therefore are not implemented.


The database is of movie tickets, the same DB used in TC-Bot. Both the pickle and text versions of the data can be seen in the [data directory](https://github.com/maxbren/GO-Bot-DRL/tree/master/data).

## Important Note
A 5-part tutorial series that describes and goes through important concepts of  code in detail can be found on medium [here](https://medium.com/@maxbrenner110/training-a-goal-oriented-chatbot-with-deep-reinforcement-learning-part-i-introduction-and-dce3af21d383)!

## Dependencies
- Python >= 3.5
- Keras >= 2.24 (Earlier versions probably work)
- numpy

## How to Run
You can train an agent from scratch with ```python train.py```. 

In constants.json you can change hyperparameters including "save_weights_file_path" and "load_weights_file_path" (both relative paths) to save and load weights respectively. For example, to use the pretrained weights in the weights folder, set the value of  "load_weights_file_path" to "weights/model.h5". Weights for both target (tar) and behavior (beh) keras models are saved every time the current success rate is at a new high. 

You can also test an agent with ```python test.py```. But make sure to load weights by setting "load_weights_file_path" in constants.json to a relative path with both behavior and target weights. 

All the constants are pretty self explanatory other than "vanilla" under agent which means DQN (true) or Double DQN (false). Defualt is vanilla DQN. 

Note: If you get an unpickling error in [train](https://github.com/maxbren/GO-Bot-DRL/blob/master/train.py#L46) or [test](https://github.com/maxbren/GO-Bot-DRL/blob/master/test.py#L43) then run ```python pickle_converter.py``` and that should fix it

## Test (or Train) with an Actual User
You can test the agent by inputing your own actions as the user (instead of using a user sim) by setting "usersim" under run in constants.json to false. You input an action and a success indicator every step of an episode/conversation in console. The format for the action input is: intent/inform slots/request slots.

Example action inputs:
- request/moviename: room, date: friday/starttime, city, theater
- inform/moviename: zootopia/
- request//starttime
- done//

In addition the console will ask for an indicator on whether the agent succeeded yet (other than after the initial action input of an episode). Allowed inputs are -1 for loss, 0 for no outcome yet, 1 for success. 

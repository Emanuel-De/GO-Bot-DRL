from typing import ValuesView
from dialogue_config import usersim_intents, all_intents
import random
import copy


emotions = ["negativ", "neutral", "positiv"]
goal_desires = ["low", "high"]
rewards = {'neg_neg': -5, 'neg_neu': 1, 'neg_pos': 10,
           'neu_neg': -7, 'neu_neu': 0.2, 'neu_pos': 10,
           'pos_neg': -10, 'pos_neu': -1, 'pos_pos': 10}

transitions = {}

for user_intent in usersim_intents:
    transitions[user_intent] = {}
    for goal_desire in goal_desires:
        transitions[user_intent][goal_desire] = {}

##################################################################################################################
# transitions for nothing high use case
transitions['nothing']['high']['neg_neg'] = ['utter_request', 'joke', 'utter_nothing', 'inform_right',
                                             'inform_wrong', 'utter_goodbye', 'find_drink_wrong']
transitions['nothing']['high']['neg_neu'] = ['trigger_user']
transitions['nothing']['high']['neg_pos'] = ['find_drink_right']
transitions['nothing']['high']['neu_neg'] = ['joke', 'utter_nothing', 'find_drink_wrong', 'utter_request',
                                             'inform_right', 'inform_wrong', 'utter_goodbye']
transitions['nothing']['high']['neu_pos'] = ['trigger_user', 'find_drink_right']
transitions['nothing']['high']['pos_pos'] = ['trigger_user', 'find_drink_right']
transitions['nothing']['high']['pos_neg'] = ['joke', 'utter_nothing', 'find_drink_wrong', 'utter_request',
                                             'inform_right', 'inform_wrong', 'utter_goodbye']
# transitions for nothing low use case
transitions['nothing']['low']['neg_neg'] = ['utter_request', 'utter_nothing', 'inform_wrong', 
                                            'utter_goodbye', 'find_drink_wrong', 'inform_right']
transitions['nothing']['low']['neg_neu'] = ['find_drink_right']
transitions['nothing']['low']['neg_pos'] = ['joke', 'trigger_user']
transitions['nothing']['low']['neu_neg'] = ['find_drink_wrong', 'utter_request',
                                            'inform_wrong', 'utter_goodbye', 'inform_right']
transitions['nothing']['low']['neu_neu'] = ['utter_nothing']
transitions['nothing']['low']['neu_pos'] = ['trigger_user', 'find_drink_right', 'joke']
transitions['nothing']['low']['pos_pos'] = ['utter_nothing', 'trigger_user', 'find_drink_right']
transitions['nothing']['low']['pos_neu'] = ['joke']
transitions['nothing']['low']['pos_neg'] = ['find_drink_wrong', 'utter_request',
                                            'inform_wrong', 'utter_goodbye', 'inform_right']

##################################################################################################################
# transitions for order_drinks high use case
transitions['order_drinks']['high']['neg_neg'] = ['utter_goodbye', 'utter_nothing', 'trigger_user', 'find_drink_wrong',
                                                  'joke', 'inform_wrong']
transitions['order_drinks']['high']['neg_neu'] = ['inform_right', 'utter_request']
transitions['order_drinks']['high']['neg_pos'] = ['find_drink_right']
transitions['order_drinks']['high']['neu_neg'] = ['joke', 'utter_nothing', 'find_drink_wrong',
                                                  'inform_wrong', 'utter_goodbye', 'trigger_user']
transitions['order_drinks']['high']['neu_neu'] = ['utter_request', 'inform_right']
transitions['order_drinks']['high']['neu_pos'] = ['find_drink_right']
transitions['order_drinks']['high']['pos_pos'] = ['find_drink_right', 'inform_right', 'utter_request']
transitions['order_drinks']['high']['pos_neu'] = ['inform_wrong']
transitions['order_drinks']['high']['pos_neg'] = ['trigger_user', 'joke', 'utter_nothing', 'find_drink_wrong',
                                                  'utter_goodbye']

# transitions for order_drinks low use case
transitions['order_drinks']['low']['neg_neg'] = ['trigger_user', 'utter_nothing', 'inform_wrong', 
                                                 'utter_goodbye', 'find_drink_wrong']
transitions['order_drinks']['low']['neg_neu'] = ['inform_right', 'utter_request', 'find_drink_right']
transitions['order_drinks']['low']['neg_pos'] = ['joke']
transitions['order_drinks']['low']['neu_neg'] = ['trigger_user', 'utter_goodbye']
transitions['order_drinks']['low']['neu_neu'] = ['utter_nothing', 'find_drink_wrong', 'utter_request',
                                                 'inform_wrong']
transitions['order_drinks']['low']['neu_pos'] = ['find_drink_right', 'joke', 'inform_right']
transitions['order_drinks']['low']['pos_neg'] = ['trigger_user', 'utter_goodbye']
transitions['order_drinks']['low']['pos_neu'] = ['find_drink_wrong', 'inform_wrong']
transitions['order_drinks']['low']['pos_pos'] = ['joke', 'utter_request', 'utter_nothing', 'inform_right',
                                                 'find_drink_right']


##################################################################################################################
# transitions for inform high use case
transitions['inform']['high']['neg_neg'] = ['utter_goodbye', 'utter_nothing', 'trigger_user', 'find_drink_wrong',
                                            'joke', 'inform_wrong']
transitions['inform']['high']['neg_neu'] = ['inform_right', 'utter_request']
transitions['inform']['high']['neg_pos'] = ['find_drink_right']
transitions['inform']['high']['neu_neg'] = ['joke', 'utter_nothing', 'find_drink_wrong',
                                            'inform_wrong', 'utter_goodbye', 'trigger_user']
transitions['inform']['high']['neu_neu'] = ['utter_request', 'inform_right']
transitions['inform']['high']['neu_pos'] = ['find_drink_right']
transitions['inform']['high']['pos_pos'] = ['find_drink_right', 'inform_right', 'utter_request']
transitions['inform']['high']['pos_neu'] = ['inform_wrong']
transitions['inform']['high']['pos_neg'] = ['trigger_user', 'joke', 'utter_nothing', 'find_drink_wrong',
                                            'utter_goodbye']

# transitions for inform low use case
transitions['inform']['low']['neg_neg'] = ['trigger_user', 'utter_nothing', 'inform_wrong', 
                                           'utter_goodbye', 'find_drink_wrong']
transitions['inform']['low']['neg_neu'] = ['inform_right', 'utter_request', 'find_drink_right']
transitions['inform']['low']['neg_pos'] = ['joke']
transitions['inform']['low']['neu_neg'] = ['trigger_user', 'utter_goodbye']
transitions['inform']['low']['neu_neu'] = ['utter_nothing', 'find_drink_wrong', 'utter_request',
                                           'inform_wrong']
transitions['inform']['low']['neu_pos'] = ['find_drink_right', 'joke', 'inform_right']
transitions['inform']['low']['pos_neg'] = ['trigger_user', 'utter_goodbye']
transitions['inform']['low']['pos_neu'] = ['find_drink_wrong', 'inform_wrong']
transitions['inform']['low']['pos_pos'] = ['joke', 'utter_request', 'utter_nothing', 'inform_right', 'find_drink_right']

##################################################################################################################
# transitions for request high use case
transitions['request']['high']['neg_neg'] = ['utter_goodbye', 'utter_nothing', 'trigger_user', 'find_drink_wrong',
                                             'joke', 'inform_wrong', 'utter_request']
transitions['request']['high']['neg_neu'] = ['inform_right']
transitions['request']['high']['neg_pos'] = ['find_drink_right']
transitions['request']['high']['neu_neg'] = ['utter_request', 'joke', 'utter_nothing', 'find_drink_wrong',
                                             'inform_wrong', 'utter_goodbye', 'trigger_user']
transitions['request']['high']['neu_neu'] = []
transitions['request']['high']['neu_pos'] = ['find_drink_right', 'inform_right']
transitions['request']['high']['pos_pos'] = ['find_drink_right', 'inform_right']
transitions['request']['high']['pos_neu'] = ['inform_wrong']
transitions['request']['high']['pos_neg'] = ['trigger_user', 'joke', 'utter_nothing', 'find_drink_wrong',
                                             'utter_goodbye', 'utter_request']

# transitions for request low use case
transitions['request']['low']['neg_neg'] = ['trigger_user', 'utter_nothing', 'inform_wrong', 
                                            'utter_goodbye', 'find_drink_wrong', 'utter_request']
transitions['request']['low']['neg_neu'] = ['inform_right', 'find_drink_right']
transitions['request']['low']['neg_pos'] = ['joke']
transitions['request']['low']['neu_neg'] = ['trigger_user', 'utter_goodbye', 'utter_request','find_drink_wrong', 'inform_wrong']
transitions['request']['low']['neu_neu'] = ['utter_nothing']
transitions['request']['low']['neu_pos'] = ['find_drink_right', 'inform_right', 'joke']
transitions['request']['low']['pos_neg'] = ['find_drink_wrong', 'inform_wrong','utter_request', 'trigger_user', 'utter_goodbye']
transitions['request']['low']['pos_pos'] = ['joke', 'utter_nothing', 'inform_right', 'find_drink_right']

##################################################################################################################
# transitions for reject high use case
transitions['reject']['high']['neg_neg'] = ['utter_goodbye', 'utter_nothing', 'trigger_user', 'find_drink_wrong',
                                            'joke', 'inform_wrong']
transitions['reject']['high']['neg_neu'] = ['inform_right']
transitions['reject']['high']['neg_pos'] = ['find_drink_right', 'utter_request']

# transitions for reject low use case
transitions['reject']['low']['neg_neg'] = ['trigger_user', 'utter_nothing', 'inform_wrong', 
                                           'utter_goodbye', 'find_drink_wrong']
transitions['reject']['low']['neg_neu'] = ['inform_right', 'utter_request', 'find_drink_right']
transitions['reject']['low']['neg_pos'] = ['joke']
transitions['reject']['low']['neu_neg'] = ['trigger_user', 'utter_goodbye', 'inform_wrong', 'find_drink_wrong']
transitions['reject']['low']['neu_neu'] = ['utter_nothing', 'inform_right']
transitions['reject']['low']['neu_pos'] = ['find_drink_right', 'joke', 'utter_request']

# ################################################################################################################                         
# transitions for thanks high use case
transitions['thanks']['high']['neg_pos'] = ['utter_goodbye']
transitions['thanks']['high']['neg_neg'] = ['joke', 'trigger_user', 'utter_nothing', 'inform_right', 'find_drink_right',
                                            'utter_request', 'find_drink_wrong', 'inform_wrong']

transitions['thanks']['high']['pos_neg'] = ['trigger_user', 'inform_right', 'find_drink_right',
                                            'utter_request', 'find_drink_wrong', 'inform_wrong']
transitions['thanks']['high']['pos_neu'] = ['joke', 'utter_nothing']
transitions['thanks']['high']['pos_pos'] = ['utter_goodbye']


# transitions for thanks low use case
transitions['thanks']['low']['neg_pos'] = ['utter_goodbye', 'utter_nothing', 'joke',]
transitions['thanks']['low']['neg_neg'] = ['trigger_user', 'inform_right', 'find_drink_right',
                                           'utter_request', 'find_drink_wrong', 'inform_wrong']
transitions['thanks']['low']['neu_neg'] = ['trigger_user', 'utter_nothing', 'inform_right', 'find_drink_right',
                                           'utter_request', 'find_drink_wrong', 'inform_wrong']
transitions['thanks']['low']['neu_pos'] = ['joke', 'utter_goodbye', 'utter_nothing']
transitions['thanks']['low']['pos_neg'] = ['trigger_user', 'inform_right', 'find_drink_right',
                                           'utter_request', 'find_drink_wrong', 'inform_wrong']
transitions['thanks']['low']['pos_pos'] = ['utter_goodbye', 'utter_nothing', 'joke']
##################################################################################################################

class UserMood:
    """Simulates the mood of a real user, to train the agent with intrinsic motivated reinforcement learning."""

    def __init__(self):
        # self.current_mood = {'goal_desire': random.choices(goal_desires, weights = [1, 1], k = 1)[0],
        #                      'emotion': random.choices(emotions, weights = [1, 1, 1], k = 1)[0]}
        self.transitions = transitions
        self.goal_desires = goal_desires
        self.rewards = rewards
        self.emotions = emotions
        self.state = ['UNK' for i in range(8)]
        self.agent_history = []

    def reset(self):
        self.current_mood = {'goal_desire': random.choices(goal_desires, weights=[1, 1], k=1)[0],
                             'emotion': random.choices(emotions, weights=[1, 1, 1], k=1)[0]}  
        self.state = ['UNK' for i in range(8)]
        self.agent_history = []

    def mood_reward(self, done, user_action, agent_action, full_action):
        act_dict = copy.deepcopy(full_action)
        act_dict.pop('round', None)
        self.agent_history.append(act_dict)
        current_transitions = self.transitions[user_action][self.current_mood['goal_desire']]
        intrinsic_reward = None
        forced_transition, extra_punishment = self.find_repetives(agent_action)

        if forced_transition is not None:
            intrinsic_reward = self.calc_reward(done, forced_transition, extra_punishment=extra_punishment)
        else:
            for key, value in current_transitions.items():
                if self.current_mood['emotion'][:3] == key[:3] and agent_action in value:
                    next_em = key[-3:]
                    #emotion schreiben
                    for emotion in self.emotions:
                        if next_em in emotion:
                            next_emotion = emotion
                            self.current_mood['emotion'] = next_emotion
                            break
                    intrinsic_reward = self.calc_reward(done, key)
                    break
        assert intrinsic_reward is not None
        self.state.pop(0)
        self.state.append(agent_action) 
        return intrinsic_reward

    def find_repetives(self, agent_action):
        forced_transition = False
        # We want to punish the agent if he find the exact same drink as before.  
        extra_punishment = 0
        
        if agent_action == self.state[-1] and not agent_action == 'utter_nothing':
            forced_transition = True
        elif self.state.count('find_drink_wrong') >= 1 and agent_action == 'find_drink_wrong':
            forced_transition = True
        elif self.state.count('find_drink_right') >= 2 and agent_action == 'find_drink_right':
            forced_transition = True
        elif agent_action == 'joke' and agent_action in self.state:
            forced_transition = True
        
        # lets check if the the exact same drink was found before and punish that
        if self.agent_history[-1]['intent'] == 'find_drink':
            if self.agent_history[-1] in self.agent_history[:-1]:
                forced_transition = True
                extra_punishment = -10
    
        if forced_transition:
            emotion_key = self.current_mood['emotion'][:3]
            self.current_mood['emotion'] = 'negativ'
            return emotion_key + '_neg', extra_punishment
        else:
            return None, extra_punishment

    def calc_reward(self, done, transition_key, extra_punishment=0):
        reward = 0
        reward = self.rewards[transition_key]
        reward += self.goal_desires.index(self.current_mood['goal_desire']) * -2
        # if done:
        #     reward = self.rewards[transition_key]
        #     reward += self.goal_desires.index(self.current_mood['goal_desire']) * -2
        # else:
            # reward = self.goal_desires.index(self.current_mood['goal_desire']) * -2
        reward += extra_punishment
        return reward

    def _transition_check(self):

        # current_transitions = self.transitions[user_action][self.current_mood['goal_desire']]
        matches = {"neg": [], "neu": [], "pos": []}

        for user_action, dic2 in self.transitions.items():
            for goal_desire, dic3 in dic2.items():
                for currentMood_futureMood, agent_actions in dic3.items():
                    matches[currentMood_futureMood[:3]] += agent_actions
                if user_action != "thanks" and user_action != "reject" and user_action != "goodbye":
                    assert len(matches['neg']) == (len(all_intents) - len(usersim_intents) + 2)
                    assert len(matches['neu']) == (len(all_intents) - len(usersim_intents) + 2)
                    assert len(matches['pos']) == (len(all_intents) - len(usersim_intents) + 2)
                matches = {"neg": [], "neu": [], "pos": []}

if __name__ == "__main__":

    user_mood = UserMood()
    # user_mood._transition_check()
    print(user_mood.current_mood)

    # user_mood.mood_reward('thanks', 'utter_goodbye')
    # print(user_mood.current_mood)
    user_mood.reset()
    print(user_mood.current_mood)

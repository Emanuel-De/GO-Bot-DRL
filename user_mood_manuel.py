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


class UserMood:
    """Simulates the mood of a real user, to train the agent with intrinsic motivated reinforcement learning."""

    def __init__(self):
        self.transitions = transitions
        self.goal_desires = goal_desires
        self.rewards = rewards
        self.emotions = emotions
        self.state = ['UNK' for i in range(8)]
        self.agent_history = []

    def reset(self):
        self.current_mood = {} 
        self.last_mood = {}
        self.state = ['UNK' for i in range(8)]

    def mood_reward(self, done, x1, x2, x3):
        key = self.last_mood['emotion'][:3] + '_' + self.current_mood['emotion'][:3]
        intrinsic_reward = self.calc_reward(done, key)

        assert intrinsic_reward is not None
        return intrinsic_reward


    def calc_reward(self, done, transition_key):
        reward = 0
        reward = self.rewards[transition_key]
        reward += self.goal_desires.index(self.current_mood['goal_desire']) * -2
        return reward

 

if __name__ == "__main__":

    user_mood = UserMood()
    # user_mood._transition_check()
    print(user_mood.current_mood)

    # user_mood.mood_reward('thanks', 'utter_goodbye')
    # print(user_mood.current_mood)
    user_mood.reset()
    print(user_mood.current_mood)

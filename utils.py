from collections import Counter
from dialogue_config import FAIL, SUCCESS
import copy


def convert_list_to_dict(lst):
    """
    Convert list to dict where the keys are the list elements, and the values are the indices of the elements in the list.

    Parameters:
        lst (list)

    Returns:
        dict
    """

    if len(lst) > len(set(lst)):
        raise ValueError('List must be unique!')
    return {k: v for v, k in enumerate(lst)}


def remove_empty_slots(dic):
    """
    Removes all items with values of '' (ie values of empty string).

    Parameters:
        dic (dict)
    """

    for id in list(dic.keys()):
        for key in list(dic[id].keys()):
            if dic[id][key] == '':
                dic[id].pop(key)


def reward_function(success, done, user, classified_agent_action=None, agent_action=None):
    """
    Return the reward given the success.

    Return -1 + -max_round if success is FAIL, -1 + 2 * max_round if success is SUCCESS and -1 otherwise.

    Parameters:
        success (int)

    Returns:
        int: Reward
    """
    int_reward = user.user_mood.mood_reward(done, user.state['last_intent'], classified_agent_action, agent_action)
    ext_reward = goal_reward(success, user.max_round)

    reward = int_reward + user.reward_weight * ext_reward
    return reward

# hyperparamter for external reward
def goal_reward(success, max_round):
    reward = 0
    if success == FAIL:
        reward += -max_round
    elif success == SUCCESS:
        reward += 2 * max_round
    return reward


def dict2sentence(input_dict, sentence_dict):

    intent = input_dict['intent']
    sentence = copy.deepcopy(sentence_dict.get(intent))

    index_offset = 0
    if input_dict['inform_slots'] and sentence.get('inform'):
        for inform in input_dict['inform_slots']:
            index = sentence['inform placeholder'][inform] + index_offset
            sentence['inform'] = sentence['inform'][:index] + input_dict['inform_slots'][inform] + ' ' +  sentence['inform'][index:]
            index_offset += len(input_dict['inform_slots'][inform]) + 1 
        sentence['raw'] = sentence['inform']
    index_offset = 0
    if input_dict['request_slots']:
        for request in input_dict['request_slots']:
            index = sentence['request placeholder'][request] + index_offset
            sentence['request'] = sentence['request'][:index] + request + ' ' + sentence['request'][index:]
            index_offset += len(request) + 1
        if sentence.get('raw'):
            sentence['raw'] += sentence['request']
        else:
            sentence['raw'] = sentence['request']

    return sentence['raw']    

def generate_agent_action_list(dialogue):
    agent_turns = [el for el in dialogue if el['speaker'] == 'Agent']
    # generate a list of agent intents based on the dialogue
    agent_intents = []
    for turn in agent_turns:
        intent = turn['intent']
        if intent == 'utter_request':
            agent_intent = intent + '_' + list(turn['request_slots'].keys())[0]
        elif intent == 'utter_inform':
            agent_intent = intent + '_' + list(turn['inform_slots'].keys())[0]
        elif intent == 'trigger_user':
            agent_intent = intent
        else:
            agent_intent = intent
        agent_intents.append(agent_intent)
    return agent_intents

def efficiency_metric(dialogue, goal_desire='high'):
    """
    Efficiency metric based on the dialogue between the agent and the user as well as the user's goal desire.
    Case of low goal desire:
    All actions apart from those in the list ignore_intent should be taken at a maximum once by the agent.
    Case of high goal desire:
    All actions should be taken at a maximum once.
    :param dialogue: list of dictionaries containing dialogue actions of both the user and the agent.
    :param goal_desire: user's goal desire
    :return:
    """
    agent_intents = generate_agent_action_list(dialogue)
    # calculate the efficiency metric
    intent_counts = Counter(agent_intents)
    if goal_desire == 'high':
        ignore_intents = ()
    else:
        ignore_intents = ('utter_nothing', 'joke')
    for intent in ignore_intents:
        intent_counts[intent] = 1
    metric = len(intent_counts)/sum(intent_counts.values())
    # possibility of punishing utter_nothing in case of high_goal_desire
    # if goal_desire == 'high':
    #   punishment = intent_counts['utter_nothing']/sum(intent_counts.values())
    #   metric = metric - punishment
    return metric
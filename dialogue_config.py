# Special slot values (for reference)
'PLACEHOLDER'  # For informs
'UNK'  # For requests
'anything'  # means any value works for the slot with this value
'no match available'  # When the intent of the agent is match_found yet no db match fits current constraints

#######################################
# Usersim Config

# 'goodbye': no request or inform
# 'rejecty': inform
# 'inform': inform  
# 'order_drinks': request and inform 
# 'request': request and inform 
# 'thanks': nor
# 'thanks': nothing
#######################################
# Used in EMC for intent error (and in user)
usersim_intents = ['order_drinks', 'inform', 'request', 'reject', 'thanks', 'goodbye', 'nothing']
# 2, 1, 2, 0,0,0,
# The goal of the agent is to inform a match for this key
usersim_default_key = 'drinknumber'

# Required to be in the first action in inform slots of the usersim if they exist in the goal inform slots
usersim_required_init_inform_keys = []  #'DRINK'

#######################################
# Agent Config
#######################################

#ToDo: Check drinks that can be hot and cold

# Possible inform and request slots for the agent
agent_request_slots = ['SIZE', 'DRINK', 'TEMP']
agent_inform_slots = ['SIZE', 'DRINK', 'TEMP']

# Possible actions for agent
agent_actions = [ 
    {'intent': 'utter_request', 'inform_slots': {}, 'request_slots': {'DRINK': 'UNK'}},
    {'intent': 'utter_request', 'inform_slots': {}, 'request_slots': {'SIZE': 'UNK'}},
    {'intent': 'utter_request', 'inform_slots': {}, 'request_slots': {'TEMP': 'UNK'}},
    {'intent': 'utter_inform', 'inform_slots': {'DRINK': 'PLACEHOLDER'}, 'request_slots': {}},
    {'intent': 'utter_inform', 'inform_slots': {'SIZE': 'PLACEHOLDER'}, 'request_slots': {}},
    {'intent': 'utter_inform', 'inform_slots': {'TEMP': 'PLACEHOLDER'}, 'request_slots': {}},

    {'intent': 'utter_nothing', 'inform_slots': {}, 'request_slots': {}},
    {'intent': 'trigger_user', 'inform_slots': {}, 'request_slots': {'DRINK': 'UNK'}},
    {'intent': 'find_drink', 'inform_slots': {}, 'request_slots': {}}, # Check wheteher there is a drink in the database - maybe generates 2 new actions (confirm_order/no drink found so far)
    {'intent': 'utter_goodbye', 'inform_slots': {}, 'request_slots': {}}, #(done) # Triggers closing of conversation
    {'intent': 'joke', 'inform_slots': {}, 'request_slots': {}} #(done) # Triggers closing of conversation
]
    #{'intent': 'check_slot', 'inform_slots': {}, 'request_slots': {}}, # Checks size - maybe generates 2 new actions (right/wrong)
    #{'intent': 'utter_greet&take_order', 'inform_slots': {}, 'request_slots': {}},  # Triggers closing of conversation

# Rule-based policy request list
rule_requests = ['DRINK', 'SIZE', 'TEMP']

# These are possible inform slot keys that cannot be used to query
no_query_keys = [usersim_default_key]

#######################################
# Global config
#######################################

# These are used for both constraint check AND success check in usersim
FAIL = -1
NO_OUTCOME = 0
SUCCESS = 1

# All possible intents (for one-hot conversion in ST.get_state())
all_intents = ['utter_request', 'utter_inform', 'find_drink', 'utter_goodbye', 'order_drinks', 'inform', 'request',
               'reject', 'thanks', 'goodbye', 'nothing', 'trigger_user', 'joke', 'utter_nothing']

# All possible slots (for one-hot conversion in ST.get_state())
all_slots = ['SIZE', 'DRINK', 'TEMP', usersim_default_key] #'mc_list'

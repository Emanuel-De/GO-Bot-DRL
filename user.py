from dialogue_config import usersim_default_key, FAIL, NO_OUTCOME, SUCCESS, usersim_required_init_inform_keys, \
    no_query_keys
from user_mood_manuel import UserMood
from utils import reward_function
from utils import dict2sentence
import random, copy
import json


class User:
    """Simulates a real user, to train the agent with reinforcement learning."""

    def __init__(self, goal_list, constants, database):
        """
        The constructor for UserSimulator. Sets dialogue config variables.

        Parameters:
            goal_list (list): User goals loaded from file
            constants (dict): Dict of constants loaded from file
            database (dict): The database in the format dict(long: dict)
        """
        with open("data/sentences_dict.txt") as f:
            content = f.read()
        self.sentence_dict = json.loads(content.replace("'", '"').replace("\n", ''))
        self.max_round = constants['run']['max_round_num']
        self.reward_weight = constants['run']['reward_weight']
        self.default_key = usersim_default_key
        # A list of REQUIRED to be in the first action inform keys
        self.init_informs = usersim_required_init_inform_keys
        self.no_query = no_query_keys
        self.user_mood = UserMood()

        # TEMP ----
        self.database = database
        # ---------

    def reset(self):
        """
        Resets the user sim. by emptying the state and returning the initial action.

        Returns:
            dict: The initial action of an episode
        """

        self.count = 0
        self.user_mood.reset()
        # Add default slot to requests of goal

        self.state = {}
        # Any inform slots for the current user sim action, empty at start of turn
        self.state['inform_slots'] = {}
        # Current request slots the user sim wants to request
        self.state['request_slots'] = {}
        # Init. all informs and requests in user goal, remove slots as informs made by user or agent
        self.state['rest_slots'] = {}
        self.state['last_intent'] = ''
        self.state['intent'] = ''
        # False for failure, true for success, init. to failure
        self.success_check = FAIL

        return self._return_init_action()

    def _return_init_action(self):
        """
        Returns the initial action of the episode.

        The initial action has an intent of request, required init. inform slots and a single request slot.

        Returns:
            dict: Initial user response
        """
        while True:
            print('-----------------------------------------NEW EPISODE -----------------------------------------')
            input_emotion = input('How do you feel in general today? Type "-" = negative, "~" = neutral, "+" = positive:')
            if input_emotion == "-":
                self.user_mood.current_mood['emotion'] = "negativ"
                break
            elif input_emotion == "~":
                self.user_mood.current_mood['emotion'] = "neutral"
                break
            elif input_emotion == "+":
                self.user_mood.current_mood['emotion'] = "positiv"
                break


        while True:
            input_desire = input('How thursty are you? Type "very" or "little":')
            if input_desire == "very":
                self.user_mood.current_mood['goal_desire'] = "high"
                self._order_drinks()
                break
            elif input_desire == "little":
                self.user_mood.current_mood['goal_desire'] = "low"
                self._only_intent_utternace('nothing')
                break


        #["negativ", "neutral", "positiv"]
        user_response = {}
        user_response['intent'] = self.state['intent']
        user_response['request_slots'] = copy.deepcopy(self.state['request_slots'])
        user_response['inform_slots'] = copy.deepcopy(self.state['inform_slots'])

        print('Your Action: {}'.format(dict2sentence(user_response, self.sentence_dict)))

        return user_response

    def render(self, agent_action, user_response):
        pass
        # print('Agent Action: {}'.format(agent_action))
        #print('Agent Action: {}'.format(dict2sentence(agent_action, self.sentence_dict)))
        # print('***User Response: {} \n ---User mood:{}'.format(user_response, self.user_mood.current_mood['emotion']))
        #print('***User Response: {} \n ---User mood:{}'.format(dict2sentence(user_response, self.sentence_dict), self.user_mood.current_mood['emotion']))


    def step(self, agent_action):
        """
        Return the response of the user sim. to the agent by using rules that simulate a user.

        Given the agent action craft a response by using deterministic rules that simulate (to some extent) a user.
        Some parts of the rules are stochastic. Check if the agent has succeeded or lost or still going.

        Parameters:
            agent_action (dict): The agent action that the user sim. responds to

        Returns:
            dict: User sim. response
            int: Reward
            bool: Done flag
            int: Success: -1, 0 or 1 for loss, neither win nor loss, win
        """

        print('Agent Action: {}'.format(dict2sentence(agent_action, self.sentence_dict)))

        # Assertions -----
        # No UNK in agent action informs
        for value in agent_action['inform_slots'].values():
            assert value != 'UNK'
            assert value != 'PLACEHOLDER'
        # No PLACEHOLDER in agent at all
        for value in agent_action['request_slots'].values():
            assert value != 'PLACEHOLDER'
        # ----------------
        
        self.state['request_slots'].clear()
        self.state['inform_slots'].clear()
        self.state['last_intent'] = copy.deepcopy(self.state['intent'])
        self.state['intent'] = ''
        self.user_mood.last_mood['emotion'] = copy.deepcopy(self.user_mood.current_mood['emotion'])

        done = False
        success = NO_OUTCOME

        while True:
            input_emotion = input('How do you feel after the agent action? Type "-" = negative, "~" = neutral, "+" = positive:')
            if input_emotion == "-":
                self.user_mood.current_mood['emotion'] = "negativ"
                break
            elif input_emotion == "~":
                self.user_mood.current_mood['emotion'] = "neutral"
                break
            elif input_emotion == "+":
                self.user_mood.current_mood['emotion'] = "positiv"
                break

        # check round num, if equal to max then fail
        if agent_action['round'] == self.max_round:
            while True: 
                input_intent = input("Say 'goodbye':")
                if input_intent == 'goodbye':
                    done = True
                    success = self.success_check
                    self.state['intent'] = 'goodbye'
                    self.state['request_slots'].clear()
                    self.state['inform_slots'].clear()
                    break

        else:
            while True:
                input_intent = input('Type your intent: "order_drinks", "inform", "request", "reject", "thanks", "goodbye", "nothing":')
                if input_intent == "reject" or input_intent == "thanks" or input_intent == "goodbye" or input_intent == "nothing":
                    self._only_intent_utternace(input_intent)
                    if input_intent == "thanks":
                        self.success_check = SUCCESS
                    if input_intent == "goodbye":
                        done = True
                        success = self.success_check
                    break 

                if input_intent == "order_drinks":
                    self._order_drinks()
                    break
                
                elif input_intent == "inform":
                    self.inform(input_intent)
                    break
            
                elif input_intent == "request":
                    self.request(input_intent)
                    break

        # Assumptions -------
        # If request intent, then make sure request slots
        if self.state['intent'] == 'request':
            assert self.state['request_slots']
        # If inform intent, then make sure inform slots and NO request slots
        if self.state['intent'] == 'inform':
            assert self.state['inform_slots']
            assert not self.state['request_slots']
        assert 'UNK' not in self.state['inform_slots'].values()
        assert 'PLACEHOLDER' not in self.state['request_slots'].values()
        # -----------------------

        reward = reward_function(success, done, self)

        user_response = {}
        user_response['intent'] = self.state['intent']
        user_response['request_slots'] = copy.deepcopy(self.state['request_slots'])
        user_response['inform_slots'] = copy.deepcopy(self.state['inform_slots'])

        print('Your Action: {}'.format(dict2sentence(user_response, self.sentence_dict)))
        return user_response, reward, done, True if success is 1 else False

    def _order_drinks(self):
        self.inform('order_drinks')
        self.request('order_drinks')


    def request(self, input_intent):
        self.state['intent'] = input_intent
        while True:
            input_req = input('Choose what to request: "DRINK" "SIZE" "TEMP":')
            if input_req == "DRINK" or input_req == "SIZE" or input_req == "TEMP":
                if input_req == "DRINK":
                    self.state['request_slots']['DRINK'] = 'UNK'
                elif input_req == "SIZE":
                    self.state['request_slots']['SIZE'] = 'UNK'
                elif input_req == "TEMP":
                    self.state['request_slots']['TEMP'] = 'UNK'
                break

    def inform(self, input_intent):
        self.state['intent'] = input_intent
        while True:
            input_req = input('Choose what to inform: "DRINK" "SIZE" "TEMP":')
            if input_req == "DRINK" or input_req == "SIZE" or input_req == "TEMP":
                if input_req == "DRINK":
                    while True:
                        input_drink = input("What drink do you want: 'cola', 'water', 'sparkling water', 'medium water', 'still water', 'coffee', 'tea', 'coffeevodka', 'mojito', 'bahama mama', 'cuba libra', 'barracuda', 'green tea', 'red vine', 'white vine': ")
                        if input_drink == 'cola' or input_drink == 'water' or input_drink == 'sparkling water' or input_drink == 'medium water' or input_drink == 'still water' or input_drink == 'coffee' or input_drink == 'tea' or input_drink == 'coffeevodka' or input_drink == 'mojito' or input_drink == 'bahama mama' or input_drink == 'cuba libra' or input_drink == 'barracuda' or input_drink == 'green tea' or input_drink == 'red vine' or input_drink == 'white vine':
                            self.state['inform_slots']['DRINK'] = input_drink
                            break
                elif input_req == "SIZE":
                    while True:
                        input_size = input("What size do you want: 'small', 'medium', 'large', 'Jumbo':")
                        if input_size == 'small' or input_size == 'medium' or input_size == 'large' or input_size == 'Jumbo':
                            self.state['inform_slots']['SIZE'] = input_size
                            break
                elif input_req == "TEMP":
                    while True:
                        input_temp = input("What temp do you want: 'cold', 'hot': ")
                        if input_temp == 'cold' or input_temp == 'hot':
                            self.state['inform_slots']['TEMP'] = input_temp
                            break
                break


    def _only_intent_utternace(self, input_intent):
        self.state['intent'] = input_intent
        self.state['inform_slots'].clear()
        self.state['request_slots'].clear()

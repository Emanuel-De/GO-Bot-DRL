from dialogue_config import usersim_default_key, FAIL, NO_OUTCOME, SUCCESS, usersim_required_init_inform_keys, \
    no_query_keys
from user_mood import UserMood
from utils import reward_function
from utils import dict2sentence
import random, copy
import json


class UserSimulator:
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
        self.goal_list = goal_list
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

        self.goal = random.choice(self.goal_list)
        self.count = 0
        self.user_mood.reset()
        # Add default slot to requests of goal
        self.goal['request_slots'][self.default_key] = 'UNK'
        self.state = {}
        # Add all inform slots informed by agent or user sim to this dict
        self.state['history_slots'] = {}
        # Any inform slots for the current user sim action, empty at start of turn
        self.state['inform_slots'] = {}
        # Current request slots the user sim wants to request
        self.state['request_slots'] = {}
        # Init. all informs and requests in user goal, remove slots as informs made by user or agent
        self.state['rest_slots'] = {}
        self.state['rest_slots'].update(self.goal['inform_slots'])
        self.state['rest_slots'].update(self.goal['request_slots'])
        self.state['last_intent'] = ''
        self.state['intent'] = ''
        # False for failure, true for success, init. to failure
        self.constraint_check = FAIL

        return self._return_init_action()
 
    def _return_init_action(self):
        """
        Returns the initial action of the episode.

        The initial action has an intent of request, required init. inform slots and a single request slot.

        Returns:
            dict: Initial user response
        """

        # Always order drinks
        
        # Pick random action from 'order_drinks', 'None'
        #sample = random.randint(0, 1)

        #if sample == 1:

        if self.user_mood.current_mood['goal_desire'] == "low":
            #1st case: Do nothing
            self._say_nothing()
        
        #elif sample == 0:
        else: 
            #2nd case: order_drinks
            self._order_drinks()
        
        user_response = {}
        user_response['intent'] = self.state['intent']
        user_response['request_slots'] = copy.deepcopy(self.state['request_slots'])
        user_response['inform_slots'] = copy.deepcopy(self.state['inform_slots'])

        return user_response

    def render(self, agent_action, user_response):
        # print('Agent Action: {}'.format(agent_action))
        print('Agent Action: {}'.format(dict2sentence(agent_action, self.sentence_dict)))
        # print('***User Response: {} \n ---User mood:{}'.format(user_response, self.user_mood.current_mood['emotion']))
        print('***User Response: {} \n ---User mood:{}'.format(dict2sentence(user_response, self.sentence_dict), self.user_mood.current_mood['emotion']))

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

        # Assertions -----
        # No UNK in agent action informs
        for value in agent_action['inform_slots'].values():
            assert value != 'UNK'
            assert value != 'PLACEHOLDER'
        # No PLACEHOLDER in agent at all
        for value in agent_action['request_slots'].values():
            assert value != 'PLACEHOLDER'
        # ----------------

        self.state['inform_slots'].clear()
        self.state['last_intent'] = self.state['intent']
        self.state['intent'] = ''

        done = False
        success = NO_OUTCOME
        
        agent_intent = agent_action['intent']
        if agent_intent == 'utter_nothing':
            classified_agent_action = self._response_to_utter_nothing(agent_action)
        if agent_intent == 'joke':
            classified_agent_action = self._response_to_joke(agent_action)
        elif agent_intent == 'trigger_user':
            classified_agent_action = self._response_to_trigger_user(agent_action)
        elif agent_intent == 'utter_request':
            classified_agent_action = self._response_to_utter_request(agent_action)
        elif agent_intent == 'utter_inform':
            classified_agent_action = self._response_to_utter_inform(agent_action)
        elif agent_intent == 'find_drink':
            classified_agent_action = self._response_to_find_drink(agent_action)
        elif agent_intent == 'utter_goodbye':
            success = self._check_success()
            classified_agent_action = 'utter_goodbye'
            self.state['intent'] = 'goodbye'
            self.state['request_slots'].clear()
            done = True

        # check round num, if equal to max then fail
        if agent_action['round'] == self.max_round:
            done = True
            success = self._check_success()
            self.state['intent'] = 'goodbye'
            self.state['request_slots'].clear()
            self.state['inform_slots'].clear()

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
        # No overlap between rest and hist
        for key in self.state['rest_slots']:
            assert key not in self.state['history_slots']
        for key in self.state['history_slots']:
            assert key not in self.state['rest_slots']
        # All slots in both rest and hist should contain the slots for goal
        for inf_key in self.goal['inform_slots']:
            assert self.state['history_slots'].get(inf_key, False) or self.state['rest_slots'].get(inf_key, False)
        for req_key in self.goal['request_slots']:
            assert self.state['history_slots'].get(req_key, False) or self.state['rest_slots'].get(req_key,
                                                                                                   False), req_key
        # Anything in the rest should be in the goal
        for key in self.state['rest_slots']:
            assert self.goal['inform_slots'].get(key, False) or self.goal['request_slots'].get(key, False)
        assert self.state['intent'] != ''
        # -----------------------

        user_response = {}
        user_response['intent'] = self.state['intent']
        user_response['request_slots'] = copy.deepcopy(self.state['request_slots'])
        user_response['inform_slots'] = copy.deepcopy(self.state['inform_slots'])

        # int_reward = self.user_mood.mood_reward(self.state['last_intent'], classified_agent_action)
        # ext_reward = reward_function(success, self.max_round)

        # reward = int_reward + self.reward_weight * ext_reward
        # reward = ext_reward

        reward = reward_function(success, done, self, classified_agent_action, agent_action)
        if self.user_mood.current_mood['emotion'] == "negativ":
            self.count += 1

            if self.count == 5:
                done = True
                #success = FAIL
                reward -= self.max_round
                user_response = {}
                user_response['intent'] = 'goodbye'
                user_response['request_slots'] = {}
                user_response['inform_slots'] = {}
        
        #outcome = success
        #return user_response, classified_agent_action, done, outcome, True if success == 1 else False
        return user_response, reward, done, True if success is 1 else False

    def _response_to_joke(self, agent_action):

        if self.user_mood.current_mood['goal_desire'] == "low":
            
            sample = random.randint(0, 20)
            if sample==0:
                #2nd case: Inform or request randomly
                self._choose_random_action()

            else:
                #1st case: Do nothing
                self._say_nothing()


        elif self.user_mood.current_mood['goal_desire'] == "high":
            
            if not self.state['history_slots']: 
                self._order_drinks()
            
            else:
                self._choose_random_action()

        return agent_action['intent']
        
    
    def _response_to_utter_nothing(self, agent_action):

        if self.user_mood.current_mood['goal_desire'] == "low":
            
            sample = random.randint(0, 10)
            if sample==0:
                #2nd case: Inform or request randomly
                self._choose_random_action()

            else:
                #1st case: Do nothing
                self._say_nothing()


        elif self.user_mood.current_mood['goal_desire'] == "high":
            
            if not self.state['history_slots']: 
                self._order_drinks()
            
            else:
                self._choose_random_action()

        return agent_action['intent']
    
    def _response_to_trigger_user(self, agent_action):
        """
        Same as request
        """
        classified_agent_action = self._response_to_utter_request(agent_action)

        return classified_agent_action
        
    
    
    def _response_to_utter_request(self, agent_action):
        """
        Augments the state in response to the agent action having an intent of request.

        There are 4 main cases for responding.

        Parameters:
            agent_action (dict): Intent of request with standard action format (including 'speaker': 'Agent' and
                                 'round_num': int)
        """

        agent_request_key = list(agent_action['request_slots'].keys())[0]
        # First Case: if agent requests for something that is in the user sims goal inform slots, then inform it
        if agent_request_key in self.goal['inform_slots']:
            self.state['intent'] = 'inform'
            self.state['inform_slots'][agent_request_key] = self.goal['inform_slots'][agent_request_key]
            self.state['request_slots'].clear()
            self.state['rest_slots'].pop(agent_request_key, None)
            self.state['history_slots'][agent_request_key] = self.goal['inform_slots'][agent_request_key]
        # Second Case: if the agent requests for something in user sims goal request slots and it has already been
        # informed, then inform it
        elif agent_request_key in self.goal['request_slots'] and agent_request_key in self.state['history_slots']:
            self.state['intent'] = 'inform'
            self.state['inform_slots'][agent_request_key] = self.state['history_slots'][agent_request_key]
            self.state['request_slots'].clear()
            assert agent_request_key not in self.state['rest_slots']

            #If the user has a high goal_desire: Add a random inform
            if self.user_mood.current_mood['goal_desire'] == "high":
                rest_informs = {}
                for key, value in list(self.state['rest_slots'].items()):
                    if value != 'UNK':
                        rest_informs[key] = value
                if rest_informs:
                    key_choice, value_choice = random.choice(list(rest_informs.items()))
                    self.state['inform_slots'][key_choice] = value_choice
                    self.state['rest_slots'].pop(key_choice)
                    self.state['history_slots'][key_choice] = value_choice
        
        # Third Case: if the agent requests for something in the user sims goal request slots and it HASN'T been
        # informed, request it 
        elif agent_request_key in self.goal['request_slots'] and agent_request_key in self.state['rest_slots']:
            self.state['request_slots'].clear()
            self.state['intent'] = 'request'
            self.state['request_slots'][agent_request_key] = 'UNK'

            #If the user has a high goal_desire: Add a random inform
            if self.user_mood.current_mood['goal_desire'] == "high":
                rest_informs = {}
                for key, value in list(self.state['rest_slots'].items()):
                    if value != 'UNK':
                        rest_informs[key] = value
                if rest_informs:
                    key_choice, value_choice = random.choice(list(rest_informs.items()))
                    self.state['inform_slots'][key_choice] = value_choice
                    self.state['rest_slots'].pop(key_choice)
                    self.state['history_slots'][key_choice] = value_choice

        # Fourth and Final Case: otherwise the user sim does not care about the slot being requested, then choose any action
        else:
            self._choose_random_action()
        
        return agent_action['intent']


    def _response_to_utter_inform(self, agent_action):
        """
        Augments the state in response to the agent action having an intent of inform.

        There are 2 main cases for responding. Add the agent inform slots to history slots,
        and remove the agent inform slots from the rest and request slots.

        Parameters:
            agent_action (dict): Intent of inform with standard action format (including 'speaker': 'Agent' and
                                 'round_num': int)
        """

        agent_inform_key = list(agent_action['inform_slots'].keys())[0]
        agent_inform_value = agent_action['inform_slots'][agent_inform_key]

        # Remove from rest slots if in it
        self.state['rest_slots'].pop(agent_inform_key, None)
        # Remove from request slots if in it
        self.state['request_slots'].pop(agent_inform_key, None)

        assert agent_inform_key != self.default_key

        # First Case: If agent informs something that is in goal informs and the value it informed doesnt match,
        # then inform the correct value
        if agent_inform_value != self.goal['inform_slots'].get(agent_inform_key, agent_inform_value):
            classified_agent_action = 'inform_wrong'
            self.state['intent'] = 'inform'
            self.state['inform_slots'][agent_inform_key] = self.goal['inform_slots'][agent_inform_key]
            self.state['request_slots'].clear()
            self.state['history_slots'][agent_inform_key] = self.goal['inform_slots'][agent_inform_key]
        # Second Case: If agent informs something that is in goal informs and the value it informs has already been informed,
        # then either say_nothing, or inform something new.
        elif agent_inform_key in self.state['history_slots'] and agent_inform_value == self.state['history_slots'][agent_inform_key]:
            classified_agent_action = 'inform_wrong'
            #If the user has a low goal_desire: Say nothing
            if self.user_mood.current_mood['goal_desire'] == "low":
                self._say_nothing()

            #If the user has a high goal_desire: Add a random inform
            if self.user_mood.current_mood['goal_desire'] == "high":
                self._choose_random_action()
        
        # Third Case: Otherwise pick a random action to take
        else:
            # Add all informs (by agent too) to hist slots
            self.state['history_slots'][agent_inform_key] = agent_inform_value
            
            classified_agent_action = 'inform_right'
            self._choose_random_action()

        return classified_agent_action
    
    
    def _response_to_find_drink(self, agent_action):
        """
        Augments the state in response to the agent action having an intent of find_drink.

        Check if there is a match in the agent action that works with the current goal.

        Parameters:
            agent_action (dict): Intent of find_drink with standard action format (including 'speaker': 'Agent' and
                                 'round_num': int)
        """
        
        agent_informs = agent_action['inform_slots']
        assert self.default_key in agent_informs

        self.state['intent'] = 'thanks'
        self.constraint_check = SUCCESS
        classified_agent_action = 'find_drink_right'

        #The agent has not found a match
        if agent_informs[self.default_key] == 'no match available':
            classified_agent_action = 'find_drink_wrong'
            self.constraint_check = FAIL

            #If the user is really thursty he chooses a random action
            if self.user_mood.current_mood['goal_desire'] == "high":
                self._choose_random_action()

            #If the user is not thursty he doesn't care and says nothing
            elif self.user_mood.current_mood['goal_desire'] == "low":
                self._say_nothing()

        else:
            # Check to see if all goal informs are in the agent informs, and that the values match
            for key, value in self.goal['inform_slots'].items():
                assert value != None
                # For items that cannot be in the queries don't check to see if they are in the agent informs here
                if key in self.no_query:
                    continue
                # Will return true if key not in agent informs OR if value does not match value of agent informs[key]
                if value != agent_informs.get(key, None):
                    classified_agent_action = 'find_drink_wrong'
                    self.state['intent'] = 'reject'
                    self.state['request_slots'].clear() #pop(self.default_key, None)
                    #If the user is really thursty he chooses a random action
                    #if self.user_mood.current_mood['goal_desire'] == "high":
                     #   self.state['inform_slots'][key] = value
                    
                    self.constraint_check = FAIL
                    break
            
        if self.constraint_check == SUCCESS:
            for key, value in agent_informs.items():
                self.state['rest_slots'].pop(key, None)
                self.state['history_slots'][key] = value
            self.state['request_slots'].clear() #pop(self.default_key, None)

        return classified_agent_action

    def _check_success(self):
        """
        Augments the state in response to the agent action having an intent of utter_goodbye.

        If the constraint_check is SUCCESS and both the rest and request slots of the state are empty for the agent
        to succeed in this episode/conversation.

        Returns:
            int: Success: -1, 0 or 1 for loss, neither win nor loss, win
        """     

        if self.constraint_check == FAIL:
            return FAIL

        if not self.state['rest_slots']:
            assert not self.state['request_slots']
        if self.state['rest_slots']:
            return FAIL

        # TEMP: ----
        assert self.state['history_slots'][self.default_key] != 'no match available'

        match = copy.deepcopy(self.database[int(self.state['history_slots'][self.default_key])])

        for key, value in self.goal['inform_slots'].items():
            assert value != None
            if key in self.no_query:
                continue
            if value != match.get(key, None):
                assert True is False, 'match: {}\ngoal: {}'.format(match, self.goal)
                break
        # ----------

        return SUCCESS


    def _order_drinks(self):
        #2nd case: order_drinks
            self.state['intent'] = 'order_drinks'

            if self.goal['inform_slots']:
                # Pick all the required init. informs, and add if they exist in goal inform slots
                for inform_key in self.init_informs:
                    if inform_key in self.goal['inform_slots']:
                        self.state['inform_slots'][inform_key] = self.goal['inform_slots'][inform_key]
                        self.state['rest_slots'].pop(inform_key)
                        self.state['history_slots'][inform_key] = self.goal['inform_slots'][inform_key]
                
                # If nothing was added then add every inform_slot randomly (not in initial inform slots)
                if not self.state['inform_slots']:
                    
                    for key, value in list(self.goal['inform_slots'].items()):
                        # sample  0 or 1 
                        sample = random.randint(0, 1)
                        if sample == 1:
                            self.state['inform_slots'][key] = value
                            self.state['rest_slots'].pop(key)
                            self.state['history_slots'][key] = value


            # Now add a request, do a random one if something other than def. available
            self.goal['request_slots'].pop(self.default_key)
            if self.goal['request_slots']:
                req_key = random.choice(list(self.goal['request_slots'].keys()))
                self.state['request_slots'][req_key] = 'UNK'
            
            self.goal['request_slots'][self.default_key] = 'UNK'


    def _choose_random_action(self):
        # - If anything in state requests then request it
        if self.state['request_slots']:
            self.state['intent'] = 'request'
        # - Else if something to say in rest slots, pick something
        elif self.state['rest_slots']:
            def_in = self.state['rest_slots'].pop(self.default_key, False)
            #If some slots except the drinknumber left, request or inform one of them
            if self.state['rest_slots']:
                key, value = random.choice(list(self.state['rest_slots'].items()))
                if value != 'UNK':
                    self.state['intent'] = 'inform'
                    self.state['inform_slots'][key] = value
                    self.state['rest_slots'].pop(key)
                    self.state['history_slots'][key] = value
                else:
                    self.state['intent'] = 'request'
                    self.state['request_slots'][key] = 'UNK'

            #If only drinknumber left
            else:
                #If the user is really thursty 
                if self.user_mood.current_mood['goal_desire'] == "high":
                    
                    #If the user has not requestet something before request drinknumber
                    if self.state['last_intent'] != 'request':
                        self.state['intent'] = 'request'
                        self.state['request_slots'][self.default_key] = 'UNK'
                    
                    #If the user has requestet something before he informs something from history slots
                    else:
                        key, value = random.choice(list(self.state['history_slots'].items()))
                        self.state['intent'] = 'inform'
                        self.state['inform_slots'][key] = value

                #If the user is not thursty he doesn't care and says nothing
                elif self.user_mood.current_mood['goal_desire'] == "low":
                    self._say_nothing()
            
            if def_in == 'UNK':
                self.state['rest_slots'][self.default_key] = 'UNK'
        # Otherwise respond with 'nothing to say' intent
        else:
            self._say_nothing()

    def _say_nothing(self):
        self.state['intent'] = 'nothing'
        self.state['inform_slots'].clear()
        self.state['request_slots'].clear()


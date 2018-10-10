from keras.models import Sequential
from keras.layers import Dense
from keras.optimizers import Adam, RMSprop
from keras.regularizers import l2
import random, copy
import numpy as np
from dialogue_config import rule_requests, agent_actions


from qlearning import DQN


# Some of code based off of https://jaromiru.com/2016/09/27/lets-make-a-dqn-theory/

# Note: They do not anneal epsilon
class DQNAgent:
    def __init__(self, state_size, constants):
        self.C = constants['agent']
        self.memory = []
        self.memory_index = 0
        self.max_memory_size = self.C['max_mem_size']
        self.eps = self.C['epsilon_init']  # Note they do not anneal eps, and default is 0, so i should test this out
        self.vanilla = self.C['vanilla']
        self.lr = self.C['learning_rate']
        self.gamma = self.C['gamma']
        self.batch_size = self.C['batch_size']
        self.hidden_size = self.C['dqn_hidden_size']
        self.decay_rate = self.C['decay_rate']
        self.smooth_epsilon = self.C['smooth_eps']
        self.l1_reg_constant = self.C['l1_reg_constant']
        self.grad_clip_constant = self.C['grad_clip_constant']

        self.state_size = state_size
        self.possible_actions = agent_actions
        self.num_actions = len(self.possible_actions)  # 40

        self.beh_model = self._build_model()
        self.tar_model = self._build_model()

        self.reset()

        self.dqn = DQN(self.state_size, self.hidden_size, self.num_actions)
        self.clone_dqn = copy.deepcopy(self.dqn)

        self.cur_bellman_err = 0

    def _build_model(self):
        model = Sequential()
        model.add(Dense(self.hidden_size, input_dim=self.state_size, activation='relu', kernel_regularizer=l2(self.l1_reg_constant)))
        model.add(Dense(self.num_actions, activation='linear', kernel_regularizer=l2(self.l1_reg_constant)))
        model.compile(loss='mse', optimizer=RMSprop(lr=self.lr, decay=self.decay_rate, epsilon=self.smooth_epsilon, clipvalue=self.grad_clip_constant))
        # model.compile(loss='mse', optimizer=Adam(lr=self.lr))
        return model

    def reset(self):
        self.rule_current_slot_index = 0
        self.rule_phase = 'not done'
        self.rule_request_set = rule_requests

    def get_action(self, state, use_rule=False):
        if self.eps > random.random():
            index = random.randint(0, self.num_actions - 1)
            action = self._map_index_to_action(index)
            return index, action
        else:
            if use_rule:
                return self._rule_action()
            else:
                return self._dqn_action(state)

    def _rule_action(self):
        if self.rule_current_slot_index < len(self.rule_request_set):
            slot = self.rule_request_set[self.rule_current_slot_index]
            self.rule_current_slot_index += 1
            rule_response = {'intent': 'request', 'inform_slots': {}, 'request_slots': {slot: 'UNK'}}
        elif self.rule_phase == 'not done':
            rule_response = {'intent': 'match_found', 'inform_slots': {}, 'request_slots': {}}
            self.rule_phase = 'done'
        elif self.rule_phase == 'done':
            rule_response = {'intent': 'done', 'inform_slots': {}, 'request_slots': {}}
        else:
            assert True is False

        index = self._map_action_to_index(rule_response)
        return index, rule_response

    def _map_action_to_index(self, response):
        for (i, action) in enumerate(self.possible_actions):
            if response == action:
                return i

    def _dqn_action(self, state):
        index = self.dqn.predict(state, {}, predict_model=True)
        action = self._map_index_to_action(index)
        return index, action

    # Map index to action
    def _map_index_to_action(self, index):
        for (i, action) in enumerate(self.possible_actions):
            if index == i:
                return copy.deepcopy(action)

    def _dqn_predict_one(self, state, target=False):
        return self._dqn_predict(state.reshape(1, self.state_size), target=target).flatten()

    def _dqn_predict(self, states, target=False):
        if target:
            return self.tar_model.predict(states)
        else:
            return self.beh_model.predict(states)

    def add_experience(self, state, action, reward, next_state, done):
        if len(self.memory) < self.max_memory_size:
            self.memory.append(None)
        self.memory[self.memory_index] = (state, action, reward, next_state, done)
        self.memory_index = (self.memory_index + 1) % self.max_memory_size

    def empty_memory(self):
        self.memory = []
        self.memory_index = 0

    def is_memory_full(self):
        return len(self.memory) == self.max_memory_size

    # States, actions, rewards, next_states, done
    # def train(self):
    #     for i in range(self.num_batches):
    #         batch = self._sample_memory(self.batch_size)
    #         batch_size = len(batch)
    #
    #         states = np.array([sample[0] for sample in batch])
    #         next_states = np.array([sample[3] for sample in batch])
    #
    #         assert states.shape == (batch_size, self.state_size), 'States Shape: {}'.format(states.shape)
    #         assert next_states.shape == states.shape
    #
    #         beh_state_preds = self._dqn_predict(states)  # For leveling error
    #         if not self.vanilla:
    #             beh_next_states_preds = self._dqn_predict(next_states)  # For indexing for DDQN
    #         tar_next_state_preds = self._dqn_predict(next_states, target=True)  # For target value for DQN (& DDQN)
    #
    #         inputs = np.zeros((batch_size, self.state_size))
    #         targets = np.zeros((batch_size, self.num_actions))
    #
    #         for i, (s, a, r, s_, d) in enumerate(batch):
    #             t = beh_state_preds[i]
    #
    #             # NOTE: I havent check that this line works as a DDQN should but i assume it does...
    #             if not self.vanilla:
    #                 t[a] = r + self.gamma * tar_next_state_preds[i][np.argmax(beh_next_states_preds[i])] * (not d)
    #             else:
    #                 t[a] = r + self.gamma * np.amax(tar_next_state_preds[i]) * (not d)
    #             inputs[i] = s
    #             targets[i] = t
    #
    #         self.beh_model.train_on_batch(inputs, targets)

    def train(self, batch_size=16, num_batches=1):
        """ Train DQN with experience replay """

        for iter_batch in range(num_batches):
            self.cur_bellman_err = 0
            for iter in range(int(len(self.memory) / (batch_size))):
                batch = [random.choice(self.memory) for i in range(batch_size)]
                batch_struct = self.dqn.singleBatch(batch, {'gamma': self.gamma}, self.clone_dqn)
                self.cur_bellman_err += batch_struct['cost']['total_cost']

            print("cur bellman err %.4f, experience replay pool %s" % (
            float(self.cur_bellman_err) / len(self.memory), len(self.memory)))

    def _sample_memory(self, num):
        new_num = min(num, len(self.memory))
        return random.sample(self.memory, new_num)

    def copy(self):
        # self.tar_model.set_weights(self.beh_model.get_weights())
        self.clone_dqn = copy.deepcopy(self.dqn)
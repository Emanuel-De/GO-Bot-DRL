from keras import layers
from keras.models import Sequential
from keras.layers import Dense
from keras.optimizers import Adam
import numpy as np
from keras import Model, Input
from keras.losses import CategoricalCrossentropy

class ICM:
    """The Intrinisc Curiosity Module for curious exploration of the action space."""

    def __init__(self, state_size, constants):

        self.state_size = state_size
        self.feature_size = constants['feature_size']
        self.hidden_size = constants['dqn_hidden_size']
        self.action_size = constants['action_size']
        self.lr = constants['learning_rate']
        self.beta = constants['loss_beta']
        self.lamda = constants['reward_lamda']
        self.action_net, self.state_enc_net, self.features_net = self._build_model()
        
    def _build_model(self):
        # Defines the input for the model: s(t), s(t+1), a(t)
        state1_input = Input(self.state_size)
        state2_input = Input(self.state_size)
        action_input = Input(self.action_size)
        encoded_input = Input(self.feature_size)

        # Build the feature encoding network
        features = Sequential()
        features.add(Dense(self.hidden_size, input_dim=self.state_size, activation='relu'))
        features.add(Dense(self.hidden_size, activation='relu'))
        features.add(Dense(self.feature_size, activation='linear'))

        # Get the incodings with shared weights
        encodings_s1 = features(state1_input)
        encodings_s2 = features(state2_input)
        state_encodings = layers.Concatenate(axis=-1)([encodings_s1, encodings_s2])

        # Build the inverse model
        inverse = Sequential()
        inverse.add(Dense(self.hidden_size, input_dim=self.feature_size * 2, activation='relu'))
        inverse.add(Dense(self.hidden_size, activation='relu'))

        # Transmit the state encodings to get an action prediction
        action_prediction = Dense(self.action_size, activation='softmax')(inverse(state_encodings))  # maybe softmax? 
        action_network = Model(inputs=[state1_input, state2_input], outputs=action_prediction)
        action_network.compile(loss=[CategoricalCrossentropy()], optimizer=Adam(lr=self.lr), loss_weights=[1 - self.beta])
        print(action_network.summary())

        # Build the forward model
        forward = Sequential()
        forward.add(Dense(self.hidden_size, input_dim=self.feature_size + self.action_size, activation='relu'))
        forward.add(Dense(self.hidden_size, activation='relu'))

        # transmit the concatenated feature encodings of s(t) with the action to get a state prediction
        forward_input = layers.Concatenate(axis=-1)([action_input, encoded_input])
        state_prediction = Dense(self.feature_size)(forward(forward_input))
        state_enc_network = Model(inputs=[action_input, encoded_input], outputs=state_prediction)
        state_enc_network.compile(loss=['mse'], optimizer=Adam(lr=self.lr), loss_weights=[self.beta])
        print(state_enc_network.summary())
        return action_network, state_enc_network, features

    def predict_action(self, state, next_state):

        state = state.reshape(-1, self.state_size)
        next_state = next_state.reshape(-1, self.state_size)
        return self.action_net.predict([state, next_state])

    def predict_state_enc(self, state, action):
        state = state.reshape(-1, self.state_size)
        return self.state_enc_net.predict([self.onehot(action), self.features_net(state)])

    def curiosity_reward(self, state, action, next_state):
        predicted_enc = self.predict_state_enc(state, action)
        encodings = self.features_net(next_state.reshape(1, self.state_size))
        diff = predicted_enc - encodings
        curiosity_reward = np.inner(diff, diff)
        return curiosity_reward * self.lamda

    def train(self, states, actions, next_states):
        # pred_actions = self.predict_action(states, next_states)
        states = states.reshape(-1, self.state_size)
        next_states = next_states.reshape(-1, self.state_size)
        actions = self.onehot(actions)
        self.action_net.fit(x=[states, next_states], y=actions, epochs=2, verbose=0)
        self.state_enc_net.fit(x=[actions, self.features_net(states)], y=self.features_net(next_states), epochs=2, verbose=0)

    def onehot(self, action):
        action = np.asarray(action)
        action_input = np.zeros((action.size, self.action_size))
        action_input[np.arange(action.size), action] = 1
        return action_input

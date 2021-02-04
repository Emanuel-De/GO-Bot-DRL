from user_simulator import UserSimulator
from error_model_controller import ErrorModelController
from dqn_agent import DQNAgent
from state_tracker import StateTracker
import pickle, argparse, json, math
from utils import remove_empty_slots, generate_agent_action_list, efficiency_metric
from user import User
import tensorflow as tf
import datetime

#import time
#from utils import reward_function

#import os
#os.environ["CUDA_VISIBLE_DEVICES"] = "-1"


if __name__ == "__main__":
    # Can provide constants file path in args OR run it as is and change 'CONSTANTS_FILE_PATH' below
    # 1) In terminal: python train.py --constants_path "constants.json"
    # 2) Run this file as is
    parser = argparse.ArgumentParser()
    parser.add_argument('--constants_path', dest='constants_path', type=str, default='')
    args = parser.parse_args()
    params = vars(args)

    # Load constants json into dict
    CONSTANTS_FILE_PATH = 'constants_training.json'
    if len(params['constants_path']) > 0:
        constants_file = params['constants_path']
    else:
        constants_file = CONSTANTS_FILE_PATH

    with open(constants_file) as f:
        constants = json.load(f)

    # Load file path constants
    file_path_dict = constants['db_file_paths']
    DATABASE_FILE_PATH = file_path_dict['database']
    DICT_FILE_PATH = file_path_dict['dict']
    USER_GOALS_FILE_PATH = file_path_dict['user_goals']

    # Load run constants
    run_dict = constants['run']
    USE_USERSIM = run_dict['usersim']
    RENDER = run_dict['render']
    WARMUP_MEM = run_dict['warmup_mem']
    NUM_EP_TRAIN = run_dict['num_ep_run']
    TRAIN_FREQ = run_dict['train_freq']
    MAX_ROUND_NUM = run_dict['max_round_num']
    SUCCESS_RATE_THRESHOLD = run_dict['success_rate_threshold']

    # Load movie DB
    # Note: If you get an unpickling error here then run 'pickle_converter.py' and it should fix it
    database = pickle.load(open(DATABASE_FILE_PATH, 'rb'), encoding='latin1')

    # Clean DB
    remove_empty_slots(database)

    # Load movie dict
    db_dict = pickle.load(open(DICT_FILE_PATH, 'rb'), encoding='latin1')

    # Load goal File
    user_goals = pickle.load(open(USER_GOALS_FILE_PATH, 'rb'), encoding='latin1')



    # Init. Objects
    if USE_USERSIM: # TODO Change this to false in constans_train.json
        user = UserSimulator(user_goals, constants, database)
    else:
        user = User(user_goals, constants, database)
    emc = ErrorModelController(db_dict, constants)
    state_tracker = StateTracker(database, constants)
    dqn_agent = DQNAgent(state_tracker.get_state_size(), constants)

    # prepare TensorBoard output
    output_dir = "logs/" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    writer = tf.summary.create_file_writer(output_dir)
    writer.set_as_default()

def run_round(state, warmup=False):
    # 1) Agent takes action given state tracker's representation of dialogue (state)
    agent_action_index, agent_action = dqn_agent.get_action(state, use_rule=warmup)
    # 2) Update state tracker with the agent's action
    state_tracker.update_state_agent(agent_action)
    # 3) User takes action given agent action
    # user_action, classified_action, done, outcome, success = user.step(agent_action)
    # reward = reward_function(outcome, done, user, classified_action, constants['run']['reward_weight'], agent_action)
    user_action, reward, done, success = user.step(agent_action)
    
    if not done:
        # 4) Infuse error into semantic frame level of user action
        if USE_USERSIM:
            emc.infuse_error(user_action)
    # 5) Print the conversation if RENDER==TRUE
    if RENDER:
        user.render(agent_action, user_action)
    # 6) Update state tracker with user action
    state_tracker.update_state_user(user_action)
    # 7) Get next state and add experience
    next_state = state_tracker.get_state(done)

    intrinsic_reward = dqn_agent.icm.curiosity_reward(state, agent_action_index, next_state)[0,0]
    reward = (1 - dqn_agent.C['extrins_reward_share']) * intrinsic_reward + dqn_agent.C['extrins_reward_share'] * reward
    dqn_agent.add_experience(state, agent_action_index, reward, next_state, done)

    return next_state, reward, done, success, intrinsic_reward


def warmup_run():
    """
    Runs the warmup stage of training which is used to fill the agents memory.

    The agent uses it's rule-based policy to make actions. The agent's memory is filled as this runs.
    Loop terminates when the size of the memory is equal to WARMUP_MEM or when the memory buffer is full.

    """

    print('Warmup Started...')
    total_step = 0
    episode = 0
    while total_step <= WARMUP_MEM and not dqn_agent.is_memory_full():
        # Reset episode
        user_action = episode_reset()
        episode += 1
        
        # Print the conversation if RENDER==TRUE
        if RENDER:
            print('\n**********Episode {} ********************'.format(episode))
            print('User Goal: {}'.format(user.goal))
            print(user.user_mood.current_mood)
            print('-----------------------------------------------------------------------------------------------------------')
            print('Initial User Utterance: {}'.format(user_action)) 
        done = False
        # Get initial state from state tracker
        state = state_tracker.get_state()
        while not done:
            next_state, _, done, _ , _= run_round(state, warmup=True)
            total_step += 1
            state = next_state

    print('...Warmup Ended')


def train_run():
    """
    Runs the loop that trains the agent.

    Trains the agent on the goal-oriented chatbot task. Training of the agent's neural network occurs every episode that
    TRAIN_FREQ is a multiple of. Terminates when the episode reaches NUM_EP_TRAIN.

    """

    print('Training Started...')
    episode = 0
    period_reward_total = 0
    period_ireward_total = 0
    period_success_total = 0
    period_mood_success_total = 0
    success_rate_best = 0.0
    episode_efficiency_total = 0.0

    # best_avg_reward = 0.0
    period_step = 0
    period_mood_total = 0
    quality_metric = 0.0
    best_quality_metric = 0.0
    # Initialize tensorflow summary
    tf.summary.experimental.set_step(episode)

    while episode < NUM_EP_TRAIN:
        user_action = episode_reset()
        episode += 1

        # Update Tensorflow
        tf.summary.experimental.set_step(episode)
        # Print the conversation if RENDER==TRUE
        if RENDER:
            print('\n********** Episode {} ********************'.format(episode))
            print('User Goal: {}'.format(user.goal))
            print(user.user_mood.current_mood)
            print('-----------------------------------------------------------------------------------------------------------')
            print('Initial User Utterance: {}'.format(user_action)) 
        done = False
        state = state_tracker.get_state()
        while not done:
            next_state, reward, done, success, intrinsisc_r = run_round(state)
            period_reward_total += reward
            period_ireward_total += intrinsisc_r
            state = next_state
            period_step += 1
            period_mood_total += user.user_mood.emotions.index(user.user_mood.current_mood['emotion']) / 2
            
        period_success_total += success
        episode_efficiency_total += efficiency_metric(state_tracker.history, user.user_mood.current_mood['goal_desire'] )
        if user.user_mood.current_mood['emotion']=="positiv":
            period_mood_success_total += 1  

        # Train
        if episode % TRAIN_FREQ == 0:
            # Check success rate
            success_rate = period_success_total / TRAIN_FREQ
            mood_success_rate = period_mood_success_total / TRAIN_FREQ
            avg_reward = period_reward_total / TRAIN_FREQ
            avg_ireward = period_ireward_total / TRAIN_FREQ
            avg_mood = period_mood_total / (period_step)
            quality_metric = avg_mood * avg_reward * success_rate
            avg_efficiancy = episode_efficiency_total / TRAIN_FREQ

            # Flush
            # if success_rate >= success_rate_best and success_rate >= SUCCESS_RATE_THRESHOLD:
            if episode == 120:
                dqn_agent.empty_memory()
            # Update current best success rate
            print('Episode: {} SUCCESS RATE: {} MOOD SUCCESS RATE: {} Avg Reward: {} QUALITY METRIC: {}' .format(episode, success_rate, mood_success_rate, avg_reward, quality_metric))

            # Logg data to tensorboard
            tf.summary.scalar(name="succes rate", data=success_rate)
            tf.summary.scalar(name="mood sucess rate", data=mood_success_rate)
            tf.summary.scalar(name="avg reward", data=avg_reward)
            tf.summary.scalar(name="avg intrinisc reward", data=avg_ireward)
            tf.summary.scalar(name="avg mood", data=avg_mood)
            tf.summary.scalar(name="quality metric", data=quality_metric)
            tf.summary.scalar(name="avg efficiency", data=avg_efficiancy)
            writer.flush()
            
            #if success_rate > success_rate_best:
            if quality_metric > best_quality_metric:
                print('**********************Episode: {} NEW BEST SUCCESS RATE: {} MOOD SUCCESS RATE: {} Avg Reward: {} QUALITY METRIC: {}********************************' .format(episode, success_rate, mood_success_rate, avg_reward, quality_metric))
                best_quality_metric = quality_metric
                dqn_agent.save_weights()
            period_success_total = 0
            period_reward_total = 0
            period_ireward_total = 0
            period_mood_success_total = 0
            period_mood_total = 0
            avg_mood = 0
            episode_efficiency_total = 0
            period_step = 0
            # Copy
            dqn_agent.copy()
            # Train
            dqn_agent.train()
        
        # for e-greedy exploration and exploitation wich is GLIE we need eps to decay to zero
        # if episode % 200 == 0:
        #     k = episode / 200
        #     dqn_agent.eps = 1 / (k + 1) 
            
    print('...Training Ended')
    tf.summary.flush()


def episode_reset():
    """
    Resets the episode/conversation in the warmup and training loops.

    Called in warmup and train to reset the state tracker, user and agent. Also get's the initial user action.

    """

    # First reset the state tracker
    state_tracker.reset()
    # Then pick an init user action
    user_action = user.reset()
    # Infuse with error
    if USE_USERSIM:
        emc.infuse_error(user_action)
    # And update state tracker
    state_tracker.update_state_user(user_action)
    # Finally, reset agent
    dqn_agent.reset()

    return user_action

if USE_USERSIM:
    warmup_run()
train_run()

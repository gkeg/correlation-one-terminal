import math
import os
import random
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from torch.distributions import Normal

import matplotlib.pyplot as plt
from c1env import C1Env

# Use CUDA if available
use_cuda = torch.cuda.is_available()
device = torch.device("cuda" if use_cuda else "cpu")

# Need some way to create environments, but we'll just stick with one now

# Compute the generalized advantage estimate
def compute_gae(next_value, rewards, masks, values, gamma=0.99, tau=0.95):
    values = values + [next_value]
    gae = 0
    returns = []
    for step in reversed(range(len(rewards))):
        delta = rewards[step] + gamma * values[step + 1] * masks[step] - values[step]
        gae = delta + gamma * tau * masks[step] * gae
        returns.insert(0, gae + values[step])
    return returns

# PPO Algorithm
def ppo_iter(mini_batch_size, states, actions, log_probs, returns, advantage):
    batch_size = states.size(0)
    for _ in range(batch_size // mini_batch_size):
        rand_ids = np.random.randint(0, batch_size, mini_batch_size)
        yield states[rand_ids, :], actions[rand_ids, :], log_probs[rand_ids, :], returns[rand_ids, :], advantage[rand_ids, :]



def ppo_update(model, optimizer, ppo_epochs, mini_batch_size,
               states, actions, log_probs, returns, advantages, clip_param=0.2):
    for _ in range(ppo_epochs):
        for state, action, old_log_probs, return_, advantage in ppo_iter(mini_batch_size, states, actions, log_probs, returns, advantages):
            dist, value = model(state)
            entropy = dist.entropy().mean()
            new_log_probs = dist.log_prob(action)

            ratio = (new_log_probs - old_log_probs).exp()
            surr1 = ratio * advantage
            surr2 = torch.clamp(ratio, 1.0 - clip_param, 1.0 + clip_param) * advantage

            actor_loss  = - torch.min(surr1, surr2).mean()
            critic_loss = (return_ - value).pow(2).mean()

            loss = 0.5 * critic_loss + actor_loss - 0.001 * entropy

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

if __name__ == '__main__':
    env = C1Env()
    num_inputs  = envs.observation_space.shape[0]
    num_outputs = envs.action_space.shape[0]

    # Hyper params:
    hidden_size      = 256
    lr               = 3e-4
    num_steps        = 20
    mini_batch_size  = 1
    ppo_epochs       = 4

    # Where the saved models are stored
    ALPHA_MODEL_PATH = ''
    BETA_MODEL_PATH = ''

    # Create the attack and defence models of both our agents
    alpha_model = ActorCritic(num_inputs, num_outputs, hidden_size).to(device)
    alpha_optimizer = optim.Adam(alpha_attack_model.parameters(), lr=lr)

    beta_model = ActorCritic(num_inputs, num_outputs, hidden_size).to(device)
    beta_optimizer = optim.Adam(alpha_attack_model.parameters(), lr=lr)

    # Check if we already have a saved model, then load it. Otherwise, make a new one!
    if os.path.isfile(ALPHA_MODEL_PATH):
        checkpoint = torch.load(ALPHA_MODEL_PATH)
        alpha_model.load_state_dict(checkpoint['alpha_model_state_dict'])
        alpha_optimizer.load_state_dict(checkpoint['alpha_optimizer_state_dict'])

    if os.path.isfile(BETA_MODEL_PATH):
        checkpoint = torch.load(BETA_MODEL_PATH)
        beta_model.load_state_dict(checkpoint['alpha_model_state_dict'])
        beta_optimizer.load_state_dict(checkpoint['alpha_optimizer_state_dict'])

    test_rewards = []
    num_games = 100000

    # FIND OUT HOW TO IMPLEMENT MINIBATCH GRADIENT DESCENT!

    # Call our env to play the gaem
    for _ in range(num_games):
        # Get our game state somehow
        log_probs, values, states, actions, rewards, masks, = [], [], [], [], [], []
        entropy = 0

        # Wtf does this mean! UNDERSTAND!
        state = torch.FloatTensor(state).to(device)
        dist, value = model(state)

        action = dist.sample()
        # WE WANT ENVS.PLAY TO RETURN ALL OF THESE! Maybe even return one from P1 and P2 perspective...
        states, actions, rewards, dones, log_probs = env.play_game()

        # For each item in the memory, append one of these things
        log_prob = dist.log_prob(action)
        entropy += dist.entropy().mean()

        log_probs.append(log_prob)
        values.append(value)
        rewards.append(torch.FloatTensor(reward).unsqueeze(1).to(device))
        masks.append(torch.FloatTensor(1 - done).unsqueeze(1).to(device))

        states.append(state)
        actions.append(action)

    # Instead of taking the "next state", find out the last state and use that
    next_state = torch.FloatTensor(next_state).to(device)
    _, next_value = model(next_state)
    returns = compute_gae(next_value, rewards, masks, values)

    returns = torch.cat(returns).detach()
    log_probs = torch.cat(log_probs).detach()
    values = torch.cat(values).detach()
    states = torch.cat(states)
    actions = torch.cat(actions)
    advantage = returns - values

    # Update our models
    # EXPERIMENT IF UPDATING JUST ONE OF THEM AT A TIME MAKES SENSE!
    # After, we can ensemble them
    ppo_update(alpha_model, alpha_optimizer,
               ppo_epochs, mini_batch_size, states, actions, log_probs, returns, advantage)

    ppo_update(beta_model, beta_optimizer,
               ppo_epochs, mini_batch_size, states, actions, log_probs, returns, advantage)

    # Save our models so that the games can be updated
    torch.save({'alpha_model_state_dict': alpha_model.state_dict(),
                'alpha_optimizer_state_dict': alpha_optimizer.state_dict()})

    torch.save({'beta_model_state_dict': beta_model.state_dict(),
                'beta_optimizer_state_dict': beta_optimizer.state_dict()})

# simulator/new_sensors/noise_models.py
import random

def gaussian_noise(mu=0.0, sigma=1.0):
    return random.gauss(mu, sigma)

def occasional_dropout(prob=1e-3):
    return random.random() < prob

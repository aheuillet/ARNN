import numpy as np
from scipy import linalg

def get_spectral_radius(W):
    """Given a squarred weight matrix (e.g. the recurrent reservoir matrix),
    returns the spectral radius"""
    return max(abs(linalg.eig(W)[0]))

def compute_error_NRMSE(teacher_signal, predicted_signal, verbose=False):
    """ Computes Normalized Root-Mean-Squarred Error between a teacher signal and a predicted signal
    Return the errors in this order: nmrse mean, nmrse max-min, rmse, mse.
    By default, only NMRSE mean should be considered as a general measure to be
    compared for different datasets.

    For more information, see:
    - Mean Squared Error https://en.wikipedia.org/wiki/Mean_squared_error
    - Root Mean Squared Error https://en.wikipedia.org/wiki/Root-mean-square_deviation for more info
    """
    mse = np.mean((teacher_signal - predicted_signal)**2)
    rmse = np.sqrt(mse)
    nmrse_mean = abs(rmse / np.mean(teacher_signal[:])) # Normalised RMSE (based on mean)
    nmrse_maxmin = rmse / abs(np.max(teacher_signal[:]) - np.min(teacher_signal[:])) # Normalised RMSE (based on max - min)
    return nmrse_mean, nmrse_maxmin, rmse, mse

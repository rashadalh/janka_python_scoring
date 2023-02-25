"""
Rulesets for bayesian inference model    
"""

import numpy as np
from typing import Tuple

#Ruleset, with simplifications...  

#We define ruleset 5 to follow this logic

def rulesetSimplified(loan_state: np.array, borrows : np.array, average_borrows : np.array, prepays : np.array, outstanding: np.array, alphas : np.array, betas : np.array, days_left : int, minBorrow : float = 100, loan_term : int = 30, stdBorrow : float = 500, stdThresh : float = 2) -> Tuple[np.array, np.array]:
    """
    In the simolified verision, we don't consider the penalty for late repayment, so nothing to increment
    in that event... Loan state 2 doesn't exist here... (so 0,1,3)

    Args:
        loan_state (np.array): (Mx2) array representing the previous and current loan state
        borrows (np.array): (Mx1) array representing the amount borrowed
        average_borrows (np.array): (Mx1) array representing the average amount borrowed
        outstanding (np.array): (Mx1) array representing the fraction of the loan outstanding
        betas (np.array): (Mx1) array representing borrowers beta parameters
        minBorrow (float, optional): Defaults to 100, the lowest borrow amount we will consider in the denominator for the credit extension penalty
        loan_term (int, optional): Defaults to 30, the length of the loan term in days

    Returns:
        Tuple[np.array, np.array]: [updated alphas, updated betas]
    """

    #create new vectors for alphas and betas
    alphas_new, betas_new = np.array(alphas), np.array(betas)

    #first if the loan state change is 0, this means either no credit was extended or the loan was fully paid off. In either case no need to update alphas and betas
    #...

    #Next, if the borrower has extended new credit (loan state 0->1) let's revise up the borrowers loan state based on the amount of money they have borrowed. 
    betas_new = np.where((loan_state[:,0] == 0) & (loan_state[:,1] == 1), betas_new + \
        np.where(borrows.reshape(betas_new.shape)>average_borrows.reshape(betas_new.shape) + stdThresh*stdBorrow, borrows.reshape(betas_new.shape)/np.maximum(average_borrows.reshape(betas_new.shape), minBorrow), 0), betas_new)

    #Next, if the borrower has prepays, we can make a partial increment to the the borrowers alpha base on the amount of time left (note negative time left means past due, check for this)
    bool1 = (days_left >= 0)*np.where((prepays > 0), 1, 0)
    bool2 = np.where(((loan_state[:,0] == 1) & (loan_state[:,1] == 1)), 1, 0).reshape(bool1.shape)
    bool3 = np.where((bool1== 1) & (bool2 == 1), 1, 0).reshape(alphas_new.shape)

    alphas_new = np.where(  bool3 == 1, \
                            alphas_new + np.multiply(prepays.reshape(alphas_new.shape), ((loan_term - days_left)/loan_term)), \
                            alphas_new)

    #Next, if the borrower has paid off their loan, we can make a standard increment, based on the fraction outstanding
    alphas_new = np.where( (loan_state[:, 0] == 1) & (loan_state[:, 1] == 0), alphas_new + outstanding, alphas_new)


    #if the borrower defaults, increment beta by 1, this is closer to a classical bayes approach..
    
    betas_new = np.where( loan_state[:,1] == 3, betas_new + 1, betas_new)

    return (alphas_new, betas_new)



def rulesetRefined(loan_state: np.array, borrows : np.array, average_borrows : np.array, prepays : np.array, outstanding: np.array, number_borrows : np.array, alphas : np.array, betas : np.array, days_left : int, minBorrow : float = 100, loan_term : int = 30, stdBorrow : float = 500, stdThresh : float = 2, initialWindow : int = 7) -> Tuple[np.array, np.array]:
    """
    Refined ruleset created at the end of the analysis for Parameter Fine Tunning V1.ipynb

    Args:
        loan_state (np.array): (Mx2) array representing the previous and current loan state
        borrows (np.array): (Mx1) array representing the amount borrowed
        average_borrows (np.array): (Mx1) array representing the average amount borrowed
        outstanding (np.array): (Mx1) array representing the fraction of the loan outstanding
        betas (np.array): (Mx1) array representing borrowers beta parameters
        minBorrow (float, optional): Defaults to 100, the lowest borrow amount we will consider in the denominator for the credit extension penalty
        loan_term (int, optional): Defaults to 30, the length of the loan term in days

    Returns:
        Tuple[np.array, np.array]: [updated alphas, updated betas]
    """

    #create new vectors for alphas and betas
    alphas_new, betas_new = np.array(alphas), np.array(betas)

    #if a person borrows to much money relative to what they normally borrow, assign a penalty beyond the threshold
    multStdevs = np.divide(borrows.reshape(average_borrows.shape) - average_borrows, stdBorrow).reshape(betas_new.shape)
    isNewlyDrawn = np.where((loan_state[:,0] == 0) & (loan_state[:,1] == 1),1, 0)
    betas_new = np.where((multStdevs > stdThresh) & (isNewlyDrawn == 1), betas_new + (multStdevs - stdThresh), betas_new)

    #Next, if the borrower has paid off their loan, we can make a standard increment, only if we are outside the standard time window
    daysIntoLoan = loan_term - days_left
    isOutOfWindow = 1*(daysIntoLoan > initialWindow)

    alphas_new = np.where( (loan_state[:, 0] == 1) & (loan_state[:, 1] == 0), alphas_new + isOutOfWindow, alphas_new)

    #if the borrower defaults, increment beta by 1 if it's not a first time default, otherwise shit list them
    newLiquidated = np.where((loan_state[:,0] != 3) & (loan_state[:,1] == 3), 1, 0)
    alphas_new = np.where((newLiquidated == 1) & (number_borrows.reshape(alphas_new.shape) <= 1), 0, alphas_new)
     
    betas_new = np.where((newLiquidated == 1), 
                         np.where(number_borrows.reshape(betas_new.shape) <= 1, 1, betas_new + 1),
                         betas_new)

    return (alphas_new, betas_new)
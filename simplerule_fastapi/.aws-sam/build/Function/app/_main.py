"""
Author: Rashad Haddad  
Description: Simplied API for interfacing with the borrowers pool.  
"""

from fastapi import FastAPI
from typing import Dict

from mangum import Mangum

from typing import Dict
import sys

from lib.obligor import SimpleObligor


app = FastAPI()
borrowers : Dict[str, SimpleObligor] = dict()



@app.get("/")
async def root():
    return {"message" : "Welcome to the lending API! Please use /borrower to fetch borrowers"}

@app.get("/borrowers/fetchStatus/{borrower_addr}")
async def fetchstatus(borrower_addr : str): #fetches a string print out about a borrower given by the borrower address
    borrower = borrowers.get(borrower_addr, None)

    if borrower is None:
        message = "Borrower " + str(borrower) + " does not exist"

    else:
        loans = borrower.getLoans()

        numLoans = len(loans.keys())

        probit = borrower.getProbit()

        totalAmountRepaid = 0

        for loan in loans.values():
            totalAmountRepaid += loan["original_amount"] - loan["amount"]


        message = "Borrower " + str(borrower_addr) + " has a " + str(1 - probit) + " chance of going bad on a loan of typical size and tenor per the borrowers history; having repaid " + \
            str(numLoans) + " loans totaling in amount " + str(totalAmountRepaid)

    return message

@app.get("/borrowers/addBorrower/{borrower_params}")
def addBorrower(borrower_params : str):
    """Borrower params should be seperated by ;

    Args:
        borrower_params (str) : borrower_addr;alpha;beta 
    """
    try:
        borrower_addr, alpha, beta = borrower_params.split(";")
        if borrowers.get(borrower_addr, None) is None:
            borrowers[borrower_addr] = SimpleObligor(alpha=float(alpha), beta=float(beta))
            return "Successfully added borrower with address " + borrower_addr + " " + alpha + " " + beta 
        message = "Borrower " + str(borrower_addr) + " is already contained in the data set."
    except:
        message = "Not able to add borrower with parameters : " + str(borrower_params)
    
    return message

@app.get("/borrowers/addLoan/{loan_params}")
def addLoan(loan_params : str):
    """
    Adds a new loan for the borrower 

    Args:
        loan_params (str): borrower_addr;loan_amount;tenor
    """

    try:
        borrower_addr, loan_amount, tenor = loan_params.split(";")

        if borrower_addr in borrowers.keys():
            loanID = borrowers[borrower_addr].addBorrow(float(loan_amount), float(tenor))

            print(loan_amount, tenor, borrower_addr, loanID)

            message = "Successfully added loan in amount " + loan_amount + " with tenor " + tenor \
            + " for " + borrower_addr + " with loan id " + loanID
        
        else:
            message = "Borrower " + borrower_addr + " does not exist in registry of borrowrs, please add this borrower first!"

    except Exception as e:
        message =  "Can't add loan with params " + str(loan_params) + " " + str(e)

    return message


@app.get("/borrowers/addRepay/{loan_params}")
def addRepay(repay_params : str):
    """
    Adds a new repay for the borrower 

    Args:
        repay_params (str): borrower_addr;loan_id;repay_amount;tenor
    """

    try:
        borrower_addr, loan_id, repay_amount, tenor = repay_params.split(";")

        if borrower_addr in borrowers.keys():
            success_bool = borrowers[borrower_addr].addRepay(loan_id=loan_id, amount=float(repay_amount), tenor = float(tenor))

            if success_bool:
                message = "Successfully added a repay for borrowr" + borrower_addr + " loan_id " +  loan_id + " in amount " + repay_amount + " at time of repayment " + tenor
            else:
                message = "Unable to add repay for borrower " + borrower_addr + " on loan_id " + loan_id
        else:
            message = "Borrower " + borrower_addr + " does not exist in registry of borrowrs, please add this borrower first!"

    except Exception as e:
        message = "Can't add repay with params " + str(repay_params) + " " + str(e)
    
    return message

@app.get("/borrowers/addLiquidation/{liq_params}")
def addLiquidation(liq_params : str):
    """Adds a liquidation for the borrower

    Args:
        liq_params (str): borrower_addr;loan_id
    """

    try:
        borrower_addr, loan_id = liq_params.split(";")

        if borrower_addr in borrowers.keys():
            borrowers[borrower_addr].addLiquidation(loan_id=loan_id)

            message = "Successfully liquidated " + loan_id + " for borrower " + str(borrower_addr)
        else:

            message = "Borrower " + borrower_addr + " does not exist in registry of borrowrs, please add this borrower first!"
    
    except:
        message = "Can't add repay with params " + str(liq_params)

    return message


handler = Mangum(app)
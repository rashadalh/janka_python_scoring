"""
Author: Rashad Haddad  
Description: Simplied API for interfacing with the borrowers pool.  
"""

from fastapi import FastAPI
from typing import Dict

from mangum import Mangum


from lib.obligor import SimpleObligor


app = FastAPI()

from typing import Dict


############## Simple Obligor Class ################################
#based on simplified "add 1" ruleset...
class SimpleObligor:
    def __init__(self, alpha : float, beta : float) -> None:
        
        self.__alpha : float = alpha
        self.__beta : float = beta

        self.__outstandingLoans : dict = dict()

    def _incAlpha(self) -> None:

        self.__alpha += 1

    def _incBeta(self) -> None:

        self.__beta += 1

    def _addLoan(self, amount : float, tenor : float) -> None:
        num_loan = len(list(self.__outstandingLoans.keys()))

        loan_id = "loan_" + str(num_loan+1)

        self.__outstandingLoans[loan_id] = {
            "amount" : amount,
            "original_amount" : amount,
            "tenor" : tenor,
            "status" : "outstanding"
        }

        return loan_id

    def _settleLoan(self, loan_id : str, repaymentTime : float):
        
        loan = self.__outstandingLoans.get(loan_id, None)

        if loan is None:
            return False

        if loan["status"] == "outstanding" and loan["tenor"] >= repaymentTime:
            loan["status"] = "Fully Repaid"
        elif loan["status"] == "outstanding" and loan["tenor"] < repaymentTime:
            loan["status"] = "Defaulted"
        else:
            return False

        return True
        


    def addBorrow(self, amount : float, tenor : float) -> str:
        
        #add loan.
        return self._addLoan(amount=amount, tenor=tenor)



    def addRepay(self, loan_id : str, amount : float, tenor : float) -> bool:

        #fetch loan based on loan_id
        loan = self.__outstandingLoans.get(loan_id, None)
        
        if loan is None:
            return False
        #if loan is fully paid off, settle loan, increment alpha by 1
        if loan["status"] == "outstanding":
            amountOutstanding = loan["amount"]
            amountRemaining = amountOutstanding - amount

            if amountRemaining <= 0: #means fully repaid

                #inc alpha
                self._incAlpha()

                #settle loan
                self._settleLoan(loan_id=loan_id, repaymentTime=tenor)

            else:
                #adjust loan
                self.__outstandingLoans["amount"] = amountRemaining
            return True
        return False
        
        
    def addLiquidation(self, loan_id : str):

        #fetch loan
        loan = self.__outstandingLoans.get(loan_id, None)

        if loan is None:
            raise Exception("Loan does not exist! "  + loan_id)

        #inc beta
        self._incBeta()

        #settle loan
        self._settleLoan(loan_id=loan_id, repaymentTime = loan["tenor"] + 1)

    def getLoans(self) -> Dict[str, Dict[str, object]]:
        return self.__outstandingLoans

    def getProbit(self) -> float:
        return self.__alpha / (self.__alpha + self.__beta)

################################################################



borrowers : Dict[str, SimpleObligor] = dict()



@app.get("/")
async def root():
    return {"message": "Welcome to the lending API! Please use /borrower to fetch borrowers"}

@app.get("/borrowers/fetchStatus/{borrower_addr}")
async def fetchstatus(borrower_addr : str): #fetches a string print out about a borrower given by the borrower address
    borrower = borrowers.get(borrower_addr, None)

    if borrower is None:
        return "Borrower " + str(borrower) + " does not exist"

    else:
        loans = borrower.getLoans()

        numLoans = len(loans.keys())

        probit = borrower.getProbit()

        totalAmountRepaid = 0

        for loan in loans.values():
            totalAmountRepaid += loan["original_amount"] - loan["amount"]


        message = "Borrower " + str(borrower_addr) + " has a " + str(1 - probit) + " chance of going bad on a loan of typical size and tenor per the borrowers history; having repaid " + \
            str(numLoans) + " loans totaling in amount " + str(totalAmountRepaid)

        return {"message" : message}

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
    
    return {"message" : message}

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

    return {"message" : message}


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
    
    return {"message" : message}

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

    return {"message" : message}


handler = Mangum(app)
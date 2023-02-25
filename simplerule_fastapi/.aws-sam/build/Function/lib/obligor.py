"""
Author: Rashad Haddad  
Description: Obligor data structure to track borrower parameters...
"""

from typing import Dict

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




            

        

        

    


    




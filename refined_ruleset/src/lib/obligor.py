"""
Obligor data structure to track borrower parameters.
"""

from typing import Dict, Tuple
from lib.credit_migration_schema import MigrationParams
from lib.default_migration_params import MIGRATION_PARAMS

from math import log, inf  # is natural log.


class Loan:
    """Simple struct for loan."""

    def __init__(
        self,
        amount: float,
        tenor: float,
        collateral_amt: float,
        protocol_name: str = "",
    ) -> None:
        self.amount = amount
        self.outstanding_amount = amount
        self.tenor = tenor
        self.status = "outstanding"
        self.collateral_amt = collateral_amt  # units of collateral token
        self.protocol_name: str = protocol_name

    def ltv(self, price: float) -> float:
        """Compute ltv.

        Args:
            price (float): price of collateral token in lent token.

        Returns:
            float: loan to value.
        """
        if self.collateral_amt > 0:
            return self.outstanding_amount / (self.collateral_amt * price)
        else:
            return inf


class Obligor:
    def __init__(
        self,
        alpha: int,
        beta: int,
        migration_params: MigrationParams = MIGRATION_PARAMS,
    ) -> None:
        """Create obligor class

        Args:
            alpha (int): Initial value for good credit parameter.
            beta (int): Initial value for bad credit parameter.
        """
        self._alpha: int = alpha
        self._beta: int = beta

        self._outstanding_loans: Dict[str, Loan] = {}
        self._settled_loans: Dict[str, Loan] = {}
        self._loans_per_protocol: Dict[str, int] = {}

        # set migration params
        # for origination
        self._c0 = migration_params.c0
        self._xi0 = migration_params.xi0

        # for repayment
        self._c1 = migration_params.c1
        self._xi1 = migration_params.xi1

        # for liquidation
        self._c2 = migration_params.c2
        self._xi2 = migration_params.xi2

        # for stickiness
        self._c3 = migration_params.c3
        self._xi3 = MIGRATION_PARAMS.xi3

    def _sum_ab(self) -> int:
        """Return sum of alpha + beta."""
        return self._alpha + self._beta

    def _inc_origination(self) -> None:
        """Increments beta for origination."""
        sum_ab: int = self._sum_ab()
        stki: float = self._stickness()
        self._beta = (self._beta + self._c0 * log(1 + self._xi0 / sum_ab)) * stki

    def _inc_repay(self) -> None:
        """Increments alpha for repayment."""
        sum_ab: int = self._sum_ab()
        stki: float = self._stickness()
        self._alpha = (self._alpha + self._c1 * log(1 + self._xi1 / sum_ab)) * stki

    def _inc_liquidation(self) -> None:
        """Increments liquidation."""
        sum_ab: int = self._sum_ab()
        stki: float = self._stickness()
        self._beta = (self._beta + self._c2 * log(1 + self._xi2 / sum_ab)) * stki

    def _stickness(self) -> float:
        """Guide sum of alpha + beta."""
        sum_ab: int = self._sum_ab()
        return max(1, self._c3 * log(1 + self._xi3 / sum_ab))

    def _add_loan(
        self,
        amount: float,
        tenor: float,
        collateral_amt: float,
        protocol_name: str = "",
    ) -> None:
        """Add loan to borrower's collection of loans."""
        num_loan: int = self._loans_per_protocol.get(protocol_name, 0)
        self._loans_per_protocol[protocol_name] = num_loan + 1

        # perpetual loan will be treated as loan_protocol_0
        if tenor > 0:
            loan_id = "loan_{0}_{1}".format(protocol_name, str(num_loan + 1))

            self._outstanding_loans[loan_id] = {
                Loan(
                    amount=amount,
                    tenor=tenor,
                    collateral_amt=collateral_amt,
                    protocol_name=protocol_name,
                ),
            }

        else:
            loan_id = "loan_{0}_{1}".format(protocol_name, 0)

            new_loan = self._outstanding_loans.get(
                loan_id,
                Loan(
                    amount=0,
                    tenor=tenor,
                    collateral_amt=0,
                    protocol_name=protocol_name,
                ),
            )

            new_loan.amount += amount
            new_loan.outstanding_amount += amount
            new_loan.collateral_amt += collateral_amt

            self._outstanding_loans[loan_id] = new_loan

        self._inc_origination()  # increment following scheme for new debt

        return

    def _get_loan_id(self, protocol_name: str, loan_num: int) -> str:
        return "loan_{0}_{1}".format(protocol_name, str(loan_num))

    def _fetch_loan(self, protocol_name: str = "", loan_num: int = 0) -> Loan:
        """Get the loan."""
        loan_id = self._get_loan_id(protocol_name=protocol_name, loan_num=loan_num)
        return self._outstanding_loans.get(loan_id, None)

    def _pop_loan(self, protocol_name: str = "", loan_num: int = 0) -> Tuple[Loan, str]:
        """Get and remove the loan."""
        loan_id = self._get_loan_id(protocol_name=protocol_name, loan_num=loan_num)
        if loan_id in self._outstanding_loans.keys():
            return self._outstanding_loans.pop(loan_id), loan_id
        return None, None

    def _settle_loan(
        self, repayment_time: float, protocol_name: str = "", loan_num: int = 0
    ):
        """Settle loan by marking as either repaid or defaulted."""
        loan, loan_id = self._pop_loan(protocol_name=protocol_name, loan_num=loan_num)

        if loan is None:
            return False

        if loan.status == "outstanding" and loan.tenor >= repayment_time:
            loan.status = "Fully Repaid"
        elif loan.status == "outstanding" and loan["tenor"] < repayment_time:
            loan.status = "Defaulted"
        else:
            return False

        # move loan to settled loans, get rid of from outstanding....
        self._settled_loans[loan_id] = loan

        return True

    def add_borrow(
        self,
        amount: float,
        tenor: float,
        collateral_amt: float,
        protocol_name: str = "",
    ) -> str:
        """Add borrow to borrower."""
        return self._add_loan(
            amount=amount,
            tenor=tenor,
            collateral_amt=collateral_amt,
            protocol_name=protocol_name,
        )

    def add_repay(
        self,
        amount: float,
        repayment_time: float,
        protocol_name: str = "",
        loan_num: int = 0,
    ) -> bool:

        # fetch loan based on loan_id
        loan: Loan = self._fetch_loan(protocol_name=protocol_name, loan_num=loan_num)

        if loan is None:
            return False
        # if loan is fully paid off, settle loan, increment alpha by 1
        if loan.status == "outstanding":
            # compute amount remaining
            amount_outstanding = loan.outstanding_amount
            amount_remaining = amount_outstanding - amount

            # set new outstanding amount
            loan.outstanding_amount = amount_remaining

            if loan.tenor == 0:  # means pertpetual (not a fixed loan)

                # give repay benefit if at least half as been returned
                # note this is arbitrary and should be fine tuned...
                if amount_remaining < 0.5 * loan.amount:

                    # give the repay benefit
                    self._inc_repay()

                    # set the loan's new 'amount' to the outstanding debt...
                    loan.amount = amount_remaining

                if amount_remaining <= 0:
                    # settle loan
                    self._settle_loan(
                        repayment_time=repayment_time,
                        protocol_name=protocol_name,
                        loan_num=loan_num,
                    )

            else:
                # if fixed loan, give benefit when fully repaid only...
                # again this is arbitrary, could be fine tuned...
                if amount_remaining <= 0:  # means fully repaid

                    # inc alpha, following scheme,  following full repayment
                    self._inc_repay()

                    # settle loan
                    self._settle_loan(
                        repayment_time=repayment_time,
                        protocol_name=protocol_name,
                        loan_num=loan_num,
                    )
            return True  # successfully processed repay transaction.
        return False  # nothing to reprocess.

    def add_liquidation(
        self,
        amt_to_liq: float,
        asset_price: float,
        repayment_time: float,
        protocol_name: str = "",
        loan_num: int = 0,
    ):

        # fetch loan
        loan: Loan = self._fetch_loan(protocol_name=protocol_name, loan_num=loan_num)

        # compute remain collateral
        rem_collat = loan.collateral_amt - amt_to_liq

        # reduce loan size by the amount liquidated.
        outstanding_amount_new: float = (
            loan.outstanding_amount - asset_price * amt_to_liq
        )
        loan.outstanding_amount = outstanding_amount_new
        loan.amount = outstanding_amount_new
        loan.collateral_amt = rem_collat

        if loan is None:
            raise Exception("Loan does not exist! ")

        # increment following liquidation scheme
        self._inc_liquidation()

        # if the loan is fully liquidated, settle debt.
        if outstanding_amount_new <= 0:
            # settle loan
            self._settle_loan(
                repayment_time=repayment_time,
                protocol_name=protocol_name,
                loan_num=loan_num,
            )

        # TODO, decide what to do when collat is 0.

    def withdraw_collateral(
        self, withdraw_amt: float, protocol_name: str = "", loan_num: int = ""
    ) -> bool:
        """Remove collateral from loan."""
        loan = self._fetch_loan(protocol_name=protocol_name, loan_num=loan_num)
        if not isinstance(loan, type(None)):
            loan.collateral_amt = max(loan.collateral_amt - withdraw_amt, 0)
            return True
        else:
            return False

    def get_loans(self) -> Dict[str, Dict[str, object]]:
        return self._outstanding_loans

    def get_probit(self) -> float:
        return self._alpha / (self._alpha + self._beta)

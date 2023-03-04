"""
Obligor data structure to track borrower parameters.

Supports multiple collateral types, and multiple borrow types.
Drops support for fixed tenor, assumption is perpetual loans (aave / compund style).  
"""

from typing import Dict, List, Tuple
from lib.credit_migration_schema import MigrationParams
from lib.default_migration_params import MIGRATION_PARAMS

from math import log  # is natural log


class Loan:
    """Simple struct for loan."""

    def __init__(
        self,
        amounts: List[float] = [],
        borrow_names: List[str] = [],
        collateral_amts: List[float] = [],
        collateral_names: List[str] = [],
        protocol_name: str = "",
    ) -> None:
        self.amounts = {}
        self.outstanding_amounts = {}
        self.status = "outstanding"
        self.collateral_amts = {}
        self.protocol_name: str = protocol_name

        for name, amt in zip(borrow_names, amounts):
            self.amounts[name] = amt
            self.outstanding_amounts[name] = amt

        for name, amt in zip(collateral_names, collateral_amts):
            self.collateral_amt[name] = amt

    def get_total_amount(self) -> float:
        return sum([amt for amt in self.amounts.values()])

    def get_total_outstanding_amt(self) -> float:
        return sum([amt for amt in self.outstanding_amounts.values()])

    def get_collat_amt(self, collat_name: str) -> float:
        return self.collateral_amts.get(collat_name, 0)


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
        self._sum_ab_cap = migration_params.cap

    def _sum_ab(self) -> int:
        """Return sum of alpha + beta."""
        return self._alpha + self._beta

    def _inc_origination(self) -> None:
        """Increments beta for origination."""
        sum_ab: int = self._sum_ab()
        self._beta = self._beta + self._c0 * log(1 + self._xi0 / sum_ab)
        self._stickness()

    def _inc_repay(self) -> None:
        """Increments alpha for repayment."""
        sum_ab: int = self._sum_ab()
        self._alpha = self._alpha + self._c1 * log(1 + self._xi1 / sum_ab)
        self._stickness()

    def _inc_liquidation(self) -> None:
        """Increments liquidation."""
        sum_ab: int = self._sum_ab()
        self._beta = self._beta + self._c2 * log(1 + self._xi2 / sum_ab)
        self._stickness()

    def _stickness(self) -> None:
        """Guide sum of alpha + beta."""
        sumab = self._sum_ab()
        diff = sumab - self._sum_ab_cap
        if diff > 0:
            self._alpha = max(self._alpha - 0.5 * diff, 0)
            self._beta = max(self._beta - 0.5 * diff, 0)

            # ensure can't exceed cap
            self._alpha = min(self._alpha, self._sum_ab_cap)
            self._beta = min(self._beta, self._sum_ab_cap)

    def _add_loan(
        self,
        amount: float,
        borrow_name: str,
        protocol_name: str = "",
    ) -> None:
        """Add loan to borrower's collection of loans."""

        loan_id = "loan_{0}_{1}".format(protocol_name, 0)

        new_loan = self._outstanding_loans.get(
            loan_id,
            Loan(
                amounts=[0],
                borrow_names=[borrow_name],
                protocol_name=protocol_name,
            ),
        )

        new_loan.amounts[borrow_name] = amount
        new_loan.outstanding_amounts[borrow_name] = amount

        new_loan.status = "outstanding"
        self._outstanding_loans[loan_id] = new_loan

        self._inc_origination()  # increment following scheme for new debt

    @staticmethod
    def _compute_score(proba: float):
        return round(100 * proba)

    def _get_loan_id(self, protocol_name: str, loan_num: int) -> str:
        return "loan_{0}_{1}".format(protocol_name, str(loan_num))

    def _fetch_loan(self, protocol_name: str = "", loan_num: int = 0) -> Loan:
        """Get the loan."""
        loan_id = self._get_loan_id(protocol_name=protocol_name, loan_num=loan_num)
        if loan_id not in self._outstanding_loans.keys():
            # return new / empty loan object
            self._outstanding_loans[loan_id] = Loan(protocol_name=protocol_name)
        return self._outstanding_loans[loan_id]

    def _pop_loan(self, protocol_name: str = "", loan_num: int = 0) -> Tuple[Loan, str]:
        """Get and remove the loan."""
        loan_id = self._get_loan_id(protocol_name=protocol_name, loan_num=loan_num)
        if loan_id in self._outstanding_loans.keys():
            return self._outstanding_loans.pop(loan_id), loan_id
        return None, None

    def _settle_loan(self, protocol_name: str = "", loan_num: int = 0) -> bool:
        """Moves loan to settled loans dict, if no outstanding owed or no collat."""
        loan = self._fetch_loan(protocol_name=protocol_name, loan_num=loan_num)

        if loan is None:
            return False

        if loan.get_total_outstanding_amt() <= 0:
            loan.status = "Fully Repaid"
            return True
        else:
            loan.status = "outstanding"
            return False  # can't settle loan

    def add_borrow(
        self,
        amount: float,
        borrow_name: str,
        protocol_name: str = "",
    ) -> str:
        """Add borrow to borrower."""
        return self._add_loan(
            amount=amount,
            borrow_name=borrow_name,
            protocol_name=protocol_name,
        )

    def add_repay(
        self,
        amount: float,
        borrow_name: str,
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
            amount_remaining = loan.outstanding_amounts.get(borrow_name, 0) - amount

            # set new outstanding amount
            loan.outstanding_amounts[borrow_name] = amount_remaining

            # give repay benefit if at least half as been returned
            # note this is arbitrary and should be fine tuned...
            if amount_remaining < 0.5 * loan.amounts[borrow_name]:

                # give the repay benefit
                self._inc_repay()

                # set the loan's new 'amount' to the outstanding debt...
                loan.amounts[borrow_name] = amount_remaining

            if amount_remaining <= 0:
                # settle loan
                self._settle_loan(
                    protocol_name=protocol_name,
                    loan_num=loan_num,
                )

            return True  # successfully processed repay transaction.
        return False  # nothing to reprocess.

    # maybe add this.
    def add_collateral(
        self,
        amt_colat_to_add: float,
        collat_name: str,
        protocol_name: str = "",
        loan_num: int = 0,
    ) -> bool:
        """Simple function to improve credit by adding collateral. This effectively awards keeping util low."""

        loan = self._fetch_loan(protocol_name=protocol_name, loan_num=loan_num)

        if not isinstance(loan, type(None)):
            original_collat_amt = loan.collateral_amts.get(collat_name, 0)
            loan.collateral_amts[collat_name] = original_collat_amt + amt_colat_to_add

            # 0.5 is just a guess at a reasonable parameter. This would need to be optimized.
            if amt_colat_to_add > 0.5 * original_collat_amt:

                # award repay benefit for providing substantial colat to reduce risk
                self._inc_repay()

            return True
        return False

    def add_liquidation(
        self,
        amt_to_liq: float,
        collat_name: str,
        protocol_name: str = "",
        loan_num: int = 0,
    ):

        # fetch loan
        loan: Loan = self._fetch_loan(protocol_name=protocol_name, loan_num=loan_num)

        if loan is None:
            raise Exception("Loan does not exist! ")

        # if aave in protocol name, search
        # for the correct type of collat
        # as it liquidates aEth[...]
        if "aave" in protocol_name:
            for name in loan.collateral_amts.keys():
                if collat_name in name:
                    # update the collateral amt
                    loan.collateral_amts[name] -= amt_to_liq
                    self._inc_liquidation()
                    return True
            raise Exception("Can't liqudiate " + collat_name)
        else:
            loan.collateral_amts[collat_name] -= amt_to_liq
            self._inc_liquidation()

    def withdraw_collateral(
        self,
        withdraw_amt: float,
        collat_name: str,
        protocol_name: str = "",
        loan_num: int = "",
    ) -> bool:
        """Remove collateral from loan."""
        loan = self._fetch_loan(protocol_name=protocol_name, loan_num=loan_num)
        if not isinstance(loan, type(None)):
            loan.collateral_amts[collat_name] -= withdraw_amt
            return True
        else:
            return False

    def get_loans(self) -> Dict[str, Dict[str, object]]:
        return self._outstanding_loans

    def get_proba(self) -> float:
        return self._alpha / (self._alpha + self._beta)

    def get_score(self) -> int:
        return self._compute_score(self.get_proba())

    def get_variance(self) -> float:
        return (self._alpha * self._beta) / (
            ((self._alpha + self._beta) ** 2) * (self._alpha + self._beta + 1)
        )

    def get_conf_interval(self, z: int = 2) -> Tuple[int, int]:
        # get variance
        stdev: float = self.get_variance() ** 0.5

        # get bounds
        proba = self.get_proba()
        lower_bound: float = max(proba - z * stdev, 0)
        upper_bound: float = max(proba + z * stdev, 0)

        # get score
        lower_score: float = self._compute_score(lower_bound)
        upper_score: float = self._compute_score(upper_bound)

        return (lower_score, upper_score)

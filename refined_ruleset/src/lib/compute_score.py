"""Module for computing score from raw json.

Note, repayment_time, tenor, and loan num are all 0 b/c
we are only work with perpetual style loans for now.


Everything should be stored relative to common base currency.
Here we use USD.
"""


import pandas as pd
from lib.obligor_v2 import Obligor  # v2 is for runnning live (not sim) data
from lib.credit_migration_schema import MigrationParams
from lib.default_migration_params import MIGRATION_PARAMS

def compute_score(input_data: dict, start_alpha: int, start_beta: int, migration_params: MigrationParams = MIGRATION_PARAMS,protocol_name:str="")->int:
    """Computes the score given input data.

    Args:
        input_data (pd.DataFrame): Input data, json.

    Returns:
        int: Janka Score, 0-100.
    """
    # python, easiest way to sort is thru pandas dataframe
    dat = pd.json_normalize(input_data)
    dat.sort_values(by=["timestamp", "logIndex"], ascending=True, inplace=True)
    dat["amount"] = dat["amount"].astype(float)

    # Instantiate obligor class
    obl: Obligor = Obligor(alpha=start_alpha, beta=start_beta, migration_params=migration_params)

    # run thru the events.
    for ix, event in dat.iterrows():
        if event["type"] == 'borrow':

            obl.add_borrow(amount=event.amount, borrow_name=event.symbol, protocol_name=protocol_name)
        elif event["type"] == 'deposit':
            # compute price of asset
            obl.add_collateral(amt_colat_to_add=event.amount,collat_name=event.symbol, protocol_name=protocol_name)
            # note, asset price is hard coded as 1 until we get amount USD in query.
        elif event["type"] == 'repay':
            obl.add_repay(amount=event.amount, borrow_name=event.symbol, protocol_name = protocol_name, loan_num=0)
        elif event['type'] == 'withdraw':
            obl.withdraw_collateral(withdraw_amt=event.amount,collat_name=event.symbol,protocol_name=protocol_name,loan_num=0)
            # note, asset price is hard coded as 1 until we get amount USD in query.
        elif event["type"] == 'liquidation':
            #if protocol is aave, liquidation token starts with a then is CollatBORROW
            liq_symbol = event.symbol
            if 'aave_v3' in protocol_name:
                first_upper = 2
                while first_upper < len(liq_symbol) and (not liq_symbol[first_upper].isupper()):
                    first_upper += 1
                liq_symbol = liq_symbol[1:first_upper].upper()
            obl.add_liquidation(amt_to_liq=event.amount, collat_name=liq_symbol, protocol_name=protocol_name, loan_num=0)
        else:
            pass
        #print(ix, event.symbol, event.type, obl.get_score())

    return obl




        



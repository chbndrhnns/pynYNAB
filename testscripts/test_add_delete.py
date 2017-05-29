from pynYNAB.ClientFactory import clientfromargs
from pynYNAB.__main__ import parser
from pynYNAB.schema import Transaction
from datetime import datetime

args = parser.parse_known_args()[0]
client = clientfromargs(args)

for account in client.budget.be_accounts:
    account0 = account

#for transaction in client.budget.be_transactions:
#    if not transaction.is_tombstone:
#        client.delete_transaction(transaction)
#        exit(0)

transactions = [Transaction(
    amount=0,
    memo='test',
    cleared='Uncleared',
    date=datetime.now(),
    entities_account_id=account0.id,
) for i in range(5)]

for tr in transactions:
    client.add_transaction(tr)
    client.delete_transaction(tr)


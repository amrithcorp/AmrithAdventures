from monero.backends.jsonrpc import JSONRPCWallet
from monero.seed import Seed
from monero.daemon import Daemon
from decimal import Decimal
from monero.wallet import Wallet
import json
import datetime
def json_wallet_cmd():
    w = Wallet(port = 28081)
    all_incoming_tx = w.incoming(unconfirmed = True, confirmed = True)
    all_outgoing_tx = w.outgoing(unconfirmed = True, confirmed = True)
    unconfirmed_incoming_tx = w.incoming(unconfirmed = True,confirmed = False)
    unconfirmed_outgoing_tx = w.outgoing(unconfirmed = True,confirmed = False)
    confirmed_incoming_tx = w.incoming(unconfirmed = False,confirmed = True)
    confirmed_outgoing_tx = w.outgoing(unconfirmed = False,confirmed = True)
    total_balance = float(Decimal(w.balance()))
    unlocked_balance = float(Decimal(w.balance(unlocked = True)))
    locked_balance = total_balance - unlocked_balance
    all_accounts = w.accounts
    all_addresses = w.addresses()
    json_wallet = {}
    json_wallet['accounts_data'] = {}
    json_wallet['wallet_data'] = {
    "account_amount" : len(all_accounts),
    "address_amount" : len(all_addresses)
    }
    json_wallet['accounts_data']['accounts'] = []
    json_wallet['wallet_data']['balance'] = {
    "locked_balance" : locked_balance,
    "unlocked_balance" : unlocked_balance,
    "total_balance" : total_balance 
    }
    json_wallet['wallet_data']['keys'] = {
        "seed" : w.seed().phrase,
        "view_key" : w.view_key(),
        "spend_key" : w.spend_key(),
        }
    json_wallet['wallet_data']['transaction_info'] = {
        "all_incoming_tx_amount" : len(all_incoming_tx),
        "all_outgoing_tx_amount" : len(all_outgoing_tx),
        "unconfirmed_outgoing_tx_amount" : len(unconfirmed_outgoing_tx),
        "unconfirmed_incoming_tx_amount" : len(unconfirmed_incoming_tx),
        "confirmed_incoming_tx_amount" : len(confirmed_incoming_tx),
        "confirmed_outgoing_tx_amount" : len(confirmed_outgoing_tx)
        }
    json_wallet['incoming_transactions'] = []
    json_wallet['outgoing_transactions'] = []
    for i in all_incoming_tx:
        if w.confirmations(i) >= 26:
            is_confirmed = True
            full_transaction = str(i).split()
            json_wallet['incoming_transactions'].append({
                "transaction_id" : full_transaction[1],
                "block_height" : full_transaction[3],
                "amount" : float(full_transaction[4]),
                "confirmations" : w.confirmations(i),
                "is_confirmed" : is_confirmed
            })
    for i in all_outgoing_tx:
        if w.confirmations(i) >= 26:
            is_confirmed = True
            full_transaction = str(i).split()
            json_wallet['outgoing_transactions'].append({
                "transaction_id" : full_transaction[1],
                "block_height" : full_transaction[3],
                "amount" : float(full_transaction[4]),
                "confirmations" : w.confirmations(i),
                "is_confirmed" : is_confirmed
            })    
    for account in all_accounts:
        addresses = []
        for i in account.addresses():
            addresses.append({"address" : str(i)})
            total_balance = float(Decimal(account.balance()))
            unlocked_balance = float(Decimal(account.balance(unlocked = True)))
            locked_balance = total_balance - unlocked_balance
            json_wallet['accounts_data']['accounts'].append({
                "address_amount" : len(account.addresses()),
                "account_balance" : total_balance,
                "locked_account_balance" : locked_balance,
                "unlocked_account_balance" : unlocked_balance,
                "addresses" : addresses
            })
        return json_wallet   


import json
import requests
import datetime
import time
from stellar_sdk import (
    Asset,
    Keypair,
    Network,
    Server,
    TransactionBuilder
            ) 


appConfig = {
    "testnet" : False,
    "memo_message" : "AmrithCoin Testing",
    "pool_name" : "AmrithCoin/XLM",
    "company_name" : "AmrithCorp",
    "pool_id" : "--pool-id--",
    "horizon" : "https://horizon.stellar.org/",
    "secret_key" : "--secret-key--",
    "asset_disperse_daily" : 50000,
    "asset_royalty_daily" : 48000,
    "asset_disperse" : {
        "code" : "AmrithCoin",
        "issuer" : "GCX2ENOVSSOOH6G4HIOBMPCBFXHDVDGA546NK3ZFX3NP3QS25BKZBWOW"
    },
    "asset_royalty" : {
        "code" : "AmrithCoin",
        "issuer" : "GCX2ENOVSSOOH6G4HIOBMPCBFXHDVDGA546NK3ZFX3NP3QS25BKZBWOW",
        "send_to" : "GBGLSXXLGTGLVLVPXK34MR6WNLFE2L3LNXZYTKRDF4ECL66LYOUUI5RJ",
        "pay_from_secret" : "--secret-key--"
    },
    
}



def get_pool_index(balances,pool_id):
    i = 0
    while(i < len(balances)):
        if balances[i]['asset_type'] == "liquidity_pool_shares":
            if balances[i]['liquidity_pool_id'] == pool_id:
                return i
        i+=1
                
def get_liquidity_pool_voters(pool_id):
    accounts_url = f"{appConfig['horizon']}accounts?cursor=&limit=200&liquidity_pool={pool_id}&order=asc"
    pool_info_url = f"{appConfig['horizon']}liquidity_pools/{pool_id}"
    pool_info = requests.get(pool_info_url).json()
    providerList = []
    total_shares = 0
    while(True):
        accounts = requests.get(accounts_url).json()
        if accounts['_embedded']['records'] != []:
            accounts_url = accounts['_links']['next']['href']
            for i in accounts['_embedded']['records']:
                index = get_pool_index(i['balances'],pool_id)                
                bal = i['balances'][index]['balance']
                if bal != "0.0000000":
                    status = f"User: {i['id']} has {bal} pool shares"
                    # print(status)
                    provider = {'account_id':i['id'], 'pool_shares':float(bal)}
                    total_shares += float(bal)
                    providerList.append(provider)
        else:
            break
    print(f"found {len(providerList)} eligible liquidity provider(s).")
    return {"providers":providerList,"total_shares":total_shares}
    
def calculate_reward():
    accounts = get_liquidity_pool_voters(appConfig['pool_id'])
    for i in accounts['providers']:
        i['reward'] = round(((i['pool_shares'] / accounts['total_shares']) * appConfig['asset_disperse_daily'])/24,7)
    return accounts
    
def lambda_handler(event,context):
    reward_list = calculate_reward()
    keypair = Keypair.from_secret(appConfig['secret_key'])
    server = Server(appConfig['horizon'])
    account = server.load_account(keypair.public_key)
    batch = 0
    hashes = []
    z = 0
    # for i in reward_list['providers']:
    #     z += i['reward']
    # return z
    fee_stat = requests.get(appConfig['horizon'] + "fee_stats").json()
    fee = int(fee_stat['max_fee']['p90'])
    tx = TransactionBuilder(
        source_account=account,
        network_passphrase=(Network.PUBLIC_NETWORK_PASSPHRASE if appConfig['testnet'] == False else Network.TESTNET_NETWORK_PASSPHRASE),
        base_fee=500000
        )
    tx.add_text_memo(appConfig['memo_message'])
    for i in reward_list['providers']:
        if batch == 100:
        # if batch == 100:
            batch = 0
            completed = tx.build()
            completed.sign(keypair)
            sub = server.submit_transaction(completed)
            hashes.append(sub['hash'])
            print("submitted transaction")
            time.sleep(5)
            tx = TransactionBuilder(
            source_account=account,
            network_passphrase=(Network.PUBLIC_NETWORK_PASSPHRASE if appConfig['testnet'] == False else Network.TESTNET_NETWORK_PASSPHRASE),
            base_fee=500000
            )    
            tx.add_text_memo(appConfig['memo_message'])
        else:
            batch += 1
            tx.append_payment_op(
                i['account_id'],
                asset = Asset(
                    appConfig['asset_disperse']['code'],
                    appConfig['asset_disperse']['issuer'],
                    ),
                amount=str(i['reward'])
                )
    if batch!=0:
        completed = tx.build()
        completed.sign(keypair)
        sub = server.submit_transaction(completed)
        hashes.append(sub['hash'])
    else:
        print("done")
    if appConfig['asset_royalty_daily'] != 0:
        royalty_keypair = Keypair.from_secret(appConfig['asset_royalty']['pay_from_secret'])
        royalty_source = server.load_account(royalty_keypair.public_key)
        royalty_tx = TransactionBuilder(
            source_account = royalty_source,
            network_passphrase=(Network.PUBLIC_NETWORK_PASSPHRASE if appConfig['testnet'] == False else Network.TESTNET_NETWORK_PASSPHRASE),
            base_fee = 500000,
            ).append_payment_op(
                appConfig['asset_royalty']['send_to'],
                Asset(
                    appConfig['asset_royalty']['code'],
                    appConfig['asset_royalty']['issuer'],
                    ),
                str(appConfig['asset_royalty_daily']/24)
                ).add_text_memo(f"{appConfig['company_name']}/{appConfig['pool_name']}").build()
        royalty_tx.sign(royalty_keypair)
        response = server.submit_transaction(royalty_tx)
        return (response['hash'])


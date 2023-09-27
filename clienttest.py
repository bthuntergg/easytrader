from easytrader import remoteclient

user = remoteclient.use('universal_client', host='127.0.0.1', port='1430')

user.prepare(exe_path=r'D:\同花顺软件\同花顺\xiadan.exe')

print(user)
# user.buy('601238', price='10.40', amount=100)
user.sell('601238', price='10.40', amount=100)


# print('用户资金',user.balance)
# print('用户持仓',user.position)

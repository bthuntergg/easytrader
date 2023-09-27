from easytrader import server
from easytrader import rpc_server

# server.run(port=1430)  # 默认端口为 1430
rpc_server.run('tcp://*:1430', 'tcp://*:1431')

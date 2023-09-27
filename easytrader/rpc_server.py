from __future__ import print_function
from __future__ import absolute_import
import functools

from . import api
from .log import logger
from .rpc import RpcServer

global_store = {}
from time import time, sleep

def error_handle(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        # pylint: disable=broad-except
        except Exception as e:
            logger.exception("服务器 错误")
            message = "{}: {}".format(e.__class__, e)
            return {"error": message}, 400

    return wrapper


class ThsRpcServer(RpcServer):
    """
    ThsRpcServer
    """

    def __init__(self):
        """
        Constructor
        """
        super(ThsRpcServer, self).__init__()

        self.register(self.prepare)
        self.register(self.balance)
        self.register(self.position)
        self.register(self.auto_ipo)
        self.register(self.today_entrusts)
        self.register(self.today_trades)
        self.register(self.cancel_entrusts)
        self.register(self.buy)
        self.register(self.sell)
        self.register(self.cancel_entrust)
        self.register(self.exit)
        self.register(self.hangqing)

    @error_handle
    def prepare(self, request):
        # json_data = request.get_json(force=True)
        json_data = request
        # print(type(request['kwargs']))
        json_data.update(json_data['kwargs'])
        json_data.pop('kwargs')
        user = api.use(json_data.pop("broker"), debug=False)

        user.prepare(**json_data)
        global_store["user"] = user
        # print(global_store)
        return {"msg": "login success"}, 201

    @error_handle
    def balance(self, request):
        user = global_store["user"]
        user.main().maximize()
        balance = user.balance

        # print('balance',balance)
        return balance, 200

    @error_handle
    def position(self, request):
        user = global_store["user"]
        user.main().maximize()
        position = user.position
        # print('position',position)
        return position, 200

    @error_handle
    def auto_ipo(self, request):
        user = global_store["user"]
        user.main().maximize()
        res = user.auto_ipo()

        return res, 200

    @error_handle
    def today_entrusts(self, request):
        user = global_store["user"]
        user.main().maximize()
        today_entrusts = user.today_entrusts

        return today_entrusts, 200

    @error_handle
    def today_trades(self, request):
        user = global_store["user"]
        user.main().maximize()
        today_trades = user.today_trades

        return today_trades, 200

    @error_handle
    def cancel_entrusts(self, request):
        user = global_store["user"]
        user.main().maximize()
        cancel_entrusts = user.cancel_entrusts

        return cancel_entrusts, 200

    @error_handle
    def buy(self, request):
        # json_data = request.get_json(force=True)
        json_data = request
        user = global_store["user"]
        user.main().maximize()
        res = user.buy(**json_data)

        return res, 201

    @error_handle
    def sell(self, request):
        # json_data = request.get_json(force=True)
        json_data = request

        user = global_store["user"]
        user.main().maximize()
        res = user.sell(**json_data)

        return res, 201

    @error_handle
    def cancel_entrust(self, request):
        # json_data = request.get_json(force=True)
        json_data = request

        user = global_store["user"]
        user.main().maximize()
        res = user.cancel_entrust(**json_data)

        return res, 201

    @error_handle
    def exit(self, request):
        user = global_store["user"]
        user.main().maximize()
        user.exit()

        return {"msg": "exit success"}, 200

    @error_handle
    def hangqing(self, request):
        json_data = request
        user = global_store["user"]
        user.main().maximize()
        data = user.hangqing(**json_data)

        return data, 200


def run(rep_address, pub_address) -> None:
    rpc_server = ThsRpcServer()
    rpc_server.start(rep_address, pub_address)
    print('运行')
    # while 1:
    #     content = f"当前服务器时间{time()}"
    #     print(content)
    #     rpc_server.publish("vnpy", content)
    #     sleep(2)

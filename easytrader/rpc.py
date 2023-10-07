import os
import signal
import threading
import traceback
from datetime import datetime, timedelta
from functools import lru_cache
from time import time
from typing import Any, Callable, Dict
import zmq
import zmq.auth
from pathlib import Path

# Achieve Ctrl-c interrupt recv
signal.signal(signal.SIGINT, signal.SIG_DFL)

HEARTBEAT_TOPIC = "heartbeat"
HEARTBEAT_INTERVAL = 10
HEARTBEAT_TOLERANCE = 60


class RemoteException(Exception):
    """
    RPC remote exception
    """

    def __init__(self, value: Any):
        """
        Constructor
        """
        self.__value = value

    def __str__(self):
        """
        Output error message
        """
        return self.__value


class RpcServer:
    """"""

    def __init__(self) -> None:
        """
        Constructor
        """
        # Save functions dict: key is function name, value is function object
        self._functions: Dict[str, Callable] = {}

        # Zmq port related
        self._context: zmq.Context = zmq.Context()

        # Reply socket (Request–reply pattern)
        self._socket_rep: zmq.Socket = self._context.socket(zmq.REP)

        # Publish socket (Publish–subscribe pattern)
        self._socket_pub: zmq.Socket = self._context.socket(zmq.PUB)

        # Worker thread related
        self._active: bool = False  # RpcServer status
        self._thread: threading.Thread = None  # RpcServer thread
        self._lock: threading.Lock = threading.Lock()

        # Heartbeat related
        self._heartbeat_at: int = None

    def is_active(self) -> bool:
        """"""
        return self._active

    def start(
            self,
            rep_address: str,
            pub_address: str,
    ) -> None:
        """
        Start RpcServer
        """
        if self._active:
            return

        # Bind socket address
        self._socket_rep.bind(rep_address)
        self._socket_pub.bind(pub_address)

        # Start RpcServer status
        self._active = True

        # Start RpcServer thread
        self._thread = threading.Thread(target=self.run)
        self._thread.start()

        # Init heartbeat发布时间戳 Init heartbeat publish timestamp
        self._heartbeat_at = time() + HEARTBEAT_INTERVAL

    def stop(self) -> None:
        """
        Stop RpcServer
        """
        if not self._active:
            return

        # Stop RpcServer status
        self._active = False

    def join(self) -> None:
        # 等待RpcServer线程退出 Wait for RpcServer thread to exit
        if self._thread and self._thread.is_alive():
            self._thread.join()
        self._thread = None

    def run(self) -> None:
        """
        Run RpcServer functions
        """
        while self._active:
            # 轮询响应套接字1秒 Poll response socket for 1 second
            n: int = self._socket_rep.poll(1000)
            self.check_heartbeat()

            if not n:
                continue

            # 从应答套接字接收请求数据 Receive request data from Reply socket
            req = self._socket_rep.recv_pyobj()

            # 获取函数名称和参数 Get function name and parameters
            name, args, kwargs = req

            # 尝试获取并执行可调用的函数对象;如果失败，捕获异常信息 Try to get and execute callable function object; capture exception information if it fails
            try:
                func: Callable = self._functions[name]
                r: Any = func(*args, **kwargs)
                rep: list = [True, r]
            except Exception as e:  # noqa
                rep: list = [False, traceback.format_exc()]

            # 通过应答套接字发送可调用的响应 send callable response by Reply socket
            self._socket_rep.send_pyobj(rep)

        # 解绑定套接字地址 Unbind socket address
        self._socket_pub.unbind(self._socket_pub.LAST_ENDPOINT)
        self._socket_rep.unbind(self._socket_rep.LAST_ENDPOINT)

    def publish(self, topic: str, data: Any) -> None:
        """
        Publish data
        """
        with self._lock:
            self._socket_pub.send_pyobj([topic, data])

    def register(self, func: Callable) -> None:
        """
        Register function
        """
        self._functions[func.__name__] = func

    def check_heartbeat(self) -> None:
        """
        Check whether it is required to send heartbeat.
        """
        now: float = time()
        if now >= self._heartbeat_at:
            # 发布的心跳包 Publish heartbeat
            self.publish(HEARTBEAT_TOPIC, now)

            # 更新下次发布的时间戳Update timestamp of next publish
            self._heartbeat_at = now + HEARTBEAT_INTERVAL


class RpcClient:
    """"""

    def __init__(self) -> None:
        """Constructor"""
        # zmq port related
        self._context: zmq.Context = zmq.Context()

        # 请求套接字(请求-应答模式) Request socket (Request–reply pattern)
        self._socket_req: zmq.Socket = self._context.socket(zmq.REQ)

        # 订阅套接字(发布-订阅模式) Subscribe socket (Publish–subscribe pattern)
        self._socket_sub: zmq.Socket = self._context.socket(zmq.SUB)

        # 设置socket选项为keepalive Set socket option to keepalive
        for socket in [self._socket_req, self._socket_sub]:
            socket.setsockopt(zmq.TCP_KEEPALIVE, 1)
            socket.setsockopt(zmq.TCP_KEEPALIVE_IDLE, 60)

        # 工作线程相关，用于处理从服务器推送的数据 Worker thread relate, used to process data pushed from server
        self._active: bool = False  # RpcClient status
        self._thread: threading.Thread = None  # RpcClient thread
        self._lock: threading.Lock = threading.Lock()

        self._last_received_ping: datetime = datetime.utcnow()

    @lru_cache(100)
    def __getattr__(self, name: str) -> Any:
        """
        Realize remote call function
        """

        # 执行远程调用任务 Perform remote call task
        def dorpc(*args, **kwargs):
            # 从kwargs中获取超时值，默认值为30秒 Get timeout value from kwargs, default value is 30 seconds
            if "timeout" in kwargs:
                timeout = kwargs.pop("timeout")
            else:
                timeout = 30000

            # Generate request
            req: list = [name, args, kwargs]

            # 发送请求并等待响应 Send request and wait for response
            with self._lock:
                self._socket_req.send_pyobj(req)

                # 超时，没有任何数据 Timeout reached without any data
                n: int = self._socket_req.poll(timeout)
                if not n:
                    msg: str = f"Timeout of {timeout}ms reached for {req}"
                    raise RemoteException(msg)

                rep = self._socket_req.recv_pyobj()

            # 如果成功返回响应;失败时触发异常 Return response if successed; Trigger exception if failed
            if rep[0]:
                return rep[1]
            else:
                raise RemoteException(rep[1])

        return dorpc

    def start(
            self,
            req_address: str,
            sub_address: str
    ) -> None:
        """
        Start RpcClient
        """
        if self._active:
            return

        # Connect zmq port
        self._socket_req.connect(req_address)
        self._socket_sub.connect(sub_address)

        # Start RpcClient status
        self._active = True

        # Start RpcClient thread
        self._thread = threading.Thread(target=self.run)
        self._thread.start()

        self._last_received_ping = datetime.utcnow()

    def stop(self) -> None:
        """
        Stop RpcClient
        """
        if not self._active:
            return

        # Stop RpcClient status
        self._active = False

    def join(self) -> None:
        # Wait for RpcClient thread to exit
        if self._thread and self._thread.is_alive():
            self._thread.join()
        self._thread = None

    def run(self) -> None:
        """
        Run RpcClient function
        """
        pull_tolerance: int = HEARTBEAT_TOLERANCE * 1000
        while self._active:
            if not self._socket_sub.poll(pull_tolerance):
                self.on_disconnected()
                continue

            # Receive data from subscribe socket
            topic, data = self._socket_sub.recv_pyobj(flags=zmq.NOBLOCK)

            if topic == HEARTBEAT_TOPIC:
                self._last_received_ping = data
            else:
                # Process data by callable function
                self.callback(topic, data)

        # Close socket
        self._socket_req.close()
        self._socket_sub.close()

    def callback(self, topic: str, data: Any) -> None:
        """
        Callable function
        """
        raise NotImplementedError

    def subscribe_topic(self, topic: str) -> None:
        """
        Subscribe data
        """
        self._socket_sub.setsockopt_string(zmq.SUBSCRIBE, topic)

    def on_disconnected(self):
        """
        Callback when heartbeat is lost.
        """
        msg: str = f"RpcServer超过 {HEARTBEAT_TOLERANCE} 秒没有响,请检查您的连接。"
        print(msg)


def generate_certificates(name: str) -> None:
    """
    Generate CURVE certificate files for zmq authenticator.
    """
    keys_path = Path.cwd().joinpath("certificates")
    if not keys_path.exists():
        os.mkdir(keys_path)

    zmq.auth.create_certificates(keys_path, name)

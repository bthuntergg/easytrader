# -*- coding: utf-8 -*-

import pywinauto
import pywinauto.clipboard

from easytrader import grid_strategies
from . import clienttrader

from typing import TYPE_CHECKING, Dict, List, Optional
from easytrader.log import logger
from easytrader.utils.captcha import captcha_recognize

class Xls(grid_strategies.Xls):
    """
    通过将 Grid 另存为 xls 文件再读取的方式获取 grid 内容
    """

    def __init__(self, tmp_folder: Optional[str] = None):
        """
        :param tmp_folder: 用于保持临时文件的文件夹
        """
        super().__init__()
        self.tmp_folder = tmp_folder

    def get(self, control_id: int) -> List[Dict]:
        grid = self._get_grid(control_id)

        # ctrl+s 保存 grid 内容为 xls 文件
        self._set_foreground(grid)  # setFocus buggy, instead of SetForegroundWindow
        grid.type_keys("^s", set_foreground=False)
        count = 1
        while count > 0:
            if self._trader.is_exist_pop_dialog() and self._trader.app.top_window().window_text() != '另存为':
                pop_dialog_window = self._trader.app.top_window()  # 验证码弹窗
                pop_dialog_window.Static2.click()
                file_path = './tmp/tmp.png'
                pop_dialog_window.Static2.capture_as_image().save(file_path)
                captcha_num = captcha_recognize(file_path).strip()  # 识别验证码
                captcha_num = "".join(captcha_num.split())
                # logger.info("captcha result-->" + captcha_num)
                pop_dialog_window.Edit.click().type_keys("{RIGHT}" * 10).type_keys("{BACKSPACE}" * 12).type_keys(
                    captcha_num).type_keys('{ENTER}')
                if pop_dialog_window.wrapper_object() == self._trader.app.top_window():
                    count = 2
                # break
            self._trader.wait(1)
            count -= 1

        # temp_path = tempfile.mktemp(suffix=".xls", dir=self.tmp_folder)
        temp_path = self.tmp_folder + r'\position.xls'
        self._set_foreground(self._trader.app.top_window())

        # alt+s保存，alt+y替换已存在的文件
        self._trader.app.top_window().Edit1.set_edit_text(temp_path)
        self._trader.wait(1)
        self._trader.app.top_window().type_keys("%{s}%{y}", set_foreground=False)
        # Wait until file save complete otherwise pandas can not find file
        self._trader.wait(1)
        if self._trader.is_exist_pop_dialog():
            self._trader.app.top_window().Button2.click()
            self._trader.wait(0.2)

        return self._format_grid_data(temp_path)

class UniversalClientTrader(clienttrader.BaseLoginClientTrader):
    grid_strategy = Xls

    @property
    def broker_type(self):
        return "universal"

    def login(self, user, password, exe_path, comm_password=None, **kwargs):
        """
        :param user: 用户名
        :param password: 密码
        :param exe_path: 客户端路径, 类似
        :param comm_password:
        :param kwargs:
        :return:
        """
        self._editor_need_type_keys = False

        try:
            self._app = pywinauto.Application().connect(
                path=self._run_exe_path(exe_path), timeout=1
            )
        # pylint: disable=broad-except
        except Exception:
            self._app = pywinauto.Application().start(exe_path)

            # wait login window ready
            while True:
                try:
                    login_window = pywinauto.findwindows.find_window(title="用户登录",class_name='#32770')
                    break
                except:
                    self.wait(1)

            self.wait(1)
            user_login_window = self._app.window(handle=login_window)
            # user_login_window = self._app.window()
            yzm = user_login_window['验 证 码(&V):Static1']
            file_path = './tmp/tmp.png'
            yzm.capture_as_image().save(file_path)
            captcha_num = captcha_recognize(file_path).strip()  # 识别验证码
            captcha_num = "".join(captcha_num.split())

            user_login_window.Edit1.set_focus()             #获取账号输入框焦点
            user_login_window.Edit1.type_keys(user)         #输入账号
            user_login_window.Edit2.set_focus()             #获取密码输入框焦点
            user_login_window.Edit2.type_keys(password)     #输入密码
            user_login_window.Edit7.set_focus()
            user_login_window['验 证 码(&V):Edit1'].type_keys(captcha_num)  #输入验证码

            try:
                user_login_window.type_keys("%{y}", set_foreground=False)
                user_login_window.wait_not('ready', timeout=5,retry_interval=2)
            except Exception as e:
                self._app.top_window().Button.click()
                self.wait(0.2)
                yzm = self._app.top_window()['验 证 码(&V):Static1']
                file_path = './tmp/tmp.png'
                yzm.capture_as_image().save(file_path)
                captcha_num = captcha_recognize(file_path).strip()  # 识别验证码
                captcha_num = "".join(captcha_num.split())
                self._app.top_window().Edit7.set_focus()
                self._app.top_window()['验 证 码(&V):Edit1'].type_keys(captcha_num)  # 输入验证码
                self._app.top_window().type_keys("%{y}", set_foreground=False)



            # user_login_window.button7.click()
            # self._app.window(handle=login_window).Edit1.set_focus()
            # self._app.window(handle=login_window).Edit1.type_keys(user)
            #
            # self._app.window(handle=login_window).button7.click()

            # detect login is success or not
            # self._app.top_window().wait_not("exists", 100)
            self.wait(10)

            self._app = pywinauto.Application().connect(
                path=self._run_exe_path(exe_path), timeout=10
            )

        self._close_prompt_windows()
        self._main = self._app.window(title="网上股票交易系统5.0")


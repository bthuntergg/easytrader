# -*- coding: utf-8 -*-
import logging
import subprocess
import time

import pywinauto
import pywinauto.clipboard

from . import grid_strategies
from . import clienttrader

from typing import TYPE_CHECKING, Dict, List, Optional
from .log import logger
from .utils.captcha import captcha_recognize
from datetime import datetime
import random
import os
import pandas as pd

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
        # self.tmp_folder = './'

    def get(self, control_id: int) -> List[Dict]:
        grid = self._get_grid(control_id)

        # ctrl+s 保存 grid 内容为 xls 文件
        self._set_foreground(grid)  # setFocus buggy, instead of SetForegroundWindow
        self._trader.app.top_window().click_input(button='right')
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
                ## break
            self._trader.wait(0.1)
            count -= 1
        # temp_path1 = tempfile.mktemp(suffix=".xls", dir=self.tmp_folder)
        random_str = ''.join(random.sample('abcdefghijklmnopqrstuvxyz', 5))

        temp_path = self.tmp_folder + r'\tmp' + datetime.now().strftime('%Y%m%d%H%M%S') + random_str + '.xls'
        self._set_foreground(self._trader.app.top_window())

        # alt+s保存，alt+y替换已存在的文件
        self._trader.app.top_window().Edit1.set_edit_text(temp_path)
        self._trader.app.top_window().type_keys("%{s}", set_foreground=False)
        # Wait until file save complete otherwise pandas can not find file
        self._trader.wait(0.2)
        # if self._trader.is_exist_pop_dialog():
        #     self._trader.app.top_window().Button2.click()
        #     self._trader.wait(0.2)

        return self._format_grid_data(temp_path)


class UniversalClientTrader(clienttrader.BaseLoginClientTrader):
    # grid_strategy = Xls
    grid_strategy = grid_strategies.Copy
    ths_app = None
    # grid_strategy.tmp_folder = r'D:\pythonProject\thstrader\easytrader\tmp'

    @property
    def broker_type(self):
        return "universal"

    def login1(self, user, password, exe_path, comm_password=None, **kwargs):
        """
        :param user: 用户名
        :param password: 密码
        :param exe_path: 客户端路径, 类似
        :param comm_password:
        :param kwargs:
        :return:
        """

        self._editor_need_type_keys = True
        try:
            self._app = pywinauto.Application().connect(path=self._run_exe_path(exe_path), timeout=2)
            # 'exists', 'visible', 'enabled', 'ready', 'active'
            # verify = self._app.window(title="网上股票交易系统5.0").wait('visible',1)
            # print(verify)
        # pylint: disable=broad-except
        except Exception as e:
            logger.error('错误：'+str(e))
            self.ths_app = pywinauto.Application().connect(path=r'D:\同花顺软件\同花顺\hexin.exe', timeout=2)
            ths_window = self.ths_app.window(title_re="同花顺(.*?)")
            if 'login_type' in kwargs.keys() and kwargs['login_type'] != '中信建投':
                ths_window.menu_select("交易->模拟炒股（M）")
                # logger.fatal(str(ths_window.PrintControlIdentifiers()))
            else:
                ths_window.menu_select("交易->中信建投")
                self.wait(2)
                desktop = pywinauto.Desktop()
                self._app = desktop['用户登录']
                while True:
                    try:
                        login_window = pywinauto.findwindows.find_window(title="用户登录", class_name='#32770')
                        break
                    except:
                        self.wait(0.1)

                self.wait(0.1)
                user_login_window = self._app.window(handle=login_window)
                # user_login_window = self._app.window()

                # yzm = user_login_window['验 证 码(&V):Static1']
                yzm = user_login_window.child_window(class_name="Static", best_match='验 证 码(&V):Static1')
                file_path = './tmp/tmp.png'
                yzm.capture_as_image().save(file_path)
                captcha_num = captcha_recognize(file_path).strip()  # 识别验证码
                captcha_num = "".join(captcha_num.split())
                logger.debug('登录验证码' + captcha_num)
                user_login_window.Edit1.set_focus()  # 获取账号输入框焦点
                user_login_window.Edit1.type_keys(user)  # 输入账号
                user_login_window.Edit2.set_focus()  # 获取密码输入框焦点
                user_login_window.Edit2.type_keys(password)  # 输入密码
                user_login_window.child_window(best_match='验 证 码(&V):Edit2').set_focus()
                user_login_window.child_window(best_match='验 证 码(&V):Edit2').type_keys(captcha_num)
                # print(user_login_window.PrintControlIdentifiers())
                self.wait(0.2)
                user_login_window.child_window(best_match='确定(&Y)Button').click_input()

            self.wait(4)
            self._app = pywinauto.Application().connect(path=self._run_exe_path(exe_path), timeout=3)

            self._close_prompt_windows()
        self._main = self._app.window(title="网上股票交易系统5.0")

    def login(self, user, password, exe_path, comm_password=None, **kwargs):
        """
        :param user: 用户名
        :param password: 密码
        :param exe_path: 客户端路径, 类似
        :param comm_password:
        :param kwargs:
        :return:
        """

        self._editor_need_type_keys = True
        try:
            command = r'runas /profile /savecred /user:desktop-i1u6b21\bthun D:\同花顺软件\同花顺\hexin.exe'
            subprocess.Popen(command, shell=True)
            self.wait(5)
            self.ths_app = pywinauto.Application().connect(path=r'D:\同花顺软件\同花顺\hexin.exe')

            handle = pywinauto.findwindows.find_window(title='网上股票交易系统5.0')
            # handle.wait("ready", 5)
            print(handle)
            logger.info('handle:'+handle)
            if handle == 0:
                logger.info('找不到窗口')
                raise Exception(f'找不到窗口')
            else:
                self._app = pywinauto.Application().connect(path=self._run_exe_path(exe_path), timeout=2)
        # pylint: disable=broad-except
        except Exception as e:
            logger.error('同花顺客户端启动错误：'+str(e))
            ths_window = self.ths_app.window(title_re="同花顺(.*?)")
            if 'login_type' in kwargs.keys() and kwargs['login_type'] != '中信建投':
                ths_window.menu_select("交易->模拟炒股（M）")
            else:
                ths_window.menu_select("交易->中信建投")
                self.wait(5)
                desktop = pywinauto.Desktop()
                self._app = desktop['用户登录']
                # self._app.wait("ready", 5)
                while True:
                    try:
                        login_window = pywinauto.findwindows.find_window(title="用户登录", class_name='#32770')
                        break
                    except:
                        self.wait(0.1)

                self.wait(0.1)
                user_login_window = self._app.window(handle=login_window)
                # yzm = user_login_window['验 证 码(&V):Static1']
                yzm = user_login_window.child_window(class_name="Static", best_match='验 证 码(&V):Static1')
                file_path = './tmp/tmp.png'
                yzm.capture_as_image().save(file_path)
                captcha_num = captcha_recognize(file_path).strip()  # 识别验证码
                captcha_num = "".join(captcha_num.split())
                logger.debug('登录验证码' + captcha_num)
                user_login_window.Edit1.set_focus()  # 获取账号输入框焦点
                user_login_window.Edit1.type_keys(user)  # 输入账号
                user_login_window.Edit2.set_focus()  # 获取密码输入框焦点
                user_login_window.Edit2.type_keys(password)  # 输入密码
                user_login_window.child_window(best_match='验 证 码(&V):Edit2').set_focus()
                user_login_window.child_window(best_match='验 证 码(&V):Edit2').type_keys(captcha_num)
                # print(user_login_window.PrintControlIdentifiers())
                self.wait(0.2)
                user_login_window.child_window(best_match='确定(&Y)Button').click_input()
                self.wait(5)
        try:
            self._app = pywinauto.Application().connect(path=self._run_exe_path(exe_path), timeout=3)
            # self._app.wait("ready", 5)
        except Exception as e:
            logger.error('pywinauto连接同花顺错误：' + str(e))
            return False

        self._close_prompt_windows()
        self._main = self._app.window(title="网上股票交易系统5.0")
        logging.info('login函数登录成功')
        return True

    def login3(self, user, password, exe_path, comm_password=None, **kwargs):
        """
        独立下单登录
        :param user: 用户名
        :param password: 密码
        :param exe_path: 客户端路径, 类似
        :param comm_password:
        :param kwargs:
        :return:
        """

        self._editor_need_type_keys = True
        try:
            handle = pywinauto.findwindows.find_window(title='网上股票交易系统5.0')
            print('句柄',handle)
            if handle == 0:
                raise Exception(f'找不到窗口')
            else:
                self._app = pywinauto.Application().connect(path=self._run_exe_path(exe_path), timeout=2)

            # print('self._run_exe_path(exe_path)')
            # 'exists', 'visible', 'enabled', 'ready', 'active'
            # verify = self._app.window(title="网上股票交易系统5.0").wait('visible',1)
            # print(verify)
        # pylint: disable=broad-except
        except Exception as e:
            logger.error('错误：'+str(e))
            command = f'runas /profile /savecred /user:desktop-i1u6b21\\bthun '+self._run_exe_path(exe_path)
            subprocess.Popen(command, shell=True)
            self.wait(2)
            self._app = pywinauto.Application().connect(path=self._run_exe_path(exe_path))

            while True:
                try:
                    login_window = pywinauto.findwindows.find_window(title="用户登录", class_name='#32770')
                    break
                except:
                    self.wait(0.1)

            self.wait(0.1)
            user_login_window = self._app.window(handle=login_window)
            # user_login_window = self._app.window()

            # yzm = user_login_window['验 证 码(&V):Static1']
            yzm = user_login_window.child_window(class_name="Static", best_match='验 证 码(&V):Static1')
            file_path = './tmp/tmp.png'
            yzm.capture_as_image().save(file_path)
            captcha_num = captcha_recognize(file_path).strip()  # 识别验证码
            captcha_num = "".join(captcha_num.split())
            logger.debug('登录验证码' + captcha_num)
            user_login_window.Edit1.set_focus()  # 获取账号输入框焦点
            user_login_window.Edit1.type_keys(user)  # 输入账号
            user_login_window.Edit2.set_focus()  # 获取密码输入框焦点
            user_login_window.Edit2.type_keys(password)  # 输入密码
            user_login_window.child_window(best_match='验 证 码(&V):Edit2').set_focus()
            user_login_window.child_window(best_match='验 证 码(&V):Edit2').type_keys(captcha_num)
            # print(user_login_window.PrintControlIdentifiers())
            self.wait(0.2)
            user_login_window.child_window(best_match='确定(&Y)Button').click_input()
            self.wait(6)
        try:
            self._app = pywinauto.Application().connect(path=self._run_exe_path(exe_path), timeout=3)
        except Exception as e:
            logger.error('pywinauto连接同花顺错误：' + str(e))
            return {'msg': 'login fail', 'error': str(e)}, False
            pass
        self._close_prompt_windows()
        self._main = self._app.window(title="网上股票交易系统5.0")
        return {'msg': 'login True', 'error': ''}, True


    def hangqing(self, name='行情->债券->可转债'):
        self._main.minimize()
        window = self.ths_app.window(title_re="同花顺(.*?)")
        window.wait("ready", 2)
        left = window.rectangle().left
        top = window.rectangle().top

        if name.startswith('BK'):
            pywinauto.keyboard.send_keys(name)
            pywinauto.keyboard.send_keys("{ENTER}")
            time.sleep(0.5)
            pass
        else:
            try:
                path = name
                # path = '行情->债券->可转债'
                # path = '行情->外汇->基本汇率\t800'
                window.menu_select(path, exact=True)
            except Exception as e:
                print(e)
        # 66944 同花顺主窗口 股票复制识别 67370
        window.click_input(button='right', coords=(left+439, top+198))
        right_menu = pywinauto.Desktop(backend='uia')['上下文Menu']

        export_window = right_menu.child_window(title="数据导出", control_type="MenuItem")

        export_window.click_input()
        time.sleep(0.1)
        item_left = export_window.rectangle().left
        item_top = export_window.rectangle().top

        pywinauto.mouse.click(button='left', coords=(item_left+284, item_top+30))

        curr_path = os.getcwd()
        file_path = curr_path+r'\table.xls'
        time.sleep(0.5)
        save_window = self.ths_app.top_window()
        time.sleep(0.5)
        save_window.Edit0.type_keys(file_path)
        time.sleep(0.5)
        pywinauto.keyboard.send_keys("%{N}")
        time.sleep(0.5)
        pywinauto.keyboard.send_keys("%{N}")
        time.sleep(0.5)
        pywinauto.keyboard.send_keys("{ENTER}")
        time.sleep(2)
        # pd.set_option('display.max_columns',None)
        data = pd.read_csv(file_path, delimiter='\t', encoding='gbk')
        self._main.maximize()
        return data

        pass


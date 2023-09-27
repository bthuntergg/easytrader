import pywinauto
import easytrader
from easytrader.utils.stock import get_today_ipo_data
import time
#
#
user = easytrader.use('universal_client')
user.enable_type_keys_for_editor()
# # 'D:\同花顺软件\同花顺\xiadan.exe' 同花顺模拟
# # "D:\Program Files\weituo\中信建投\xiadan.exe"  #独立委托
# user.prepare(user='123123', password='123123', exe_path="D:\\pythonProject\\中信建投\\xiadan.exe", login_type='moni')
user.prepare(user='123123', password='123123', exe_path="D:\\同花顺软件\\同花顺\\xiadan.exe", login_type='moni')
# print('用户持仓',user.position)
# print('用户资金',user.balance)

# user.grid_strategy_instance.tmp_folder = r'D:\pythonProject\ths\tmp'
# # user.login(user='',password='',exe_path=r'D:\Program Files\weituo\中信建投\xiadan.exe')   #委托管理地址
# user.connect(r'D:\同花顺软件\同花顺\xiadan.exe')

# user.prepare(user='123',password='123',exe_path=r'D:\同花顺软件\同花顺\xiadan.exe')

print(user.hangqing('BK233'))



#
# user.buy('113534', price='253.94', amount=10)
# result=user.buy('601318', price='47.40', amount=100)
# print(result)
# user.buy('000002', price='15.1123', amount=100)
# print('当日成交',user.today_trades)

# print(user.today_entrusts)
# #
# #
# ipo_data = get_today_ipo_data()
# print(ipo_data)
#
#
# user.refresh()

# app=pywinauto.Application().start(cmd_line=r'runas /profile /savecred  /user:desktop-i1u6b21\bthun D:/同花顺软件/同花顺/hexin.exe')
# app=pywinauto.Application().start(r'D:/同花顺软件/同花顺/hexin.exe')
# app = pywinauto.Application().connect(path=r'D:\同花顺软件\同花顺\xiadan.exe', timeout=2)
# print(111,dir(app))
# # win1=app.window(title_re="同花顺(.*?)")
# win=app.window(process=app.process)
# print(222,win)


# import subprocess
# from pywinauto import Application
#
# # 创建一个辅助进程以管理员权限运行目标程序
# # program_path = "D:\\同花顺软件\\同花顺\\xiadan.exe"
# # program_path = "D:\\同花顺软件\\同花顺\\hexin.exe"
# program_path = "D:/Program Files/weituo/中信建投/xiadan.exe"  #独立委托
# def run_as_admin():
#
#
#     # 使用 subprocess 和 runas 参数以管理员身份运行命令
#     command = f'runas /profile /savecred  /user:desktop-i1u6b21\\bthun "{program_path}"'
#     subprocess.Popen(command, shell=True)
#     time.sleep(3)
#
# # 连接到管理员权限下运行的应用程序
# def connect_to_program():
#     app = Application(backend="uia")
#     app.connect(path=program_path)
#     print(app.top_window().print_control_identifiers())
#     # 在这里进行与应用程序的交互
#
# # 在主程序中调用函数
# if __name__ == "__main__":
#     run_as_admin()
#     connect_to_program()
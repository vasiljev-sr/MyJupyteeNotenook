import sys
from PyQt5.QtWidgets import QApplication,QMainWindow, QSizePolicy, QVBoxLayout, QMessageBox
from PyQt5.QtCore import QRect, QPropertyAnimation, QThread, QTimer
from PyQt5 import QtGui,QtCore
from PyQt5 import QtGui
from AppMainWindow import Ui_MainWindow
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
import matplotlib.pyplot as plt
import matplotlib as mpl
from machine_statistics import MachineStatistics
from matplotlib import rc
import time
import threading

mach_stat = MachineStatistics()
class MyMplCanvas(FigureCanvasQTAgg):
    def __init__(self,fig,parent=None):
        self.fig = fig
        FigureCanvasQTAgg.__init__(self,self.fig)
        FigureCanvasQTAgg.setSizePolicy(self, QSizePolicy.Expanding, QSizePolicy.Expanding)
        FigureCanvasQTAgg.updateGeometry(self)

def plot():
    plt.rcParams['figure.facecolor'] = '#2d2d2d'
    plt.rcParams['legend.frameon'] = 'False'
    mpl.rcParams['axes.facecolor'] = 'ffffff'
    mpl.rcParams['font.size'] = 10

    fig, ((ax1, ax2, ax3), (ax4, ax5, ax6)) = plt.subplots(2, 3)
    plt.subplots_adjust(wspace=0.5, hspace=0.5)
    plt.axis('off')
    ax = [ax1, ax2, ax3, ax4, ax5,ax6]
    for axes in ax:
        axes.set_axis_off()

    return fig, ax


def canvas_for_prev_plot(parent= None):
    parent.prev_fig, parent.prev_ax = plot()
    parent.componovka_for_mpl = QVBoxLayout(parent.prev_plot_widget)
    parent.canvas = MyMplCanvas(parent.prev_fig)
    parent.componovka_for_mpl.addWidget(parent.canvas)

def canvas_for_curr_plot(parent= None):
    parent.curr_fig, parent.curr_ax = plot()
    parent.componovka_for_mpl = QVBoxLayout(parent.curr_plot_widget)
    parent.canvas = MyMplCanvas(parent.curr_fig)
    parent.componovka_for_mpl.addWidget(parent.canvas)

def canvas_for_selected_plot(parent= None):
    parent.select_fig, parent.select_ax = plot()
    parent.componovka_for_mpl = QVBoxLayout(parent.selected_plot_widget)
    parent.canvas = MyMplCanvas(parent.select_fig)
    parent.componovka_for_mpl.addWidget(parent.canvas)


class ParamsThread(QThread):
    params = mach_stat.read_database_params()
    ves = params[0:5]
    vlazh = params[5:10]
    speed = params[10:]
    time_value = 5
    def __init__(self):
        QThread.__init__(self)

    def run(self):
        while True:
            self.params = mach_stat.read_database_params()
            self.ves = self.params[0:5]
            self.vlazh = self.params[5:10]
            self.speed = self.params[10:]
            print(self.time_value)
            time.sleep(self.time_value)

class PlotTread(QThread):
    def __init__(self,mainwindow, parent=None):
        super().__init__()
        self.mw = mainwindow

    def run(self):
        data = list(zip(self.mw.curr_ax[0:5], mach_stat.machines_id.keys()))
        for ax, id in data:
            plot_df = mach_stat.curr_mon_date(id_num=id)
            explode = (0.1, 0)
            vals = plot_df['секунды']
            ax.clear()
            ax.pie(vals, autopct='%1.1f%%', shadow=False,
                   explode=explode,
                   rotatelabels=True,
                   colors=('#ff5533', 'w'),
                   pctdistance=0.65,
                   textprops=dict(color="black"),
                   radius=1.5)
            ax.set_title('OM' + str(id), color='w', loc='right', pad=10)

        self.mw.curr_ax[5].text(0.05, 0.5, 'Время простоя', color='#ff5533', fontsize=14)
        self.mw.curr_ax[5].text(0.05, 0.7, 'Время работы ', color='w', fontsize=14)

        self.mw.curr_fig.canvas.draw()


class MainWindow(QMainWindow,Ui_MainWindow):
    #my_signal = QtCore.pyqtSignal(list, name='my_signal')
    def __init__(self):
        QMainWindow.__init__(self)
        self.setupUi(self)
        self.btn_functions()
        self.date_in.setDate(QtCore.QDate.currentDate())
        self.date_out.setDate(QtCore.QDate.currentDate())
        canvas_for_curr_plot(parent=self)
        canvas_for_prev_plot(parent=self)
        canvas_for_selected_plot(parent=self)
        self.params = ParamsThread()
        self.params.start()
        self.show_params()
        self.timer = QTimer()
        self.timer.timeout.connect(self.show_params)
        self.timer.start(1000)
        self.time_slider.valueChanged.connect(self.update_time)
        self.plot = PlotTread(mainwindow=self)

        #self.signal = QtCore.pyqtSignal(list, name='my_signal')

        #self.my_signal.connect(self.mySignalHandler, QtCore.Qt.QueuedConnection)

    def update_time(self, value):
        self.params.time_value = value
        self.update_freq.setText('Частота обновления: '+ str(value))

    def btn_functions(self):
        # кнопки перехода между страницами
        self.btn_cur_mon.clicked.connect(lambda: self.Pages_Widjet.setCurrentWidget(self.curr_mon_page))
        self.btn_prev_mon.clicked.connect(lambda: self.Pages_Widjet.setCurrentWidget(self.prev_mon_page))
        self.btn_select_date.clicked.connect(lambda: self.Pages_Widjet.setCurrentWidget(self.selected_data_page))
        self.btn_params.clicked.connect(lambda: self.Pages_Widjet.setCurrentWidget(self.params_page))
        # self.btn__select_date.clicked.connect()
        # кнопки обновления страниц
        self.update_curr_mon.clicked.connect(lambda: self.plot.start())
        self.update_prev_mon.clicked.connect(self.show_prev_mon_plots)
        self.update_selected_date.clicked.connect(self.show_selected_date_plot)
        # self.update_params_page.clicked.connect(lambda : self.show_params(self.params.ves,
        #                                                                   self.params.vlazh,
        #                                                                   self.params.speed))
        #кнопка меню
        self.btn_toggle.clicked.connect(lambda: self.toggleMenu(170, True))


    def toggleMenu(self, maxWidth, enable):
        if enable:

            # получаем значение Width
            width = self.frame_left_menu.width()
            maxExtend = maxWidth
            standart = 50

            # задаем макс значание width
            if width == 50:
                widthExtend = maxExtend
            else:
                widthExtend = standart

            # анимация
            self.animation = QPropertyAnimation(self.frame_left_menu, b'minimumWidth')
            self.animation.setDuration(200)
            self.animation.setStartValue(width)
            self.animation.setEndValue(widthExtend)
            self.animation.setEasingCurve(QtCore.QEasingCurve.InOutQuart)
            self.animation.start()

    def show_curr_mon_plots(self):

        data = list(zip(self.curr_ax[0:5], mach_stat.machines_id.keys()))
        for ax, id in data:
            plot_df = mach_stat.curr_mon_date(id_num=id)
            explode = (0.1, 0)
            vals = plot_df['секунды']
            ax.clear()
            ax.pie(vals, autopct='%1.1f%%', shadow=False,
                   explode=explode,
                   rotatelabels=True,
                   colors=('#ff5533', 'w'),
                   pctdistance=0.65,
                   textprops=dict(color="black"),
                   radius=1.5)
            ax.set_title('OM'+str(id), color='w', loc='right',pad = 10)

        self.curr_ax[5].text(0.05, 0.5,'Время простоя', color = '#ff5533',fontsize = 14)
        self.curr_ax[5].text(0.05, 0.7, 'Время работы ', color='w', fontsize=14)

        self.curr_fig.canvas.draw()

    def show_prev_mon_plots(self):

        data = list(zip(self.prev_ax, mach_stat.machines_id.keys()))
        for ax, id in data:
            plot_df = mach_stat.prev_mon_date(id_num=id)
            explode = (0.1, 0)
            vals = plot_df['секунды']
            ax.clear()
            ax.pie(vals, autopct='%1.1f%%', shadow=False,
                   explode=explode,
                   rotatelabels=True,
                   colors=('#ff5533', 'w'),
                   pctdistance=0.65,
                   textprops=dict(color="black"),
                   radius=1.5)
            ax.set_title('OM'+str(id), color='w', loc='right',pad = 10)
        self.prev_ax[5].text(0.05, 0.5, 'Время простоя', color='#ff5533', fontsize=14)
        self.prev_ax[5].text(0.05, 0.7, 'Время работы ', color='w', fontsize=14)
        self.prev_fig.canvas.draw()

    def show_selected_date_plot(self):
        date_in = self.date_in.dateTime().toString('yyyy-MM-dd 00:00:00')
        date_out = self.date_out.dateTime().toString('yyyy-MM-dd 23:59:59')
        if date_in > date_out:
            invalid_date = QMessageBox()
            invalid_date.setWindowTitle('Ошибка')
            invalid_date.setText('Невозможно отобразить диаграммы! \nНачальная дата больше, чем конечная.')
            invalid_date.setIcon(QMessageBox.Warning)
            invalid_date.setStandardButtons(QMessageBox.Ok| QMessageBox.Cancel)

            invalid_date.exec_()
        elif self.date_in.date().month() > mach_stat.today.month or self.date_out.date().month() > mach_stat.today.month:
            print(self.date_in.date().month())
            print(self.date_out.date().month())
            print(mach_stat.today.month)
            invalid_date = QMessageBox()
            invalid_date.setWindowTitle('Ошибка')
            invalid_date.setText('Невозможно отобразить диаграммы! \nУказанная дата выходит за пределы текущей даты.')
            invalid_date.setIcon(QMessageBox.Warning)
            invalid_date.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)

            invalid_date.exec_()
        else:
            data = list(zip(self.select_ax, mach_stat.machines_id.keys()))
            for ax, id in data:
                plot_df = mach_stat.selected_date(date_in, date_out, id_num=id)
                print(plot_df)
                explode = (0.1, 0)
                vals = plot_df['секунды']
                ax.clear()
                ax.pie(vals, autopct='%1.1f%%', shadow=False,
                       explode=explode,
                       rotatelabels=True,
                       colors=('#ff5533', 'w'),
                       pctdistance=0.65,
                       textprops=dict(color="black"),
                       radius=1.5)
                ax.set_title('OM' + str(id), color='w', loc='right', pad=10)
            self.select_ax[5].text(0.05, 0.5, 'Время простоя', color='#ff5533', fontsize=14)
            self.select_ax[5].text(0.05, 0.7, 'Время работы ', color='w', fontsize=14)
            self.select_fig.canvas.draw()

    def show_params(self):

        ves_labels = [self.om1_ves,self.om2_ves,self.om4_ves,self.om5_ves,self.om6_ves]
        ves = self.params.ves
        for value, label in list(zip(ves, ves_labels )):
            label.setText('Вес: ' + str(value)+ ' гр/м2')

        vlazh = self.params.vlazh
        vlazh_labels = [self.om1_vlazh, self.om2_vlazh, self.om4_vlazh, self.om5_vlazh, self.om6_vlazh]
        for value, label in list(zip(vlazh, vlazh_labels )):
            label.setText('Влажность: ' + str(value)+ ' %')

        speed = self.params.speed
        speed_labels = [self.om1_speed, self.om2_speed, self.om4_speed, self.om5_speed, self.om6_speed]
        for value, label in list(zip(speed, speed_labels)):
            label.setText('Скорость: ' + str(value)+ ' м/мин')


def main_application():
    app = QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())

if __name__ == '__main__':

    main_application()


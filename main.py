import sys
from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QMessageBox
from PyQt5.QtCore import QTimer, QDate, QTime, QEvent
from PyQt5.QtGui import QPalette, QColor, QIcon
from UI_files.design_list_1 import Ui_MainWindow
from UI_files.design_list_2 import Ui_SettingWindow
import pyqtgraph as pg
import numpy as np
import random
from pyedflib import highlevel
import os


class Project(QMainWindow, Ui_MainWindow):
    def __init__(self, settings_window, dpiX, dpiY):
        self.dpi_x = dpiX  # Устанавливаем dpi по горизонтали
        self.dpi_y = dpiY  # Устанавливаем dpi по вертикали
        self.graph_px_height = 139  # Размер одного графика по y в пикселях
        # (при изменении размеров виджета надо перерассчитать вручную - dpi и линейка в помощь)
        self.graph_px_width = 833  # Размер одного графика по x в пикселях
        # (при изменении размеров виджета надо перерассчитать вручную - dpi и линейка в помощь)
        self.inch_to_mm = 25.4  # Константа для перевода дюймов в мм
        self.y_mm_size = (self.graph_px_height / self.dpi_y) * self.inch_to_mm  # Размер границ одного графика в мм по y
        self.x_mm_size = (self.graph_px_width / self.dpi_x) * self.inch_to_mm  # Размер границ одного графика в мм по x

        self.update_frequency = 10  # Период обновления графиков в миллисекундах
        self.x_diapason = 5000  # Диапозон значений по x для отображения
        self.y_diapason = 10000  # Диапозон значений по y для отображения
        self.start = 0  # Значение начала видимой границы по x
        self.end = self.x_diapason  # Значение конца видимой границы по x
        self.curr_x_data = np.array([0])  # Список для хранения данных по x
        self.curr_y_data = np.random.randint(-self.y_diapason // 2, self.y_diapason // 2, 1)  # Список
        # для хранения данных по y

        self.channel_names = ['F3-C3', 'P3-Po3', 'P4-Po4']  # Имена каналов
        self.signal_headers = highlevel.make_signal_headers(self.channel_names,
                                                            sample_rate=1 // (self.update_frequency / 1000),
                                                            physical_max=500000, physical_min=-500000)  # Создание
        # заголовков для записи данных в edf
        self.data_from_states_to_save = [[[] for __ in range(3)] for _ in range(6)]  # Контейнер для записи данных со всех state
        self.states = [False for _ in range(6)]  # Контейнер состояний кнопок state

        super(Project, self).__init__()  # Перегружаем класс
        self.setupUi(self)  # Подгружаем дизайн
        self.initUI()  # Инициализация UI виджетов
        self.create_folder_for_records()

        self.combobox_uV_mm_data = [int(self.y_scale_combo_box.itemText(ind).split()[0]) for ind in   # Считываем данные
                                    range(self.y_scale_combo_box.count())]  # с левого выпадающего списка
        self.combobox_mm_sec_data = [int(self.x_scale_combo_box.itemText(ind).split()[0]) for ind in  # Считываем данные
                                     range(self.x_scale_combo_box.count())]  # c правого выдапающего списка
        self.add_current_xy_scale()

    def initUI(self):
        self.settings_window = settings_window  # Записываем экземпляр класса окна настроек
        self.setWindowIcon(QIcon('icons/Main window icon.png'))
        self.setFixedSize(self.size())

        pg.setConfigOptions(antialias=False)  # Конфигурация внутренних переменных pyqtgraph
        self.graph_widget = pg.GraphicsLayoutWidget()  # Конейнер для графиков
        self.graph_layout.addWidget(self.graph_widget)  # Добавления виджета для графиков в layout

        self.plot_1 = self.graph_widget.addPlot()  # Инициализация нового графика
        self.plot_1.setXRange(self.start, self.end)   # Установка границ отрисовки по x
        self.plot_data = self.plot_1.plot([], pen='g')  # Объект, хранящий и рисующий данные графика
        # self.plot_1.addLegend() # Можно добавить легенду
        self.plot_1.showAxis('bottom', show=False)  # Убираем ось X
        self.plot_1.showAxis('left', show=False)  # Убираем ось Y
        self.plot_1.hideButtons()  # Скрываем доп. кнопки
        self.graph_widget.nextRow()  # Переход указателя для след. графика под текущий график

        self.plot_2 = self.graph_widget.addPlot()  # Инициализация нового графика
        self.plot_2.setXRange(self.start, self.end)
        self.plot_data2 = self.plot_2.plot([], pen='g')
        # self.plot_2.addLegend() # Можно добавить легенду
        self.plot_2.showAxis('bottom', show=False)
        self.plot_2.showAxis('left', show=False)
        self.plot_2.hideButtons()
        self.graph_widget.nextRow()

        self.plot_3 = self.graph_widget.addPlot()  # Инициализация нового графика
        self.plot_3.setXRange(self.start, self.end)
        self.plot_data3 = self.plot_3.plot([], pen='g')
        # self.plot_3.addLegend() # Можно добавить легенду
        self.plot_3.showAxis('bottom', show=False)
        self.plot_3.showAxis('left', show=False)
        self.plot_3.hideButtons()
        self.graph_widget.nextRow()

        self.y_scale_combo_box.currentTextChanged.connect(self.change_y_scale)  # Подключаем обработчики событий для
        self.x_scale_combo_box.currentTextChanged.connect(self.change_x_scale)  # выпад. списков

        # -----------Настройки кнопок------------
        self.connectButton.clicked.connect(self.connect)

        self.state_1.clicked.connect(self.write_data)
        self.state_2.clicked.connect(self.write_data)
        self.state_3.clicked.connect(self.write_data)
        self.state_4.clicked.connect(self.write_data)
        self.state_5.clicked.connect(self.write_data)
        self.state_6.clicked.connect(self.write_data)

        self.state_1.setAutoFillBackground(True)
        self.state_2.setAutoFillBackground(True)
        self.state_3.setAutoFillBackground(True)
        self.state_4.setAutoFillBackground(True)
        self.state_5.setAutoFillBackground(True)
        self.state_6.setAutoFillBackground(True)

        self.runRecognitionButton.clicked.connect(self.run_recognition)

        self.midiSettButton.clicked.connect(self.open_midi_settings_window)

        self.runMidiButtom.clicked.connect(self.run_midi)

        self.devSettButton.clicked.connect(self.open_device_settings)
        # -----------Настройки кнопок------------

        self.state_button_palett = QPalette()  # Инициализация палитры

        self.date = QDate()  # Инициализация объектов для даты
        self.time = QTime()  # и времени

        self.close_event_message_box = QMessageBox()  # Инициализация и настройка инф. окна при закрытии приложения
        self.close_event_message_box.setWindowTitle('Warning')
        self.close_event_message_box.setText('Save states?')
        self.close_event_message_box.setIcon(QMessageBox.Question)
        self.close_event_message_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        self.close_event_message_box.setWindowIcon(QIcon('icons/Message icon.png'))

    # -------------Функции масштабирования-------------------
    def add_current_xy_scale(self):  # Функция, добавляющая текущий масштаб в выпадающие списки
        curr_scale_y = round(self.y_diapason / self.y_mm_size)  # Расcчитываем текущий масштаб для вертикали
        self.combobox_uV_mm_data.append(curr_scale_y)  # Добавляем данные в список значений выпадающего списка
        self.combobox_uV_mm_data.sort()
        self.y_scale_combo_box.insertItem(self.combobox_uV_mm_data.index(curr_scale_y), f'{curr_scale_y} uV/mm(default)')
        # Добавляем в y_scale_combobox
        self.y_scale_combo_box.setCurrentIndex(self.combobox_uV_mm_data.index(curr_scale_y))

        curr_scale_x = round(self.x_mm_size / self.x_diapason * 1000)  # Расчитываем
        # текущий масштаб для горизонтали
        self.combobox_mm_sec_data.append(curr_scale_x)  # Добавляем данные в список значений выпадающего списка
        self.combobox_mm_sec_data.sort()
        self.x_scale_combo_box.insertItem(self.combobox_mm_sec_data.index(curr_scale_x),
                                          f'{curr_scale_x} mm/sec(default)')  # Добавляем в x_scale_combobox
        self.x_scale_combo_box.setCurrentIndex(self.combobox_mm_sec_data.index(curr_scale_x))

    def change_y_scale(self):  # Функция для перерасчета масштаба по Y
        value = int(self.y_scale_combo_box.currentText().split()[0])  # Получаем масштаб в uV/mm
        self.y_diapason = value * self.y_mm_size
        self.plot_1.setYRange(-self.y_diapason // 2, self.y_diapason // 2)
        self.plot_2.setYRange(-self.y_diapason // 2, self.y_diapason // 2)
        self.plot_3.setYRange(-self.y_diapason // 2, self.y_diapason // 2)

    def change_x_scale(self):  # Функция для перерасчета масштаба по X
        value = int(self.x_scale_combo_box.currentText().split()[0])  # Получаем масштаб в mm/sec
        self.x_diapason = 1000 * self.x_mm_size / value
        self.start = self.end - self.x_diapason
        self.plot_1.setXRange(self.start, self.end)
        self.plot_2.setXRange(self.start, self.end)
        self.plot_3.setXRange(self.start, self.end)
    # -------------Функции масштабирования-------------------

    # -------------Обработчики кнопок------------------------
    def connect(self):
        for widget in self.findChildren(QWidget):
            widget.setEnabled(True)

        timer = QTimer(self)
        timer.setInterval(self.update_frequency)
        timer.start()
        timer.timeout.connect(self.update_graph)

    def write_data(self):
        if self.sender().palette().color(QPalette.Button) == QColor(0, 0, 0):  # Устанавливаем цвет обводки
            # ненажатой кнопки и далее заканчиваем запись файла
            self.state_button_palett.setColor(self.state_button_palett.Button, QColor(255, 255, 255))
            self.sender().setPalette(self.state_button_palett)
            self.save_state(self.sender().text())
        else:
            self.state_button_palett.setColor(self.state_button_palett.Button, QColor(0, 0, 0))  # Устанавливаем цвет
            # обводки нажатой кнопки и далее начинаем записывать файл
            self.sender().setPalette(self.state_button_palett)
            self.states[int(self.sender().text().split()[-1]) - 1] = True

    def run_recognition(self):
        pass

    def open_midi_settings_window(self):
        self.settings_window.show()

    def run_midi(self):
        pass

    def open_device_settings(self):
        pass

    # ----------Обработчики кнопок-----------

    # ------------Работа с сохраняемыми файлами-------------
    def create_folder_for_records(self):  # Фунция для создания папки с записями
        if not os.path.exists('Records'):  # Если папки со всеми папками для записей нет, создаем
            os.mkdir('Records')
        self.records_folder_name = f'Records({self.date.currentDate().toPyDate()}' \
                                   f' {self.time.currentTime().toString().split(".")[0].replace(":", ".")})'
        self.num_of_files = 0  # Счетчик количества файлов
        os.mkdir(f'Records/{self.records_folder_name}')

    def check_folder_content(self):  # Функция удаляющая папку с записями, если она пуста
        if self.num_of_files == 0:
            os.rmdir(f'Records/{self.records_folder_name}')

    def save_state(self, button_name):  # Функция для сохранения файла в edf
        self.states[int(button_name.split()[-1]) - 1] = False
        self.num_of_files += 1
        highlevel.write_edf(f'Records/{self.records_folder_name}/record'
                            f' {self.num_of_files}.edf',
                            np.array(self.data_from_states_to_save[int(button_name.split()[-1]) - 1]),
                            self.signal_headers)  # Запись данных
        self.data_from_states_to_save[int(button_name.split()[-1]) - 1] = [[], [], []]  # Очищаем контейнер

    def check_states(self):
        for num, state in enumerate(self.states):  # Проверяем состояния кнопок state
            if state is True:  # Если идет запись, то добавляем последние данные в список для записи в edf
                self.data_from_states_to_save[num][0].append(self.curr_y_data[-1])
                self.data_from_states_to_save[num][1].append(self.curr_y_data[-1])
                self.data_from_states_to_save[num][2].append(self.curr_y_data[-1])
    # ------------Работа с сохраняемыми файлами-------------

    # ------------Работа с графиками-------------
    def get_data(self):
        # Нужно дописать подключение к C++ коду сюда
        self.curr_x_data = list(self.curr_x_data)
        self.curr_x_data.append(self.curr_x_data[-1] + self.update_frequency)  # Добавляем значение по X

        self.curr_y_data = list(self.curr_y_data)
        self.curr_y_data.append(random.randint(-self.y_diapason // 2, self.y_diapason // 2))  # Добавляем значение по Y

    def update_graph(self):
        self.get_data()  # Получаем новые данные

        if self.curr_x_data[-1] >= self.end:  # Если дошли до границы self.end, начинаем перемещаться по оси X
            self.start += self.update_frequency  # Равномерно продвигаем
            self.end += self.update_frequency  # границу
            self.plot_1.setXRange(self.start, self.end)  # Устанавливаем новые границы
            self.plot_2.setXRange(self.start, self.end)  # для
            self.plot_3.setXRange(self.start, self.end)  # графиков

        if len(self.curr_y_data) > 15000:  # Устанавливаем лимит на количество данных графика в массивe
            self.curr_y_data = self.curr_y_data[1:]
            self.curr_x_data = self.curr_x_data[1:]

        self.check_states()  # Проверяем состояние кнопок state

        self.curr_x_data = np.array(self.curr_x_data)

        self.curr_y_data = np.array(self.curr_y_data)

        self.add_value_on_graph(self.curr_x_data, self.curr_y_data)  # Обновляем график

    def add_value_on_graph(self, x, y):  # Установка значений на графики
        self.plot_data.setData(x, y)
        self.plot_data2.setData(x, y)
        self.plot_data3.setData(x, y)
    # ------------Работа с графиками-------------

    # ----------------Глобальные события-----------------
    def closeEvent(self, event):
        if any(self.states):  # Если на каком-то state идет запись
            response = self.close_event_message_box.exec()
            if response == QMessageBox.Yes:
                for ind, state in enumerate(self.states):
                    if state:
                        self.save_state(f'State {ind + 1}')
        self.check_folder_content()  # Проверяем наличие содержимого в папке с записями
        self.settings_window.close()  # Закрываем окно настроек

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Wheel:
            return True
        return super(QMainWindow, self).eventFilter(obj, event)
    # ----------------Глобальные события-----------------


class SettingsWindow(QMainWindow, Ui_SettingWindow):
    def __init__(self):
        super(SettingsWindow, self).__init__()  # Перегружаем класс
        self.setupUi(self)  # Подгружаем дизайн
        self.initUI()

    def initUI(self):
        self.setWindowIcon(QIcon('icons/Setting window icon.png'))  # Задаем иконку приложения

        # Настройка кнопок
        self.detectMIDIButton.clicked.connect(self.midi_detect)

        self.connectButton.clicked.connect(self.connect_it)

        self.stateButton_1.clicked.connect(self.state_1)
        self.stateButton_2.clicked.connect(self.state_2)
        self.stateButton_3.clicked.connect(self.state_3)
        self.stateButton_4.clicked.connect(self.state_4)
        self.stateButton_5.clicked.connect(self.state_5)
        self.stateButton_6.clicked.connect(self.state_6)

        self.alphaButton.clicked.connect(self.alpha)
        self.bettaButton.clicked.connect(self.betta)

        self.spaceXButton.clicked.connect(self.space_x)
        self.spaceYButton.clicked.connect(self.space_y)

        self.meanStateButton.clicked.connect(self.mean_state)

        self.buttonWay_1_2.clicked.connect(self.way_1_2)
        self.buttonWay_2_1.clicked.connect(self.way_2_1)
        self.buttonWay_1_3.clicked.connect(self.way_1_3)
        self.buttonWay_3_1.clicked.connect(self.way_3_1)
        self.buttonWay_2_3.clicked.connect(self.way_2_3)
        self.buttonWay_3_2.clicked.connect(self.way_3_2)

        # Настройка вып. списка
        self.devicesComboBox.currentTextChanged.connect(self.combo_box_text_changed)

    def midi_detect(self):
        pass

    def connect_it(self):
        pass

    def state_1(self):
        pass

    def state_2(self):
        pass

    def state_3(self):
        pass

    def state_4(self):
        pass

    def state_5(self):
        pass

    def state_6(self):
        pass

    def alpha(self):
        pass

    def betta(self):
        pass

    def space_x(self):
        pass

    def space_y(self):
        pass

    def mean_state(self):
        pass

    def way_1_2(self):
        pass

    def way_2_1(self):
        pass

    def way_1_3(self):
        pass

    def way_3_1(self):
        pass

    def way_2_3(self):
        pass

    def way_3_2(self):
        pass

    def combo_box_text_changed(self):
        pass


if __name__ == '__main__':
    app = QApplication(sys.argv)
    dpi_x = app.desktop().physicalDpiX()
    dpi_y = app.desktop().physicalDpiY()
    settings_window = SettingsWindow()  # Инициализация окна с настройками
    main_window = Project(settings_window, dpi_x, dpi_y)  # Инициализация основного окна
    main_window.show()
    app.installEventFilter(main_window)
    app.exec()

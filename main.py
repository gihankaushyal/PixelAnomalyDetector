# imports
import h5py
import numpy as np
from PyQt5.QtWidgets import *
import pyqtgraph as pg
from PyQt5 import uic
import sys


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        uic.loadUi("mainWindow.ui", self)

        # connecting elements to functions
        self.browseButton.clicked.connect(self.browseFiles)
        self.sortButton.clicked.connect(lambda: self.sortFrames(self.fileField.text()))
        self.advanceSortButton.clicked.connect(lambda: self.advanceSortFrames(self.fileField.text()))
        # button and input line for calling plotCurves() method to plot vertically average intensity profile for the
        # panel
        self.plotPixelIntensityButton.clicked.connect(lambda: self.plotCurve(self.fileField.text(),
                                                                             self.eventNumber.text()))
        # button for call the fit_curve() method to fit a 4th order polynomial for
        # the vertically average intensity profile
        self.fitPolynormialButton.clicked.connect(lambda: self.plotFit(self.fileField.text(), self.eventNumber.text()))
        # button for calling plot_max_pixels() method to plot the pixel with the highest intensity for all
        # the frames of the
        self.plotPeakPixelButton.clicked.connect(lambda: self.plotMaxPixels(self.fileField.text()))

        # graphing
        self.graphWidget = pg.PlotWidget()
        self.layout = QHBoxLayout()
        self.layout.addWidget(self.graphWidget)
        self.graphingSpace.setLayout(self.layout)

        self.setWindowTitle("Detector Analyser")
        self.show()

    def browseFiles(self):
        """
            This method gets triggered when the browse button is Clicked in the GUI
        function: The function is to take in a text field where the value needs to be set and called in a dialog box with
        file struture view starting at the 'root' and lets the user select the file they want and set the file path to
        the test field.
        """
        dialog_box = QDialog()
        fname = QFileDialog.getOpenFileNames(dialog_box, 'Open File', ' ', 'CXI Files (*.cxi)')
        self.fileField.setText(fname[0][0])
        self.eventNumber.setText("1")
        # print(fname[0][0])

    def writeToFile(self, eventsList, fileName):
        f = open(fileName, 'w')
        for key in eventsList:
            for i in eventsList[key]:

                # f.write('%s //%i \n' % (key, i))
                f.write(key)
                f.write(' ')
                f.write('//')
                f.write(str(i))
                f.write('\n')

        f.close()

    def sortFrames(self, file_name):
        """
            this method only works on single cxi file. for multiple files code needs to be changed
            function for sorting good frames from the bad frames based on the average intensity ratio of the peak of the
            curve vs crest of the curve
        """

        try:
            goodEvents = {}
            badEvents = {}
            # exit()
            # goodList to store all the events with expected pixel intensities for the file
            goodList = []

            # badList to store all the events with detector artifacts for the file
            badList = []

            with h5py.File(file_name, "r") as f:
                data = f['entry_1']['data_1']['data'][()]

            # print(len(data)) #this line was intended to see if the code is actually reading file and also at the same
            # time check to the number of data blocks in each cxi file

            # print('Reading %s and it has %i events' % (file, len(data)))
            # break

            for i in range(0, len(data)):
                frame = data[i]

                peakMeanIntensities = []
                for j in range(60, 80):
                    peakMeanIntensities.append(np.average(frame[2112:2288, j]))
                # print(peakMeanIntensities)

                crestMeanIntensities = []
                for k in range(165, 185):
                    crestMeanIntensities.append(np.average(frame[2112:2288, k]))
                # print(crestMeanIntensities)

                peakMean = np.average(peakMeanIntensities)
                crestMean = np.average(crestMeanIntensities)

                if peakMean / crestMean > 1.3:
                    goodList.append(i)
                else:
                    badList.append(i)

            #       print(goodList)
            #       print(badList)

            goodEvents[str(file_name)] = goodList
            badEvents[str(file_name)] = badList

            self.writeToFile(goodEvents, 'goodEventsGUI.list')
            self.writeToFile(badEvents, 'badEventsGUI.list')

            QMessageBox.information(self, 'Success', "Done Sorting")

        except FileNotFoundError:
            QMessageBox.critical(self, 'Fail', "Couldn't find file %s" % file_name)

        except ValueError:
            QMessageBox.critical(self, 'Fail', "Please enter a valid path")

    def advanceSortFrames(self, file_name):
        goodEvents = {}
        badEvents = {}

        # goodList to store all the events with expected pixel intensities for the file
        goodList = []
        # badList to store all the events with detector artifacts for the file
        badList = []
        try:
            with h5py.File(file_name, "r") as f:
                data = f['entry_1']['data_1']['data'][()]

            for i in range(len(data)):
                frame = data[i]

                avgIntensities = []
                for j in range(10, 186):
                    avgIntensities.append(np.average(frame[2112:2288, j]))

                fit = np.polyfit(np.arange(10, 186), avgIntensities, deg=4)
                # calculating the inflection points (second derivative of the forth order polynomial)

                # print(fit)
                x1 = round((-6 * fit[1] + np.sqrt(36 * fit[1] * fit[1] - 96 * fit[0] * fit[2])) / (24 * fit[0]))
                x2 = (-6 * fit[1] - np.sqrt(36 * fit[1] * fit[1] - 96 * fit[0] * fit[2])) / (24 * fit[0])
                # print('x1', x1)
                # print('x2', x2)

                if x1 in range(130, 140):
                    goodList.append(i)
                else:
                    badList.append(i)

            goodEvents[str(file_name)] = goodList
            badEvents[str(file_name)] = badList

            self.writeToFile(goodEvents, 'goodEvents-advanceSearch.list')
            self.writeToFile(badEvents, 'badEvents-advanceSearch.list')

            QMessageBox.information(self, 'Sucess', "Done Sorting")

        except FileNotFoundError:
            QMessageBox.critical(self, 'Fail', "Couldn't find file %s" % file_name)

        except ValueError:
            QMessageBox.critical(self, 'Fail', "Please Enter a file path")

    def returnMaxPixel(self, coeff, x_range):
        """
            coeff (object): out put of a numpy curve fit.
            xRange (tup) : a tuple with (min, max)

            returns the value where the coeff is maximized
        """

        storing_list = []
        for i in range(x_range[0], x_range[1]):
            storing_list.append((np.polyval(coeff, i), i))

        storing_list.sort()

        return storing_list[-1][1]

    def returnMaxPixelsList(self, file_name, deg=1, *args):
        """ fileName(str) : name of the file to be open
            deg (int) : order of the fit ex: is the fit a straight line (1) or quadratic (2 or more)
            *args(list) : expects a list of events to be considered. **TO BE IMPLEMENTED**
        """
        filename = file_name
        max_pixels = []

        with h5py.File(filename, "r") as f:
            data = f['entry_1']['data_1']['data'][()]

        for i in range(len(data)):
            frame = data[i]

            avgIntensities = []
            for j in range(10, 186):
                avgIntensities.append(np.average(frame[2112:2288, j]))

            fit = np.polyfit(np.arange(10, 186), avgIntensities, deg=deg)

            max_pixels.append(self.returnMaxPixel(fit, (10, 186)))

        return max_pixels

    def plotCurve(self, file_name, event_number=1):
        try:
            with h5py.File(file_name, "r") as f:
                data = f['entry_1']['data_1']['data'][()]

            frame = data[int(event_number)]

            avgIntensities = []

            for i in range(10, 185):
                avgIntensities.append(np.average(frame[2112:2288, i]))
            self.graphWidget.clear()
            self.graphWidget.plot(list(np.linspace(10, 185, 175)), avgIntensities)
            self.graphWidget.setTitle('average intensity over the selected panel', size='15pt')
            self.graphWidget.setLabel('left', "Avg. Pixel intensity")
            self.graphWidget.setLabel('bottom', "Pixel Number")
            self.graphWidget.show()

        except FileNotFoundError:
            QMessageBox.critical(self, 'Fail', "Couldn't find file %s" % file_name)

        except ValueError:
            QMessageBox.critical(self, 'Fail', "Please Enter a file path")

        except IndexError:
            QMessageBox.critical(self, 'Fail', 'Value you entered is out of bound')

    def plotFit(self, file_name, eventNumber=1, deg=4):
        """ fileName(str) : name of the file to be open
                eventNumber(int) : event number for the file
                deg (int) : order of the fit ex: is the fit a straight line (1) or quadratic (2 or more)
        """
        try:
            filename = file_name
            with h5py.File(filename, "r") as f:
                data = f['entry_1']['data_1']['data'][()]

            frame = data[int(eventNumber)]

            avgIntensities = []

            for i in range(10, 186):
                avgIntensities.append(np.average(frame[2112:2288, i]))

            fit = np.polyfit(np.arange(10, 186), avgIntensities, deg=deg)

            self.graphWidget.clear()
            self.graphWidget.plot(range(10, 186), avgIntensities, name='data')
            self.graphWidget.plot(range(10, 186), np.polyval(fit, range(10, 186)), name='fit', pen=pg.mkPen(color='r',
                                                                                                            width=2))
            self.graphWidget.setTitle('fitting a polynomial to average intensity over the selected panel', size='15pt')
            self.graphWidget.setLabel('left', "Avg. Pixel intensity")
            self.graphWidget.setLabel('bottom', "Pixel Number")
            self.graphWidget.addLegend()
            self.graphWidget.show()

        except FileNotFoundError:
            QMessageBox.critical(self, 'Fail', "Couldn't find file %s" % file_name)

        except ValueError:
            QMessageBox.critical(self, 'Fail', "Please Enter a file path")

    def plotMaxPixels(self, file_name):
        try:
            y = self.returnMaxPixelsList(file_name, deg=6)
            x = range(len(y))
            self.graphWidget.clear()
            self.graphWidget.plot(x, y, pen=None, symbol='o')
            self.graphWidget.setTitle('change of the pixel with the highest average intensity', size='15pt')
            self.graphWidget.setLabel('left', "Pixel Number")
            self.graphWidget.setLabel('bottom', "Frame Number")
            self.graphWidget.show()

        except FileNotFoundError:
            QMessageBox.critical(self, 'Fail', "Couldn't find file %s" % file_name)

        except ValueError:
            QMessageBox.critical(self, 'Fail', "Please Enter a file path")


# main .
if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = MainWindow()
    sys.exit(app.exec_())

import pyqtgraph as pg

w = pg.GraphicsWindow()
for i in range(4):
    w.addPlot(0, i)


def onClick(event):
    items = w.scene().items(event.scenePos())
    print("Plots:" + str([x for x in items if isinstance(x, pg.PlotItem)]))


w.scene().sigMouseClicked.connect(onClick)

app = pg.QtGui.QApplication([])
app.exec_()

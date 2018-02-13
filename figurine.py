# -*- coding: utf-8 -*-
"""
Created on Tue Nov 07 17:37:16 2017

Module to save modifiable matplotlib figure as simple .py script

call function saveFigurine(fig, filename) to use

Supported plot methods:
    ax.plot() :

    ax.scatter() :

    ax.pcolormesh() :


Supported customization methods:
    axis xlimit & ylimit
    axis xscale & yscale
    axis xlabel & ylabel
    axis title
    legend (plot and scatter)
    linecolor (plot and scatter)
    linestyle (plot)

@author: sebastian
"""

import numpy as np
import matplotlib.pyplot as plt


def saveFigurine(fig, filename):
    """
    Save matplotlib figure as .py file

    Parameters
    ----------
    fig :   plt.figure
            matplotlib figure you want to save

    filename :  string
                Path to save file. If it does not end in '.py', ending will be added automatically

    Output
    ------
    pyfig :     pyFigure
                PyFigure class used to create the file. Can be used for debugging purposes.
    """
    if filename[-3:] != '.py':
        filename += '.py'
    pyfig = pyFigure(fig)
    pyfig.save(filename)
    return pyfig


# =============================================================================
#  CLASSES
# =============================================================================
class pyFigure(object):
    def __init__(self, fig):
        self._base = fig
        self.axes = []
        for ax in self._base.axes:
            self.axes.append(pyAxis(ax))
        self.length = len(self.axes)

    def save(self, filename):
        wstr = self.getFileString()
        with open(filename, 'w') as ff:
            ff.writelines(wstr)

    def getFileString(self):
        fstr = ''
        # Write imports
        fstr += 'import numpy as np\n'
        fstr += 'import matplotlib.pyplot as plt\n'
        fstr += 'import matplotlib.mlab as ml\n'
        fstr += 'import seaborn as sns\n'
        fstr += 'sns.set_style(\'whitegrid\')\n'
        fstr += '\n'

        # Write figure creation
        fstr += 'fig = plt.figure()\n'

        subplots_numx = np.ceil((np.sqrt(self.length)))
        subplots_numy = int(round((np.sqrt(self.length))))
        # Write axes creation including data sets
        for i_ax, ax in enumerate(self.axes):
            ax_str = 'ax_%d' % i_ax
            fstr += ax_str + ' = fig.add_subplot(%d, %d, %d)\n' % (subplots_numx, subplots_numy, i_ax+1)
            fstr += '\n'
            for i_plot, plot in enumerate(ax.plots):
                for i_dat, dat_str in enumerate(plot.getDataStringList()):
                    var_str = 'dat_%d_%d_%d' % (i_ax, i_plot, i_dat)
                    fstr += var_str + ' = ' + dat_str + '\n'
                    fstr += '\n'
                if plot.length == 2:
                    dat1_str = 'dat_%d_%d_0' % (i_ax, i_plot)
                    dat2_str = 'dat_%d_%d_1' % (i_ax, i_plot)
                    fstr += ax_str + '.%s(%s, %s%s)' % (plot.getMethodString(), dat1_str, dat2_str, plot.getConfigString())
                    fstr += '\n'
                elif plot.length == 3 and plot.method == 'pcolormesh':
                    dat1_str = 'dat_%d_%d_0' % (i_ax, i_plot)
                    dat2_str = 'dat_%d_%d_1' % (i_ax, i_plot)
                    dat3_str = 'dat_%d_%d_2' % (i_ax, i_plot)
                    fstr += 'x,y = np.meshgrid(%s, %s)\n' % (dat1_str, dat2_str)
                    fstr += 'z = np.pad(%s.reshape(len(%s)-1, len(%s)-1), ((0,1),(0,1)), \'edge\')\n' % (dat3_str, dat1_str, dat2_str)
                    fstr += 'z = ml.griddata(x.flatten(), y.flatten(), z.flatten(), %s, %s, interp = \'linear\')\n' % (dat1_str, dat2_str)
                    fstr += ax_str + '.pcolormesh(x,y,z%s)\n' % (plot.getConfigString())
            fstr += ax.getConfigString(ax_str)
            fstr += ax.getLegendString(ax_str)
        fstr += 'plt.show(block=True)'
        return fstr



class pyAxis(object):
    def __init__(self, ax):
        self._base = ax
        self.plots = []
        for line in ax.lines:
            self.plots.append(pyLine(line))
        for item in ax.collections:
            if 'PathCollection' in str(type(item)):
                self.plots.append(pyScatter(item))
            if 'QuadMesh' in str(type(item)):
                self.plots.append(pyColormesh(item))
        self.length = len(self.plots)
        # Get config info
        self.xscale = self._base.get_xscale()
        self.yscale = self._base.get_yscale()
        self.xlabel = self._base.get_xlabel()
        self.ylabel = self._base.get_ylabel()
        self.xlim = self._base.get_xlim()
        self.ylim = self._base.get_ylim()

    def getConfigString(self, ax_str):
        cstr = ''
        cstr += ax_str + '.set_xscale(\'%s\')' % self.xscale + '\n'
        cstr += ax_str + '.set_yscale(\'%s\')' % self.yscale + '\n'
        cstr += ax_str + '.set_xlabel(\'%s\')' % self.xlabel + '\n'
        cstr += ax_str + '.set_ylabel(\'%s\')' % self.ylabel + '\n'
        cstr += ax_str + '.set_xlim([%.2e, %.2e])' % self.xlim + '\n'
        cstr += ax_str + '.set_ylim([%.2e, %.2e])' % self.ylim + '\n'
        cstr += ax_str + '.set_title(\'%s\')' % self._base.get_title() + '\n'
        cstr += '\n'
        return cstr

    def getLegendString(self, ax_str):
        if self._base.get_legend() != None:
            return ax_str+'.legend() \n'
        else:
            return ''

class pyPlot(object):
    def __init__(self, plot):
        self._base = plot
        self.method = 'plot'
        self.data = []
        # Get config info

    @property
    def length(self):
        return len(self.data)

    def getDataStringList(self):
        strings = []
        for data in self.data:
            strings.append('['+','.join(map(str, data))+']')
        return strings

    def getConfigString(self):
        cstr = ''
        cstr += ', label = r\'%s\'' % self._base.get_label()
        return cstr

    def getMethodString(self):
        return self.method

class pyLine(pyPlot):
    def __init__(self, plot):
        pyPlot.__init__(self, plot)
        self.method = 'plot'
        for item in self._base.get_data():
            self.data.append(item)

    def getConfigString(self):
        cstr = super(pyLine, self).getConfigString()
        color = self._base.get_color()
        if isinstance(color, str):
            cstr += ', color = \'%s\'' % color
        else:
            cstr += ', color = ' + str(color)
        cstr += ', linestyle = \'%s\'' % self._base.get_linestyle()
        return cstr

class pyScatter(pyPlot):
    def __init__(self, plot):
        pyPlot.__init__(self, plot)
        self.method = 'scatter'
        self._base.set_offset_position('data')
        for item in self._base.get_offsets().transpose():
            self.data.append(item)

    def getConfigString(self):
        cstr = super(pyScatter, self).getConfigString()
        facecolor = self._base.get_facecolor()[0]
        if isinstance(facecolor, str):
            cstr += ', facecolor = \'%s\'' % facecolor
        else:
            cstr += ', facecolor = ' + '['+','.join(map(str, facecolor))+']'
        return cstr

class pyColormesh(pyPlot):
    def __init__(self, plot):
        pyPlot.__init__(self, plot)
        self.method = 'pcolormesh'
        self.data.append(np.unique(self._base._coordinates[:,:,0]))
        self.data.append(np.unique(self._base._coordinates[:,:,0]))
        self.data.append(self._base.get_array())

    def getConfigString(self):
        cstr = ''
        return cstr



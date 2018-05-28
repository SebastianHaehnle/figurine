# -*- coding: utf-8 -*-
"""
Created on Tue Nov 07 17:37:16 2017

Module to save modifiable matplotlib figure as simple .py script

call function saveFigurine(fig, filename) to use

Supported plot methods:
    ax.plot() :

    ax.scatter() :

    ax.pcolormesh() :

    ax.errorbar() : (partially) Shows upper/lower limit bars, but not connecting line.

Supported customization methods:
    twinx() (exclusively, does not distinguish for twiny)
    axis xlimit & ylimit
    axis xscale & yscale
    axis xlabel & ylabel
    axis title
    legend (plot/errorbar and scatter)
    linecolor (plot/errorbar and scatter)
    linestyle (plot/errorbar)
    marker (plot/errorbar)
    mec (errorbar)
    mew (errorbar)

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
        self.twins = self.getTwinAxes()
        self.axes = []
        for i, ax in enumerate(self._base.axes):
#            if i in self.twins.keys():
            self.axes.append(pyAxis(self, ax))
        self.setColorbars()
        self.length = len(self.axes) - len(self.twins)

    def save(self, filename):
        wstr = self.getFileString()
        with open(filename, 'w') as ff:
            ff.writelines(wstr)

    def getTwinAxes(self):
        """
        Get twin axis occasions by comparing axis boundaries. Assumes twinx() was called if two axes have the same bounds
        returns
        -------
        twins :     dict
                    twins[key] = item --> key = item.twinx()
        """
        bounds = [ax.get_position().bounds for ax in self._base.axes]
        twins = {}
        for i, b in enumerate(bounds):
            if b in bounds[:i]:
                twins[i] = bounds[:i].index(b)
        return twins

    def setColorbars(self):
        for i, a in enumerate(self.axes):
            for j, p in enumerate(a.plots):
                if p.colorbar:
                    target_axes = [a._base for a in self.axes].index(p.colorbar.ax)
                    if target_axes < i:
                        print "Cannot handle colorbar properly in axes prior to data axes"
                        pass
                    else:
                        self.axes[target_axes].contains_colorbar = True
                        self.axes[target_axes].plots[0].method = 'colorbar'
                        self.axes[target_axes].plots[0].source_plot_string = 'im_%d_%d' % (i, j)
                        self.axes[target_axes].source_axis_string = 'ax_%d' % i


    def getFileString(self):
        fstr = ''
        # Write imports
        fstr += 'import numpy as np\n'
        fstr += 'import matplotlib.pyplot as plt\n'
        fstr += 'import matplotlib.mlab as ml\n'
        fstr += 'from mpl_toolkits.axes_grid1 import make_axes_locatable\n'
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
            if self.twins.has_key(i_ax):
                fstr += ax_str + ' = ax_%d.twinx()' % self.twins[i_ax]
            elif ax.contains_colorbar:
                fstr += ax_str + ' = make_axes_locatable(%s).append_axes(\'right\', size=\'5%s\', pad=0.05)' % ( ax.source_axis_string, '%')
            else:
                fstr += ax_str + ' = fig.add_subplot(%d, %d, %d)\n' % (subplots_numx, subplots_numy, i_ax+1)
            fstr += '\n'
            for i_plot, plot in enumerate(ax.plots):
                for i_dat, dat_str in enumerate(plot.getDataStringList()):
                    var_str = 'dat_%d_%d_%d' % (i_ax, i_plot, i_dat)
                    fstr += var_str + ' = ' + dat_str + '\n'
                    fstr += '\n'
                if plot.method in ['plot', 'scatter']:
                    dat1_str = 'dat_%d_%d_0' % (i_ax, i_plot)
                    dat2_str = 'dat_%d_%d_1' % (i_ax, i_plot)
                    fstr += ax_str + '.%s(%s, %s%s)' % (plot.getMethodString(), dat1_str, dat2_str, plot.getConfigString())
                    fstr += '\n'
                elif plot.method == 'pcolormesh':
                    dat1_str = 'dat_%d_%d_0' % (i_ax, i_plot)
                    dat2_str = 'dat_%d_%d_1' % (i_ax, i_plot)
                    dat3_str = 'dat_%d_%d_2' % (i_ax, i_plot)
                    fstr += 'x,y = np.meshgrid(%s, %s)\n' % (dat1_str, dat2_str)
                    fstr += 'z = np.pad(np.array(%s).reshape(len(%s)-1, len(%s)-1), ((0,1),(0,1)), \'edge\')\n' % (dat3_str, dat1_str, dat2_str)
                    fstr += 'z = ml.griddata(x.flatten(), y.flatten(), z.flatten(), %s, %s, interp = \'linear\')\n' % (dat1_str, dat2_str)
                    fstr += 'im_%d_%d = %s.pcolormesh(x,y,z%s)\n' % (i_ax, i_plot, ax_str, plot.getConfigString())
                elif plot.method == 'colorbar':
                    fstr += 'fig.colorbar(%s, cax = %s)' % (plot.source_plot_string, ax_str)
                fstr += '\n'
            fstr += ax.getConfigString(ax_str)
            fstr += ax.getLegendString(ax_str)
        fstr += 'plt.show(block=True)'
        return fstr



class pyAxis(object):
    def __init__(self, parent, ax):
        self.parent = parent
        self._base = ax
        self.plots = []
        for line in ax.lines:
            self.plots.append(pyLine(self, line))
        for item in ax.collections:
            if 'PathCollection' in str(type(item)):
                self.plots.append(pyScatter(self, item))
            if 'QuadMesh' in str(type(item)):
                self.plots.append(pyColormesh(self, item))
        self.length = len(self.plots)
        self.contains_colorbar = False
        self.source_axis_string  = ''

    def getConfigString(self, ax_str):
        cstr = ''
        if not self.contains_colorbar:
            cstr += ax_str + '.set_xscale(\'%s\')' % self._base.get_xscale() + '\n'
            cstr += ax_str + '.set_yscale(\'%s\')' % self._base.get_yscale() + '\n'
            cstr += ax_str + '.set_xlabel(\'%s\')' % self._base.get_xlabel() + '\n'
            cstr += ax_str + '.set_ylabel(\'%s\')' % self._base.get_ylabel() + '\n'
            cstr += ax_str + '.set_xlim([%.2e, %.2e])' % self._base.get_xlim()+ '\n'
            cstr += ax_str + '.set_ylim([%.2e, %.2e])' % self._base.get_ylim() + '\n'
            cstr += ax_str + '.set_title(\'%s\')' % self._base.get_title() + '\n'
        cstr += ax_str + '.set_position(%s)' % str(self._base.get_position().bounds) + '\n'
        cstr += '\n'
        return cstr

    def getLegendString(self, ax_str):
        if self._base.get_legend() != None:
            return ax_str+'.legend() \n'
        else:
            return ''

class pyPlot(object):
    def __init__(self, parent, plot):
        self.parent = parent
        self._base = plot
        self.colorbar = None
        self.method = 'plot'
        self.source_plot_string  = ''
#        self.data = []
        # Get config info

    @property
    def data(self):
        return []

    @property
    def length(self):
        return len(self.data)

    def getDataStringList(self):
        strings = []
        for data in self.data:
            strings.append('['+','.join(map(str, data))+']')
            strings[-1] = strings[-1].replace('inf', 'np.inf')
        return strings

    def getConfigString(self):
        cstr = ''
        cstr += ', label = r\'%s\'' % self._base.get_label()
        return cstr

    def getMethodString(self):
        return self.method

    def getColorString(self, color, argname):
        if isinstance(color, str):
            cstr = ', %s = \'%s\'' % (argname, color)
        else:
            cstr = ', %s = %s' % (argname, str(color))
        return cstr

class pyLine(pyPlot):
    def __init__(self, parent, plot):
        pyPlot.__init__(self, parent, plot)
        self.method = 'plot'

    @property
    def data(self):
        data = []
        for item in self._base.get_data():
            data.append(item)
        return data

    def getConfigString(self):
        cstr = super(pyLine, self).getConfigString()
        color = self._base.get_color()
        mec = self._base.get_mec()
        cstr += self.getColorString(color, 'color')
        cstr += ', linestyle = \'%s\'' % self._base.get_linestyle()
        cstr += ', marker = \'%s\'' % self._base.get_marker()
        cstr += self.getColorString(mec, 'mec')
        cstr += ', mew = \'%s\'' % self._base.get_mew()
        return cstr

class pyScatter(pyPlot):
    def __init__(self, parent, plot):
        pyPlot.__init__(self, parent, plot)
        self.method = 'scatter'

    @property
    def data(self):
        data = []
        self._base.set_offset_position('data')
        for item in self._base.get_offsets().transpose():
            data.append(item)
        return data

    def getConfigString(self):
        cstr = super(pyScatter, self).getConfigString()
        facecolor = self._base.get_facecolor()[0]
        if isinstance(facecolor, str):
            cstr += ', facecolor = \'%s\'' % facecolor
        else:
            cstr += ', facecolor = ' + '['+','.join(map(str, facecolor))+']'
        return cstr


class pyColormesh(pyPlot):
    def __init__(self, parent, plot):
        pyPlot.__init__(self, parent, plot)
        self.colorbar = self._base.colorbar
        self.method = 'pcolormesh'

    @property
    def data(self):
        data = []
        if self.method == 'pcolormesh':
            data.append(np.unique(self._base._coordinates[:,:,0]))
            data.append(np.unique(self._base._coordinates[:,:,1]))
            data.append(self._base.get_array())
        else:
            data = []
        return data

    def getCmapString(self):
        try:
            cmap_name = self._base.cmap.name
            return ', cmap = plt.get_cmap(\'%s\')' % cmap_name
        except ValueError:
            print "Colormap name not supported in Figurine"
            return ''

    def getConfigString(self):
        cstr = ''
        cstr += self.getCmapString()
        return cstr



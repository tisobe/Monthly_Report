#!/usr/bin/env /proj/sot/ska/bin/python

#############################################################################################################
#                                                                                                           #
#           monthly_report_cti_avg_plots.py: create data and plots of cti trends for monthly report         #
#                                                                                                           #
#               ******* you must run:*******************                                                    #
#           setenv PYTHONPATH "/proj/sot/ska/arch/x86_64-linux_CentOS-5/lib/python2.7/site-packages"        #
#               ****************************************                                                    #
#                                                                                                           #
#           this version does not use "al k alpha" values                                                   #
#                                                                                                           #
#           author: t. isobe (tisobe@cfa.harvard.edu)                                                       #
#                                                                                                           #
#           Last Update: Jun 02, 2014                                                                       #
#                                                                                                           #
#############################################################################################################

import os
import sys
import re
import string
import random
import operator
import numpy

import matplotlib as mpl

if __name__ == '__main__':

    mpl.use('Agg')

path = '/data/mta/Script/ACIS/CTI/house_keeping/dir_list_py'

f    = open(path, 'r')
data = [line.strip() for line in f.readlines()]
f.close()

for ent in data:
    atemp = re.split(':', ent)
    var  = atemp[1].strip()
    line = atemp[0].strip()
    exec "%s = %s" %(var, line)

#
#--- append a path to a private folder to python directory
#
sys.path.append(mta_dir)
#
#--- converTimeFormat contains MTA time conversion routines
#
import convertTimeFormat    as tcnv
import mta_common_functions as mcf
import robust_linear        as robust

#
#--- temp writing file name
#

rtail  = int(10000 * random.random())
zspace = '/tmp/zspace' + str(rtail)

yupper = 4.0

#---------------------------------------------------------------------------------------------------
#-- monthly_report_cti_avg_plots: a control function to create plots and data for monthly report ---
#---------------------------------------------------------------------------------------------------

def monthly_report_cti_avg_plots():

    """
    a control function to create plots and data for monthly report cti trends
    Input: none, but read from cti full data table (/data/mta/Script/ACIS/CTI/Data/...)
    Output: plots in ./Plots
            data  in ./Data
    """
#
#--- set which CCDs belong to which set
#
    image_ccds = (0, 1, 2, 3)
    spec_ccds  = (4, 6, 8, 9)
    back_ccds  = (5, 7)
#
#--- set a few plotting related values
#
    xname = 'Time (Year)'
    yname = 'Mean CTI'
#
#--- extract data for imaging
#
    [xSets, ySets, eSets] = get_data(image_ccds, 'image')

    xmin = int(min(xSets[0])) -1
    xmax = int(max(xSets[0])) +1

    ymin  = 1.0
    ymax  = 3.0
    yMinSets = []
    yMaxSets = []
    for ent in ySets:

        yMinSets.append(ymin)
        yMaxSets.append(ymax)
#
#--- plot the trend
#
    entLabels = ['CCD0', 'CCD1', 'CCD2', 'CCD3']
    plotPanel(xmin, xmax, yMinSets, yMaxSets, xSets, ySets, eSets, xname, yname, entLabels, 2011.0)
#    cmd = 'mv out.png ./Plots/cti_avg_acis_i.png'
#    cmd = 'mv out.png ./cti_avg_acis_i.png'
#    os.system(cmd)
#
#--- spectral
#

    ymin  = 1.0
    ymax  = 3.0
    yMinSets = []
    yMaxSets = []
    for ent in ySets:

        yMinSets.append(ymin)
        yMaxSets.append(ymax)
    [xSets, ySets, eSets] = get_data(spec_ccds,   'spec')
    entLabels = ['CCD4', 'CCD6', 'CCD8', 'CCD9']
    plotPanel(xmin, xmax, yMinSets, yMaxSets, xSets, ySets, eSets, xname, yname, entLabels, 2011.0)
#    cmd = 'mv out.png ./Plots/cti_avg_acis_s.png'
#    cmd = 'mv out.png ./cti_avg_acis_s.png'
#    os.system(cmd)
#
#--- back side
#

    ymin  = 0.0
    ymax  = 1.0
    yMinSets = []
    yMaxSets = []
    for ent in ySets:

        yMinSets.append(ymin)
        yMaxSets.append(ymax)

    [xSets, ySets, eSets] = get_data(back_ccds,  'back')
    entLabels = ['CCD5', 'CCD7']
    plotPanel(xmin, xmax, yMinSets, yMaxSets, xSets, ySets, eSets, xname, yname, entLabels, 2012.0)
    cmd = 'mv out.png ./Plots/cti_avg_acis_bi.png'
#    cmd = 'mv out.png ./cti_avg_acis_bi.png'
    os.system(cmd)

    
#---------------------------------------------------------------------------------------------------
#-- get_data: read out data from the full cti data table and creates monthly report data table  ----
#---------------------------------------------------------------------------------------------------

def get_data(ccd_list, out):

    """
    read out data from the full cti data table and creates monthly report data table
    Input: ccd_list     --- a list of ccds which you want to read the data
           out          --- a type of the data, "image", "spec", or "back"
           data are read from "/data/mta/Script/ACIS/CTI/DATA/..."
    Output: xSets       --- a list of lists of x values of each ccd
            ySets       --- a list of lists of y values of each ccd
            eSets       --- a list of lists of y error of each ccd
            ./Data/ccd<ccd>_data: monthly averaged cti for monthly report
    """
#
#--- read intercept adjusting table
#
    al_factors = read_correction_factor('al')
    mn_factors = read_correction_factor('mn')
    ti_factors = read_correction_factor('ti')
#
#--- find today's date; ctime[0] is year and ctime[1] is month
#
    ctime = tcnv.currentTime()
    lyear = int(ctime[0])
    lmonth= int(ctime[1])
#
#--- set dimension of the array
#
    c_cnt = 12 * (int(ctime[0]) - 2000) + int(ctime[1])
    d_cnt = len(ccd_list)
#
#--- for none backside CCDs, we use detrended data sets
#
    if out == 'back':
        dir = '/data/mta/Script/ACIS/CTI/Data/Data_adjust/'
#
#--- vadd to adjust the mean position of CTI
#
    else:
        dir = '/data/mta/Script/ACIS/CTI/Data/Det_Data_adjust/'

    xSets = []
    ySets = []
    eSets = []
#
#-- go around each ccds
#
    for i in range(0, d_cnt):
        ccd = ccd_list[i]
#
#--- set cti data array and error array
#
        avals = [0 for x in range(0, c_cnt)]
        sum   = [0 for x in range(0, c_cnt)]
        sum2  = [0 for x in range(0, c_cnt)]
#
#--- go around all lines
#
        for elm in ('mn'):
            vadd = 0
            corrections = mn_factors
            for k in range(0, 4):
                vadd += corrections[k][ccd]
            vadd /= 4.0

            file = dir + 'mn_ccd' + str(ccd)
            f    = open(file, 'r')
            data = [line.strip() for line in f.readlines()]
            f.close()

            for ent in data:
                atemp = re.split('\t+|\s+', ent)
                btemp = re.split('-', atemp[0])
#
#--- find the row that you want to add this data 
#
                pos   = 12 * (int(btemp[0]) - 2000) + int(btemp[1]) - 1

                for k in range(1, 5):
                    ctemp = re.split('\+\-', atemp[k])
                    val  = float(ctemp[0])
                    if val > 0 and val < yupper:
#
#--- correct the value so that all data points have about the same base line
#
                        val -= (corrections[k-1][ccd])
                        val += vadd
                        err  = float(ctemp[1])
                        if err > 0:
                            avals[pos] += val 
                            sum[pos]   += 1.0
                            sum2[pos]  += val * val
#
#--- open file for print out
#
        file = './Data/cti_data/ccd' + str(ccd) + '_data'
        fo   = open(file, 'w')
        line = '#\n#date       cti     errer\n#\n'
        fo.write(line)
        
        chk  = 0
        xvals = []
        yvals = []
        evals = []
        for k in range(2000, lyear+1):
            for m in range(0, 13):
                if (k == lyear) and (m > lmonth):
                    chk = 1
                    break

                pos = 12 * (k - 2000) + m -1
#
#--- set time in fractional year. adding 0.04 to set time to the mid month
#
                date = k + float(m) / 12.0 + 0.04     
                date = round(date, 3)
#
#--- compute average and erorr
#
                if avals[pos] > 0:
                    avg = avals[pos] / sum[pos]
                    err = math.sqrt(sum2[pos] /sum[pos] - avg * avg)
                    avg =  round(avg, 3)
                    err =  round(err, 3)

                    if len(str(date)) == 7:
                        line = str(date) + ' \t' + str(avg) + '\t' + str(err) + '\n'
                    else:
                        line = str(date) + '\t'  + str(avg) + '\t' + str(err) + '\n'
                    fo.write(line)


                    xvals.append(date)
                    yvals.append(avg)
                    evals.append(err)


            if chk  > 0:
                break

        fo.close()
#
#--- create a lists of lists
#
        xSets.append(xvals)
        ySets.append(yvals)
        eSets.append(evals)

    return [xSets, ySets, eSets]


#---------------------------------------------------------------------------------------------------
#-- read_correction_factor: read mean CTI values from table                                      ---
#---------------------------------------------------------------------------------------------------

def read_correction_factor(elm):

    """
    read mean CTI values from table
    Input:  elm --- element al, mn, or ti
    Output: save --- 4 x 10 data table contatining mean CTI values of <node> x <ccd>
    """
    save = numpy.zeros((4,10))

    file = './house_keeping/' + elm + '_intc'
    f    = open(file, 'r')
    data = [line.strip() for line in f.readlines()]
    f.close()

    for i in range(0, len(data)):
        temp = re.split('\s+', data[i])
        for j in range(0, 4):
            val  = float(temp[j+1])
            save[j][i] = val

    return save


#---------------------------------------------------------------------------------------------------
#--- plotPanel: plots multiple data in separate panels                                           ---
#---------------------------------------------------------------------------------------------------

def plotPanel(xmin, xmax, yMinSets, yMaxSets, xSets, ySets, eSets, xname, yname, entLabels, ydiv):

    """
    This function plots multiple data in separate panels
    Input:  xmin, xmax, ymin, ymax: plotting area
            xSets: a list of lists containing x-axis data
            ySets: a list of lists containing y-axis data
            eSets: a list of lists containing error values of y-axis
            yMinSets: a list of ymin 
            yMaxSets: a list of ymax
            entLabels: a list of the names of each data
            ydiv:   a location of dividing spot

    Output: a png plot: out.png
    """
#
#--- set line color list
#
    colorList = ('blue', 'green', 'red', 'aqua', 'lime', 'fuchsia', 'maroon', 'black', 'yellow', 'olive')
#
#--- clean up the plotting device
#
    plt.close('all')
#
#---- set a few parameters
#
    mpl.rcParams['font.size'] = 13
    props = font_manager.FontProperties(size=9)
    plt.subplots_adjust(hspace=0.06)

    tot = len(entLabels)
#
#--- start plotting each data
#
    for i in range(0, len(entLabels)):
        axNam = 'ax' + str(i)
#
#--- setting the panel position
#
        j = i + 1
        if i == 0:
            line = str(tot) + '1' + str(j)
        else:
            line = str(tot) + '1' + str(j) + ', sharex=ax0'
            line = str(tot) + '1' + str(j)

        exec "%s = plt.subplot(%s)"       % (axNam, line)
        exec "%s.set_autoscale_on(False)" % (axNam)      #---- these three may not be needed for the new pylab, but 
        exec "%s.set_xbound(xmin,xmax)"   % (axNam)      #---- they are necessary for the older version to set

        exec "%s.set_xlim(xmin=xmin, xmax=xmax, auto=False)" % (axNam)
        exec "%s.set_ylim(ymin=yMinSets[i], ymax=yMaxSets[i], auto=False)" % (axNam)
#
#--- since the cti seems evolving after year <ydiv>, fit two different lines before and after that point
#
        xdata  = xSets[i]
        ydata  = ySets[i]
        edata  = eSets[i]
  
        xdata1 = []
        ydata1 = []
        edata1 = []
        xdata2 = []
        ydata2 = []
        edata2 = []
        for k in range(0, len(xdata)):
            if xdata[k] < ydiv:
                xdata1.append(xdata[k])
                ydata1.append(ydata[k])
                edata1.append(edata[k])
            else:
                xdata2.append(xdata[k])
                ydata2.append(ydata[k])
                edata2.append(edata[k])

#
#---- actual data plotting
#
        p, = plt.plot(xdata, ydata, color=colorList[i], marker='*', markersize=4.0, lw =0)
        errorbar(xdata, ydata, yerr=edata, color=colorList[i],  markersize=4.0, fmt='*')
#
#--- fitting straight lines with robust method and plot the results
#
        xdata1 = numpy.array(xdata1)
        ydata1 = numpy.array(ydata1)
        edata1 = numpy.array(edata1)
        (intc, slope, err)  = robust.robust_fit(xdata1, ydata1)

        ystart = intc + slope * 2000
        ystop  = intc + slope * ydiv 
        lxdata = [2000, ydiv]
        lydata = [ystart, ystop]
        p, = plt.plot(lxdata, lydata, color=colorList[i], marker='', markersize=1.0, lw =2)

        xdata2 = numpy.array(xdata2)
        ydata2 = numpy.array(ydata2)
        edata2 = numpy.array(edata2)
        (intc2, slope2,err)  = robust.robust_fit(xdata2, ydata2)

        ystart = intc2 + slope2 * ydiv 
        ystop  = intc2 + slope2 * xmax 
        lxdata = [ydiv, xmax]
        lydata = [ystart, ystop]
        p, = plt.plot(lxdata, lydata, color=colorList[i], marker='', markersize=1.0, lw =2)

#
#--- add legend
#
        lslope = round(slope, 3)
        lslope2 = round(slope2, 3)
        line = entLabels[i] + ' Slope: ' + str(lslope) + ' (before '+ str(ydiv) + ') / ' + str(lslope2) + ' (after '+ str(ydiv) + ')'
        leg = legend([p],  [line], prop=props, loc=2)
        leg.get_frame().set_alpha(0.5)

        exec "%s.set_ylabel(yname, size=8)" % (axNam)

#
#--- add x ticks label only on the last panel
#
    for i in range(0, tot):
        ax = 'ax' + str(i)

        if i != tot-1: 
            exec "line = %s.get_xticklabels()" % (ax)
            for label in  line:
                label.set_visible(False)
        else:
            pass

    xlabel(xname)

#
#--- set the size of the plotting area in inch (width: 10.0in, height 2.08in x number of panels)
#
    fig = matplotlib.pyplot.gcf()
    height = (2.00 + 0.08) * tot
    fig.set_size_inches(10.0, height)
#
#--- save the plot in png format
#
    plt.savefig('out.png', format='png', dpi=100)

#--------------------------------------------------------------------

#
#--- pylab plotting routine related modules
#

from pylab import *
import matplotlib.pyplot as plt
import matplotlib.font_manager as font_manager
import matplotlib.lines as lines

if __name__ == '__main__':
    monthly_report_cti_avg_plots()



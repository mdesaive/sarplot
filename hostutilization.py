#! /usr/bin/env python
# $Id: demo.py 299 2007-03-30 12:52:17Z mhagger $

# Copyright (C) 1999-2003 Michael Haggerty <mhagger@alum.mit.edu>
#
# This file is licensed under the GNU Lesser General Public License
# (LGPL).  See LICENSE.txt for details.

"""hostutilization.py -- Reads SAR data from host and creates plots.

Run this script by typing 'python hostutilization.py'.

"""

import argparse
import datetime
import errno
import glob
import shlex
import os
import pdb
import re
import subprocess

from numpy import *

# If the package has been installed correctly, this should work:
import Gnuplot
import Gnuplot.funcutils


class hostutil(object):

    def __init__(self, dom, user, host, sysstat_path, dst_dir="."):
        self.dom = dom
        self.user = user
        self.host = host
        self.sysstat_path = sysstat_path
        self.dst_dir = dst_dir

        self.sysstat_snippet = "sa"
        self.sysstat_files = "sysstat-files"
        self.csv_files = "results"

        self.nic_names = {}
        self.doms_explicit = []

    def download_sysstat_files(self):
        if self.user is not None:
            serverstring = self.user + "@" + \
                self.host + ":" + self.sysstat_path
        else:
            serverstring = self.host + ":" + self.sysstat_path

        try:
            os.makedirs(
                self.dst_dir + "/hosts/" + self.host + "/" + self.sysstat_files)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise

        if self.dom == "ALL":
            serverstring = serverstring + "/sa??"
            print("scp", serverstring, self.dst_dir +
                  "/hosts/" + self.host + "/" + self.sysstat_files)
            subprocess.call(
                ["scp", serverstring, self.dst_dir + "/" + self.host + "/" + self.sysstat_files])
        else:
            for mydom in self.dom.split():
                print("scp", serverstring + "/" + self.sysstat_snippet + mydom,
                      self.dst_dir + "/hosts/" + self.host + "/" + self.sysstat_files)
                subprocess.call(
                    ["scp", serverstring + "/" + self.sysstat_snippet + mydom, self.dst_dir + "/hosts/" + self.host + "/" + self.sysstat_files])

    def net_prep_csv(self):
        try:
            os.makedirs(self.dst_dir + "/" + self.csv_files)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise

        if self.dom == "ALL":
            self.doms_explicit = [file[-2:]
                                  for file in glob.glob(self.dst_dir + "/hosts/" + self.host + "/" + self.sysstat_files + "/sa??")]
            # str_dom_tmp = subprocess.check_output(["ls", self.dst_dir + "/hosts/" + self.host + "/" + self.sysstat_files + "/sa??"])
            # my_doms = []
            # my_doms_tmp = str_dom_tmp.splitlines()
            # for my_dom in my_doms_tmp:
            #     self.doms_explicit.append(my_dom[2:].decode())
        else:
            self.doms_explicit = self.dom.split()

        net_header = "09:00:01        IFACE   rxpck/s   txpck/s    rxkB/s    txkB/s   rxcmp/s   txcmp/s  rxmcst/s   %ifutil".split(
        )

        # Match for English language.
        drop_lines = re.compile(
            "^Linux|LINUX RESTART|^$|IFACE   rxpck/s   txpck/s    rxkB/s    txkB/s   rxcmp/s   txcmp/s  rxmcst/s   %ifutil|^Durchschn")

        for my_dom in self.doms_explicit:
            matrix_output = []
            dict_nic_files = {}

            str_cmd = "/usr/bin/sar -n DEV -f " + self.dst_dir + \
                "/hosts/" + self.host + "/" + self.sysstat_files + "/sa" + my_dom
            print(str_cmd)
            cmd = shlex.split(str_cmd)
            str_sar_net = subprocess.check_output(cmd)

            for myline in str_sar_net.splitlines():
                # pdb.set_trace()
                if not drop_lines.search(myline.decode()):
                    # print(myline.decode())
                    # matrix_output.append(myline.decode().split())
                    nic_name = myline.decode().split()[1]
                    if nic_name not in dict_nic_files:
                        dict_nic_files[nic_name] = open(
                            self.csv_files + "/" + self.host + "-" + my_dom + "-nic-" + nic_name + ".csv", "w")
                        # print(nic_name)
                    # To leave decimal separator as is:
                    # dict_nic_files[nic_name].write(myline.decode() + "\n")
                    # To replace comma with dot use:
                    dict_nic_files[nic_name].write(
                        myline.decode().replace(',', '.') + "\n")

            self.nic_names[my_dom] = dict_nic_files.keys()

            for my_file in dict_nic_files.values():
                my_file.close()

    def net_plot(self):
        if not os.path.exists('./diagrams'):
             os.makedirs('./diagrams')

        for my_dom in self.doms_explicit:
            print("*** Day " + my_dom)
            # A straightforward use of gnuplot.  The `debug=1' switch is used
            # in these examples so that the commands that are sent to gnuplot
            # are also output on stderr.

            plots_ethx_rxkb = []
            plots_ethx_txkb = []
            plots_vif_rxkb = []
            plots_vif_txkb = []
            plots_vlan_rxkb = []
            plots_vlan_txkb = []

            for my_nic in self.nic_names[my_dom]:
                if my_nic.startswith("eth"):
                    plots_ethx_rxkb.append(
                        Gnuplot.File("./results/" + self.host + "-" + my_dom + "-nic-" + my_nic + ".csv", using="1:5", with_="lines", title=my_nic))
                    plots_ethx_txkb.append(
                        Gnuplot.File("./results/" + self.host + "-" + my_dom + "-nic-" + my_nic + ".csv", using="1:6", with_="lines", title=my_nic))
                elif my_nic.startswith("vlan"):
                    plots_vlan_rxkb.append(
                        Gnuplot.File("./results/" + self.host + "-" + my_dom + "-nic-" + my_nic + ".csv", using="1:5", with_="lines", title=my_nic))
                    plots_vlan_txkb.append(
                        Gnuplot.File("./results/" + self.host + "-" + my_dom + "-nic-" + my_nic + ".csv", using="1:6", with_="lines", title=my_nic))
                elif my_nic != "br0" and my_nic != "lo" and my_nic != "ovs-system":
                    plots_vif_rxkb.append(
                        Gnuplot.File("./results/" + self.host + "-" + my_dom + "-nic-" + my_nic + ".csv", using="1:5", with_="lines", title=my_nic))
                    plots_vif_txkb.append(
                        Gnuplot.File("./results/" + self.host + "-" + my_dom + "-nic-" + my_nic + ".csv", using="1:6", with_="lines", title=my_nic))

            # g.plot(Gnuplot.File("./results/hera-" + my_dom + "-nic-" + "eth0" + ".csv", using="1:5"),
            # Gnuplot.File("./results/hera-" + my_dom + "-nic-" + "eth1" +
            # ".csv", using="1:5"))

            g = Gnuplot.Gnuplot(debug=1)

            g('set terminal pngcairo size 1750,875 enhanced font \'Verdana,8\'')
            g('set output \'./diagrams/' +
              self.host + "-" + my_dom + '-nic.png\'')
            # g('set style data linespoints') # give gnuplot an arbitrary
            # command
            g('set format x "%H:%M"')
            g('set timefmt "%H:%M:%S"')
            g('set xdata time')
            g('set multiplot layout 3, 2')
            g("set decimalsign ','")

            g.title('Network Received KB/s')  # (optional)
            g.plot(*plots_ethx_rxkb)
            g.title('Network Received KB/s')  # (optional)
            g.plot(*plots_ethx_txkb)
            g.title('Network Received KB/s')  # (optional)
            g.plot(*plots_vlan_rxkb)
            g.title('Network Transmited KB/s')  # (optional)
            g.plot(*plots_vlan_txkb)
            g.title('Network Transmited KB/s')  # (optional)
            g.plot(*plots_vif_rxkb)
            g.title('Network Transmited KB/s')  # (optional)
            g.plot(*plots_vif_txkb)

            g('set nomultiplot')
        # Plot a list of (x, y) pairs (tuples or a numpy array would
        # also be OK):
        # real_nics = (Gnuplot.File("./results/hera-04-nic-eth0.csv", using="1:5"),
        #     (Gnuplot.File("./results/hera-04-nic-eth1.csv", using="1:5"))
        # g.plot(real_nics)
        # input('Please press return to continue...\n')


def initialize():
    parser = argparse.ArgumentParser()
    parser.add_argument("-H", "--host", required=True,
                        help="Host from which the sysstat info should be collected.")
    parser.add_argument("-u", "--user", help="User for SSH server connection")
    parser.add_argument(
        "-p", "--path", help="Path where to find sysstat files")
    parser.add_argument(
        "-d", "--days", help="Days of month, for which graphs should be created. \"02 03 31\" or ALL")
    args = parser.parse_args()

    if args.days is None:
        d = datetime.date.today()
        DOM = d.strftime('%d')
    else:
        DOM = str(args.days)

    USER = args.user

    if args.path is None:
        PATH = "/var/log/sysstat"
    else:
        PATH = args.path

    HOST = str(args.host)
    my_hostutil = hostutil(DOM, USER, HOST, PATH)

    return(my_hostutil)


def demo():
    """Demonstrate the Gnuplot package."""

    # A straightforward use of gnuplot.  The `debug=1' switch is used
    # in these examples so that the commands that are sent to gnuplot
    # are also output on stderr.
    g = Gnuplot.Gnuplot(debug=1)
    g.title('Network Utilization')  # (optional)
    g('set style data linespoints')  # give gnuplot an arbitrary command
    # Plot a list of (x, y) pairs (tuples or a numpy array would
    # also be OK):
    g.plot([[0, 1.1], [1, 5.8], [2, 3.3], [3, 4.2]])
    input('Please press return to continue...\n')

    g.reset()
    # Plot one dataset from an array and one via a gnuplot function;
    # also demonstrate the use of item-specific options:
    x = arange(10, dtype='float_')
    y1 = x ** 2
    # Notice how this plotitem is created here but used later?  This
    # is convenient if the same dataset has to be plotted multiple
    # times.  It is also more efficient because the data need only be
    # written to a temporary file once.
    d = Gnuplot.Data(x, y1,
                     title='calculated by python',
                     with_='points 3 3')
    g.title('Data can be computed by python or gnuplot')
    g.xlabel('x')
    g.ylabel('x squared')
    # Plot a function alongside the Data PlotItem defined above:
    g.plot(Gnuplot.Func('x**2', title='calculated by gnuplot'), d)
    input('Please press return to continue...\n')

    # Save what we just plotted as a color postscript file.

    # With the enhanced postscript option, it is possible to show `x
    # squared' with a superscript (plus much, much more; see `help set
    # term postscript' in the gnuplot docs).  If your gnuplot doesn't
    # support enhanced mode, set `enhanced=0' below.
    g.ylabel('x^2')  # take advantage of enhanced postscript mode
    g.hardcopy('gp_test.ps', enhanced=1, color=1)
    print ('\n******** Saved plot to postscript file "gp_test.ps" ********\n')
    input('Please press return to continue...\n')

    g.reset()
    # Demonstrate a 3-d plot:
    # set up x and y values at which the function will be tabulated:
    x = arange(35) / 2.0
    y = arange(30) / 10.0 - 1.5
    # Make a 2-d array containing a function of x and y.  First create
    # xm and ym which contain the x and y values in a matrix form that
    # can be `broadcast' into a matrix of the appropriate shape:
    xm = x[:, newaxis]
    ym = y[newaxis, :]
    m = (sin(xm) + 0.1 * xm) - ym ** 2
    g('set parametric')
    g('set style data lines')
    g('set hidden')
    g('set contour base')
    g.title('An example of a surface plot')
    g.xlabel('x')
    g.ylabel('y')
    # The `binary=1' option would cause communication with gnuplot to
    # be in binary format, which is considerably faster and uses less
    # disk space.  (This only works with the splot command due to
    # limitations of gnuplot.)  `binary=1' is the default, but here we
    # disable binary because older versions of gnuplot don't allow
    # binary data.  Change this to `binary=1' (or omit the binary
    # option) to get the advantage of binary format.
    g.splot(Gnuplot.GridData(m, x, y, binary=0))
    input('Please press return to continue...\n')

    # plot another function, but letting GridFunc tabulate its values
    # automatically.  f could also be a lambda or a global function:
    def f(x, y):
        return 1.0 / (1 + 0.01 * x ** 2 + 0.5 * y ** 2)

    g.splot(Gnuplot.funcutils.compute_GridData(x, y, f, binary=0))
    input('Please press return to continue...\n')

    # Explicit delete shouldn't be necessary, but if you are having
    # trouble with temporary files being left behind, try uncommenting
    # the following:
    # del g, d


# when executed, just run demo():
if __name__ == '__main__':
    my_hostutil = initialize()
    my_hostutil.download_sysstat_files()
    my_hostutil.net_prep_csv()
    my_hostutil.net_plot()
    # demo()

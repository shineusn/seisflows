
import numpy as np

from seisflows.tools import unix
from seisflows.tools.array import loadnpy, savenpy
from seisflows.tools.code import loadtxt, savetxt

from seisflows.optimize.lib.LBFGS import LBFGS


class LCG:
    """ Generic CG solver
    """
    def __init__(self, path, eta0, lcgmax, precond_type=None):
        self.path = path
        self.eta0 = eta0
        self.lcgmax = lcgmax
        self.precond_type = precond_type

        self.ilcg = 0
        self.iter = 0

        unix.mkdir(self.path+'/'+'LCG')


    def precond(self, r):
        return r


    def initialize(self):
        unix.cd(self.path)
        self.iter += 1
        self.ilcg = 0

        r = loadnpy('g_new')
        x = np.zeros(r.size)
        savenpy('LCG/x', x)
        savenpy('LCG/r', r)

        y = self.precond(r)
        p = -y
        savenpy('LCG/y', y)
        savenpy('LCG/p', p)
        savetxt('LCG/ry', np.dot(r, y))


    def update(self, ap):
        """ performs CG update
        """
        unix.cd(self.path)
        self.ilcg += 1

        x = loadnpy('LCG/x')
        r = loadnpy('LCG/r')
        y = loadnpy('LCG/y')
        p = loadnpy('LCG/p')
        ry = loadtxt('LCG/ry')

        pap = np.dot(p, ap)
        if pap < 0:
            print ' Stopping LCG [negative curvature]'
            isdone = True
            return isdone
                       
        alpha = ry/pap
        x = x + alpha*p
        r = r + alpha*ap
        savenpy('LCG/x', x)
        savenpy('LCG/r', r)

        # check status
        if self.check_status(ap) == 0:
            isdone = True
        elif self.ilcg >= self.lcgmax:
            isdone = True
        else:
            isdone = False

        if not isdone:
            y = self.precond(r)
            ry_old = ry
            ry = np.dot(r, y)
            beta = ry/ry_old
            p = -y + beta*p

            savenpy('LCG/y', y)
            savenpy('LCG/p', p)
            savetxt('LCG/ry', np.dot(r, y))

        return isdone


    def check_status(self, ap, eta=0.9999, verbose=True):
        """ Checks Eisenstat-Walker termination status
        """
        g = loadnpy('g_new')
        LHS = np.linalg.norm(g+ap)
        RHS = np.linalg.norm(g)

        # for comparison, calculate forcing term proposed by 
        # Eisenstat & Walker 1996
        if self.iter > 1:
            g_new = np.linalg.norm(g)
            g_old = np.linalg.norm(loadnpy('g_old'))
            g_ratio = g_new/g_old
        else:
            g_ratio = np.nan

        if verbose:
            # print numerical statistics
            print ' k+1/k:', g_ratio
            print ' LHS:  ', LHS
            print ' RHS:  ', RHS
            print ' RATIO:', LHS/RHS
            print ''

        # check termination condition
        if LHS < eta * RHS:
            return 0
        else:
            return 1


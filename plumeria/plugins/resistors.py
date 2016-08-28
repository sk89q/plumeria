import shlex
from math import floor

from plumeria.command import commands, CommandError, ArgumentParser
from plumeria.util.ratelimit import rate_limit


class Combination:
    def __init__(self, value1, value2, op, result, error):
        self.result = result
        self.value1 = value1
        self.value2 = value2
        self.op = op
        self.error = error

    def __str__(self):
        return "{value1: 12.0f} {op:2} {value2: 12.0f} = {result: 10.3f} ({error: 7.5f}%)".format(
            result=self.result,
            value1=self.value1,
            value2=self.value2,
            op=self.op,
            error=self.error * 100
        )

    def __repr__(self):
        return self.__str__()

class ResistorCalculator:
    # Copyright (C) 2001-2010 Claudio Girardi

    def __init__(self):
        self.set_series("E24")

    def set_series(self, series):
        if series == "E12":
            self.Rbase = [1, 1.2, 1.5, 1.8, 2.2, 2.7, 3.3, 3.9, 4.7, 5.6, 6.8, 8.2]
        elif series == "E24":
            self.Rbase = [1, 1.1, 1.2, 1.3, 1.5, 1.6, 1.8, 2.0, 2.2, 2.4, 2.7, 3.0, 3.3, 3.6, 3.9, 4.3, 4.7, 5.1, 5.6,
                          6.2, 6.8, 7.5, 8.2, 9.1]
        elif series == "E96":
            self.Rbase = [1.00, 1.02, 1.05, 1.07, 1.10, 1.13, 1.15, 1.18, 1.21, 1.24, 1.27, 1.30, 1.33, 1.37, 1.40,
                          1.43, 1.47, 1.50, 1.54, 1.58, 1.62, 1.65, 1.69, 1.74, 1.78, 1.82, 1.87, 1.91, 1.96, 2.00,
                          2.05, 2.10, 2.15, 2.21, 2.26, 2.32, 2.37, 2.43, 2.49, 2.55, 2.61, 2.67, 2.74, 2.80, 2.87,
                          2.94, 3.01, 3.09, 3.16, 3.24, 3.32, 3.40, 3.48, 3.57, 3.65, 3.74, 3.83, 3.92, 4.02, 4.12,
                          4.22, 4.32, 4.42, 4.53, 4.64, 4.75, 4.87, 4.99, 5.11, 5.23, 5.36, 5.49, 5.62, 5.76, 5.90,
                          6.04, 6.19, 6.34, 6.49, 6.65, 6.81, 6.98, 7.15, 7.32, 7.50, 7.68, 7.87, 8.06, 8.25, 8.45,
                          8.66, 8.87, 9.09, 9.31, 9.53, 9.76]
        else:
            raise Exception("Invalid resistor series!")

        self.R = []
        for mult in range(0, 7):
            for idx in range(0, len(self.Rbase)):
                # need to round to compensate for pow() errors; allow max two decimals, needed for E96
                self.R.append(round(self.Rbase[idx] * (10 ** mult) * 100) / 100)

        self.n_max = len(self.R) - 1

        # compute the conductances array, lowest conductance first to have an
        # array sorted in ascending order
        self.G = []
        for idx in range(0, self.n_max + 1):
            self.n_max = len(self.R) - 1  # maximum valid index
            self.G.append(1.0 / self.R[self.n_max - idx])

    def find_index(self, vect, value):
        index_min = 0
        index_max = self.n_max + 1
        index = floor((index_min + index_max) / 2)
        i = 0

        while (index_max - index_min) > 1 and (i < 500):
            if vect[index] == value:
                break

            elif vect[index] > value:
                index_max = index
            elif vect[index] < value:
                index_min = index

            index = floor((index_min + index_max) / 2)
            i += 1

        if index < self.n_max:
            tol1 = abs(vect[index] / value - 1.0)
            tol2 = abs(vect[index + 1] / value - 1.0)
            if tol1 < tol2:
                return index
            else:
                return index + 1
        else:
            return index

    def calculate(self, rd):
        i, j, iter = 0, 0, 0  # number of iterations

        results = []

        # compute assuming resistors in series
        # locate nearest approximation with standard resistor values
        r1_idx = self.find_index(self.R, rd)
        r1 = self.R[r1_idx]
        r2 = 0
        rres = r1
        rres_tol = (rres - rd) / rd  # relative tolerance
        best_tol = rres_tol

        results.append(Combination(r1, r2, "+", rres, rres_tol))

        while self.R[r1_idx] >= rd / 2.0:
            iter += 1
            r1 = self.R[r1_idx]

            r2d = rd - r1  # this is the value needed
            if (r2d < 0):
                r1_idx -= 1
                continue  # might happen...

            r2_idx = self.find_index(self.R, r2d)
            r2 = self.R[r2_idx]  # get the nearest standard value
            rres = r1 + r2  # compute the resulting composition
            rres_tol = rres / rd - 1.0  # and its tolerance

            if abs(rres_tol) < abs(best_tol):
                results.append(Combination(r1, r2, "+", rres, rres_tol))

            r1_idx -= 1

        rd = 1.0 / rd

        # compute assuming resistors in parallel
        r1_idx = self.find_index(self.G, rd)
        while self.G[r1_idx] >= rd / 2.1:
            iter += 1
            r1 = self.G[r1_idx]

            r2d = rd - r1  # this is the value needed
            if r2d < 0:
                r1_idx -= 1
                continue  # might happen...

            r2_idx = self.find_index(self.G, r2d)
            r2 = self.G[r2_idx]  # get the nearest standard value
            rres = r1 + r2  # compute the resulting composition
            rres_tol = rd / rres - 1.0  # and its tolerance

            if abs(rres_tol) < abs(best_tol):
                # use values from R array to avoid rounding errors
                # which will lead to something like 6800.0000001...
                results.append(Combination(self.R[self.n_max - r1_idx],  # 1.0 / r1
                                           self.R[self.n_max - r2_idx],  # 1.0 / r2
                                           "||",
                                           1.0 / rres,
                                           rres_tol))

            r1_idx -= 1

        return sorted(results, key=lambda e: abs(e.error))


@commands.register("resistors", category="Electronics")
@rate_limit()
async def resistors(message):
    """
    Finds the best combination of two resistors to achieve a certain value.
    The first parameter is the resistor value to achieve and the second,
    optional, value is the resistor series (choose from E12 (10%), E24 (5%),
    or E96 (1%)).

    Example::

        /resistors 9234
        /resistors 3525 e12

    Response::

        3300 +           220 =   3520.000 (-0.14184%)
        2700 +           820 =   3520.000 (-0.14184%)
        3900 ||        39000 =   3545.455 ( 0.58027%)
        4700 ||        15000 =   3578.680 ( 1.52284%)
        5600 ||        10000 =   3589.744 ( 1.83670%)

    """
    parser = ArgumentParser()
    parser.add_argument("value", type=int)
    parser.add_argument("series", nargs='?', default="E24", choices=['E12', 'E24', 'E96', 'e12', 'e24', 'e95'])
    args = parser.parse_args(shlex.split(message.content))

    calculator = ResistorCalculator()
    calculator.set_series(args.series.upper())
    return "```{}```".format("\n".join(map(str, calculator.calculate(args.value))))

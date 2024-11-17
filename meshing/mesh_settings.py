import pandas as pd
import argparse
from scipy.optimize import fsolve

# Constants that will approximately hold true
RHO = 1.23  # density of air
MU = 1.8 * 10 ** -5  # viscosity of air
N_limits = list(range(10, 26))
MAX_YPLUS = 200
MIN_YPLUS = 30
MIN_LENGTH = 0.1
MAX_LENGTH = 5
MAX_VELOCITY = 1715  # mach 5
MIN_VELOCITY = 1


def calcs(density, viscosity, velocity, length, yplus):
    """
    Calculates the physical properties necessary to determine layer heights
    and BL thickness

    :param density: (float) approximate density of water
    :param viscosity: (float) approximate viscosity of water
    :param velocity: (float) target velocity for target y plus
    :param length: (float) length of rocket
    :param yplus: (float) target y plus value for a mesh
    :returns (float, float):  initial layer height (y1) and boundary layer
        thickness (BL)
    """
    if not MIN_YPLUS < yplus < MAX_YPLUS:
        raise ValueError(f'y+: {yplus} should be '
                         f'{MIN_YPLUS} < y+ < {MAX_YPLUS}')

    if not MIN_LENGTH < length < MAX_LENGTH:
        raise ValueError(f'rocket length: {length} is not in range '
                         f'({MIN_LENGTH, MAX_LENGTH})')

    if not MIN_VELOCITY < velocity < MAX_VELOCITY:
        raise ValueError(f'velocity: {velocity} is not in range '
                         f'({MIN_VELOCITY}, {MAX_VELOCITY})')

    try:
        Re = (density * velocity * length) / viscosity  # reynolds number
        Cf = 0.058 / (Re ** 0.2)  # skin friction coefficient
        Tw = 0.5 * Cf * density * (velocity ** 2)  # wall shear stress
        U = (Tw / density) ** 0.5  # frictional velocity

        # initial layer height - we only go to 2 dp anyway.
        y1 = round((yplus * viscosity) / (density * U), 5)
        BL = (0.37 * length) / (Re ** 0.2)  # boundary layer thickness
    except ZeroDivisionError as divide_by_zero_error:
        raise ValueError(f'Division by zero encountered.') from \
            divide_by_zero_error

    return y1, BL


def f(G, N, y1, BL):
    """
    Function defined to rootfind for
    :param G: (float) inflation layer growth rate
    :param N: (float) number of inflation layers
    :param y1: (float) initial layer height
    :param BL: (float) boundary layer thickness
    """
    y = (y1 * (1 - (G ** N))) / (1 - G) - BL

    return y


def get_table(y1, BL, g_guess=1.1):
    """
    Function defined for rootfinding through fsolve to return dataframe
    : param y1 : (float) initial layer height
    : param BL : (float) boundary layer thickness
    : returns growth rates, number of layers, and initial layers (lists) :
    """
    y1_mm = y1 * 10 ** 3  # convert to mm
    n_layers = []
    g_rates = []
    initial_layers = []

    for N in N_limits:
        parameters = (N, y1, BL)
        g_current = fsolve(f, g_guess, parameters)
        if 1.05 < g_current < 1.3:
            g_rates.append(round(g_current[0], 3))
            n_layers.append(N)
            initial_layers.append(y1_mm)

    table = pd.DataFrame(
        {'Initial Layer Height (mm)': initial_layers,
         'Number of Layers': n_layers,
         'Inflation Growth Rate': g_rates
         })

    return table


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--y_plus', default=100, action='store',
                        help="target y plus value", type=int)
    parser.add_argument('--mach', default=0.5, action='store',
                        help="target velocity by mach number", type=float)
    parser.add_argument('--length', default=3, action='store',
                        help="length of rocket in m", type=float)
    args = parser.parse_args()

    y1, BL = calcs(RHO, MU, args.mach * 343, args.length, args.y_plus)
    table = get_table(y1, BL)

    print(f'To achieve a y_plus value of {args.y_plus}, '
          f'you need one of the following configurations: ')
    print(table)

"""Automatisk retting av FY2-04-ladning-i-magnetfelt.

Hver sjekk i SJEKKER er én deltest, og poengene fordeles likt på dem.
De samme sjekkene ligger i "Test løsningen din"-cellen nederst i notebooken.
"""
import pytest

from notebook_loader import last_notebook

def naer(a, b, rel=1e-3):
    """Sant hvis tallet a er innenfor rel (relativt) av b."""
    try:
        a, b = float(a), float(b)
    except (TypeError, ValueError):
        return False
    if b == 0:
        return abs(a) < 1e-9
    return abs(a - b) <= rel * abs(b)


def S(tekst):
    """Gjør tekst om til et sympy-uttrykk, f.eks. S("x**2 - 1")."""
    import sympy
    return sympy.sympify(tekst, locals={n: sympy.Symbol(n) for n in ("N", "O", "Q", "S")})


def lik(a, b):
    """Sant hvis a og b er matematisk like.

    Lister og mengder sammenlignes uten hensyn til rekkefølge, tupler (koordinater) i rekkefølge.
    """
    import sympy
    if a is None:
        return False
    if isinstance(b, tuple):
        if not isinstance(a, (tuple, list, sympy.Tuple)) or len(a) != len(b):
            return False
        return all(lik(x, y) for x, y in zip(a, b))
    if isinstance(b, (list, set)):
        if isinstance(a, sympy.FiniteSet):
            a = list(a)
        if not isinstance(a, (list, tuple, set)) or len(a) != len(b):
            return False
        rest = list(a)
        for y in b:
            for i, x in enumerate(rest):
                if lik(x, y):
                    del rest[i]
                    break
            else:
                return False
        return True
    if isinstance(b, dict):
        if not isinstance(a, dict) or len(a) != len(b):
            return False
        a = {str(k): v for k, v in a.items()}
        return all(str(k) in a and lik(a[str(k)], v) for k, v in b.items())
    try:
        a, b = sympy.sympify(a), sympy.sympify(b)
    except (sympy.SympifyError, TypeError):
        return False
    vanlige = lambda u: u.subs({s: sympy.Symbol(s.name) for s in u.free_symbols})
    a, b = vanlige(a), vanlige(b)
    if isinstance(a, sympy.Set) or isinstance(b, sympy.Set):
        return a == b
    if getattr(b, "is_Relational", False):
        return a == b
    try:
        return sympy.simplify(a - b) == 0
    except TypeError:
        return a == b

oppgave = last_notebook("oppgave")

SJEKKER = [
    ('1_radius', 'radius for protonet (1e6 m/s, 0.5 T) skal være ca. 2.09 cm', 'naer(radius(1.673e-27, 1e6, 1.602e-19, 0.5), 1.673e-27 * 1e6 / (1.602e-19 * 0.5))'),
    ('1_negativ', 'radius skal være positiv også for negativ ladning', 'naer(radius(9.109e-31, 1e6, -1.602e-19, 0.5), 9.109e-31 * 1e6 / (1.602e-19 * 0.5))'),
    ('1_frekvens', 'syklotronfrekvens for protonet i 0.5 T skal være ca. 7.62 MHz', 'naer(syklotronfrekvens(1.673e-27, 1.602e-19, 0.5), 1.602e-19 * 0.5 / (2 * 3.141592653589793 * 1.673e-27))'),
    ('2', 'masse_fra_radius skal gi |q|B²r²/(2U)', 'naer(masse_fra_radius(1.602e-19, 0.25, 0.124, 2000), 1.602e-19 * 0.0625 * 0.124**2 / 4000)'),
    ('3', 'hastighetsfilter(2e4, 0.1) skal gi 2e5 m/s', 'naer(hastighetsfilter(2e4, 0.1), 2e5)'),
    ('4_diameter', 'den simulerte banen skal ha bredde ca. 2r', '(lambda b: naer(max(b[1]) - min(b[1]), 2 * 1.673e-27 * 1e6 / (1.602e-19 * 0.5), rel=0.01))(simuler_partikkel(1.673e-27, 1.602e-19, 0.5, 1e6, (2 * 3.141592653589793 * 1.673e-27 / (1.602e-19 * 0.5)) / 5000, 5000))'),
    ('4_lukket', 'etter én omløpstid skal partikkelen være nesten tilbake i origo', '(lambda b: (b[0][-1]**2 + b[1][-1]**2)**0.5 < 0.02 * 1.673e-27 * 1e6 / (1.602e-19 * 0.5))(simuler_partikkel(1.673e-27, 1.602e-19, 0.5, 1e6, (2 * 3.141592653589793 * 1.673e-27 / (1.602e-19 * 0.5)) / 5000, 5000))'),
]


@pytest.mark.parametrize(
    "beskrivelse,uttrykk", [s[1:] for s in SJEKKER], ids=[s[0] for s in SJEKKER]
)
def test_sjekk(beskrivelse, uttrykk):
    navnerom = {**vars(oppgave), "naer": naer, "lik": lik, "S": S}
    assert eval(uttrykk, navnerom), beskrivelse

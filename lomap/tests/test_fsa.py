from lomap.classes import Fsa

def test_fsa():
    specs1 = ['F a && F !b']
    specs2 = ['F !a || F b || F !c']
    specs3 = ['F a && F b && F c || F !a']

    for spec in specs:
        aut1 = Fsa()
        aut2 = Fsa()
        aut3 = Fsa()
        aut1.from_formula(spec1)
        aut2.from_formula(spec2)
        aut3.from_formula(spec3)
        print "Aut1"
        print aut1
        print "Aut2"
        print aut2
        print "Aut3"
        print aut3

        print "Bitmap of aut2"
        print aut2.bitmap_of_props({'a':1, 'b':2})
        print "Symbols of aut2 without c"
        print aut3.symbols_wo_prop('c')

        print "Next States of aut3 starting at a"
        print aut3.nextstates('a', {'a':1, 'b':2, 'c':3})
        print "Trap state added to aut3"
        print aut3.add_trap_state()
        print "Deterministic form of aut3"
        print aut3.determinize()

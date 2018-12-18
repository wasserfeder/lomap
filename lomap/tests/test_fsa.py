from lomap.classes import Fsa


def test_fsa():
	specs1 = ['F a && F !b']
	specs2 = ['F !a || F b || F !c']
	specs3 = ['F a && F b && F c || F !a']
	all_specs = [specs1, specs2, specs3]

	for spec in specs1:
		aut1 = Fsa()
		aut1.from_formula(spec)
		print "Aut1"
		print aut1
		print "Bitmap of aut1"
		print aut1.bitmap_of_props({'a':1, 'b':2})
		print "Symbols of aut1 without b"
		print aut1.symbols_wo_prop('b')

		print "Next States of aut3 starting at a"
		print aut1.next_states('a', {'a':1, 'b':2})
		print "Trap state added to aut1"
		print aut1.add_trap_state()



	for spec in specs2:
		aut2 = Fsa()
		aut2.from_formula(spec)
		print "Aut2"
		print aut2
		print "Bitmap of aut2"
		print aut1.bitmap_of_props({'a':1, 'b':2, 'c':3})

		#print "Deterministic form of aut2"
		#print aut2.determinize()

	for spec in specs3:
		aut3 = Fsa()
		aut3.from_formula(spec)
		print "Aut3"
		print aut3
		print "Bitmap of aut3"
		print aut1.bitmap_of_props({'a':1, 'b':2})
		print "Symbols of aut3 without a"
		print aut1.symbols_wo_prop('a')


if __name__ == '__main__':
	test_fsa()

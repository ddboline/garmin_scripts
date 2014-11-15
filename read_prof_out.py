import pstats
stats = pstats.Stats( 'prof.out' )
stats.strip_dirs().sort_stats('time').reverse_order().print_stats()
#stats.strip_dirs().sort_stats('ncalls').reverse_order().print_stats()
#stats.strip_dirs().sort_stats('cumtime').reverse_order().print_stats()

#stats.print_callees('_get_elements_by_tagName_helper')
#stats.print_callers('_get_elements_by_tagName_helper')
#stats.print_callees('Parse')
#stats.print_callers('Parse')

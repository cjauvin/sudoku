from collections import defaultdict
from copy import deepcopy
import math, random

class Sudoku:
    
    def __init__(self, conf, graph_file=None):        
        self.grid = defaultdict(lambda: defaultdict(int))
        self.rows = defaultdict(set)
        self.cols = defaultdict(set)
        self.boxes = defaultdict(set)
        self.size = int(math.sqrt(len(conf))) # note that the number of squares is size^2
        self.recursion_depth = 0
        for i in range(self.size):
            for j in range(self.size):
                v = conf[(i * self.size) + j]
                if v.isdigit():
                    self.set(i, j, int(v))                
        self.recursion_depth = 0 # was updated by init, needs to be reset
        self.n_calls = 0        
        self.graph_file = open(graph_file, 'w') if graph_file else None
        if self.graph_file:
            self.graph_file.write('digraph g {\n')
            self.graph_file.write('rankdir=LR\n')

    def set(self, i, j, v):
        self.grid[i][j] = v
        if v > 0:
            self.rows[i].add(v)
            self.cols[j].add(v)
            self.boxes[self.box(i, j)].add(v)
        self.recursion_depth += 1

    def unset(self, i, j):
        v = self.grid[i][j]
        self.rows[i].remove(v)
        self.cols[j].remove(v)
        self.boxes[self.box(i, j)].remove(v)
        self.grid[i][j] = 0
        self.recursion_depth -= 1

    def isValid(self, i, j, v):
        return not (v in self.rows[i] or 
                    v in self.cols[j] or 
                    v in self.boxes[self.box(i, j)])

    def areRelated(self, i0, j0, i1, j1):
        return (i0 == i1) or \
               (j0 == j1) or \
               (self.box(i0, j0) == self.box(i1, j1))

    def getOccupancy(self, i, j):
        return (self.size * 3) - (len(self.rows[i]) + len(self.cols[j]) + len(self.boxes[self.box(i, j)]))

    def writeToGraphFile(self, prev, curr):
        if self.recursion_depth > 5: return
        node1_id = 'node_%s_%s_%s_%s' % prev
        node1_str = '%s [label="%s,%s,%s"]\n' % tuple([node1_id] + list(prev)[1:])
        node2_id = 'node_%s_%s_%s_%s' % curr
        node2_str = '%s [label="%s,%s,%s"]\n' % tuple([node2_id] + list(curr)[1:])
        self.graph_file.write(node1_str)
        self.graph_file.write(node2_str)
        self.graph_file.write('%s -> %s\n' % (node1_id, node2_id))

    def solveNaive(self, i=0, j=0):
        self.n_calls += 1
        solved = False
        prev = (self.n_calls, i, j, self.grid[i][j]) if (i,j) != (0,0) else None
        while self.grid[i][j] and not solved:
            j += 1
            if j % self.size == 0:
                i += 1
                j = 0
            solved = (i >= self.size)
        if solved:
            return True
        #print i, j, [v for v in range(1, self.size+1) if self.isValid(i, j, v)]
        for v in range(1, self.size+1):
            if self.isValid(i, j, v):
                if self.graph_file and prev:
                    self.writeToGraphFile(prev, (self.n_calls+1, i, j, v))
                self.set(i, j, v)
                if self.solveNaive(i, j):
                    return True
                self.unset(i, j)
        return False
        
    def solve(self, i=None, j=None):
        self.n_calls += 1
        prev = (self.n_calls, i, j, self.grid[i][j]) if (i,j) != (None,None) else None
        nopts = {} # n options -> (opts, (i,j))
        for i in range(self.size):
            for j in range(self.size):
                if self.grid[i][j]: continue
                opts_ij = []
                for v in range(1, self.size+1):
                    if self.isValid(i, j, v):
                        opts_ij.append(v)
                g = self.getOccupancy(i, j)
                h = len(opts_ij)
                #nopts[g] = (opts_ij, (i,j))
                nopts[len(opts_ij)] = (opts_ij, (i,j))
        if nopts:
            opts_ij, (i,j) = min(nopts.items())[1]
            for v in opts_ij:
                if self.graph_file and prev:
                    self.writeToGraphFile(prev, (self.n_calls+1, i, j, v))
                self.set(i, j, v)
                if self.solve(i, j): 
                    return True
                self.unset(i, j)
            return False
        return True

    def solveMoreConstrained(self, i0=None, j0=None):
        self.n_calls += 1
        prev = (self.n_calls, i0, j0, self.grid[i0][j0]) if (i0,j0) != (None,None) else None
        nopts = {} # (n options, relatedness factor) -> (opts, (i,j))
        for i in range(self.size):
            for j in range(self.size):
                if self.grid[i][j]: continue
                opts_ij = []
                for v in range(1, self.size+1):
                    if self.isValid(i, j, v):
                        opts_ij.append(v)     
                ij_relatedness_factor = 0 if prev and self.areRelated(i0, j0, i, j) else 1
                nopts[(len(opts_ij), ij_relatedness_factor)] = (opts_ij, (i,j))
        if nopts:
            opts_ij, (i,j) = min(nopts.items())[1]
            for v in opts_ij:
                if self.graph_file and prev:
                    self.writeToGraphFile(prev, (self.n_calls+1, i, j, v))
                self.set(i, j, v)
                if self.solveMoreConstrained(i, j): 
                    return True
                self.unset(i, j)
            return False
        return True

    def solveWithLessRecursion(self):
        self.n_calls += 1
        single_value_ijs = []
        while True:
            nopts = {} # n options -> (opts, (i,j))
            for i in range(self.size):
                for j in range(self.size):
                    if self.grid[i][j]: continue
                    opts_ij = []
                    for v in range(1, self.size+1):
                        if self.isValid(i, j, v):
                            opts_ij.append(v)
                    nopts[len(opts_ij)] = (opts_ij, (i,j))
            if nopts:
                opts_ij, (i,j) = min(nopts.items())[1]
                if len(opts_ij) == 1:
                    self.set(i, j, opts_ij[0])
                    single_value_ijs.append((i,j))
                    continue
                for v in opts_ij:
                    self.set(i, j, v)
                    if self.solveWithLessRecursion(): 
                        return True
                    self.unset(i, j)
                for i, j in single_value_ijs:
                    self.unset(i, j)
                return False
            return True

    def solveMoreConstrainedWithLessRecursion(self, i0=None, j0=None):
        self.n_calls += 1
        single_value_ijs = []
        while True:
#            prev = (self.n_calls, i, j, self.grid[i][j]) if (i,j) != (None,None) else None
            nopts = {} # (n options, relatedness factor) -> (opts, (i,j))
            for i in range(self.size):
                for j in range(self.size):
                    if self.grid[i][j]: continue
                    opts_ij = []
                    for v in range(1, self.size+1):
                        if self.isValid(i, j, v):
                            opts_ij.append(v)     
                    ij_relatedness_factor = 0
                    if i0 is not None and j0 is not None:
                        ij_relatedness_factor = 0 if self.areRelated(i0, j0, i, j) else 1
                    nopts[(len(opts_ij), ij_relatedness_factor)] = (opts_ij, (i,j))
            if nopts:
                opts_ij, (i,j) = min(nopts.items())[1]
                if len(opts_ij) == 1:
                    self.set(i, j, opts_ij[0])
                    single_value_ijs.append((i,j))
                    i0, j0 = i, j
                    continue
                for v in opts_ij:
                    # if self.graph_file and prev:
                    #     self.writeToGraphFile(prev, (self.n_calls+1, i, j, v))
                    self.set(i, j, v)
                    if self.solveMoreConstrainedWithLessRecursion(i, j): 
                        return True
                    self.unset(i, j)
                for i, j in single_value_ijs:
                    self.unset(i, j)
                return False
            return True

    # not a valid technique, but I don't understand exactly why
    def solveFull(self):
        self.n_calls += 1
        nopts = defaultdict(list)
        for i in range(self.size):
            for j in range(self.size):
                if self.grid[i][j]: continue
                opts_ij = []
                for v in range(1, self.size+1):
                    if self.isValid(i, j, v):
                        opts_ij.append(v)
                nopts[len(opts_ij)].append((opts_ij, (i,j)))
        if nopts:
            for n, opts_list in sorted(nopts.items(), reverse=False):
                for opts_ij, (i,j) in opts_list:
                    for v in opts_ij:
                        self.set(i, j, v)
                        if self.solveFull(): 
                            return True
                        self.unset(i, j)
            return False
        return True

    def solveRandom(self):
        self.n_calls += 1
        rnd_opts_ij = []
        for i in range(self.size):
            for j in range(self.size):
                if self.grid[i][j]: continue
                opts_ij = []
                for v in range(1, self.size+1):
                    if self.isValid(i, j, v):
                        opts_ij.append(v)
                rnd_opts_ij.append((opts_ij, (i,j)))
        if rnd_opts_ij:
            opts_ij, (i, j) = random.choice(rnd_opts_ij)
            for v in opts_ij:
                self.set(i, j, v)
                if self.solveRandom(): 
                    return True
                self.unset(i, j)
            return False
        return True

    # yields solved copies of self
    def solveAll(self):
        self.n_calls += 1
        nopts = {} # n options -> (opts, (i,j))
        for i in range(self.size):
            for j in range(self.size):
                if self.grid[i][j]: continue
                opts = []
                for v in range(1, self.size+1):
                    if self.isValid(i, j, v):
                        opts.append(v)
                nopts[len(opts)] = (opts, (i,j))
        if nopts:
            opts, (i,j) = min(nopts.items())[1]
            for v in opts:
                self.set(i, j, v)
                for S in self.solveAll():
                    yield S
                self.unset(i, j)
        else:
            yield deepcopy(self)            
            
    def show(self, pretty=True):
        if not pretty:
            grid_list = []
            for i in range(self.size):
                for j in range(self.size):
                    grid_list.append(self.grid[i][j])
            print grid_list
            return
        for i in range(self.size):
            for j in range(self.size):
                print '%s ' % self.grid[i][j] if self.grid[i][j] else '. ',                  
                if self.size == 9 and j in [2, 5]: print '| ',
            print
            if self.size == 9 and i in [2, 5]:
                print '---------+-----------+---------'

    def isSolved(self):
        rows_ok = len(self.rows) == self.size and all([len(self.rows[i]) == self.size for i in self.rows])
        cols_ok = len(self.cols) == self.size and all([len(self.cols[j]) == self.size for j in self.cols])
        boxes_ok = len(self.boxes) == self.size and all([len(self.boxes[k]) == self.size for k in self.boxes])
        return rows_ok and cols_ok and boxes_ok

    def box(self, i, j):
        if self.size == 9:
            return ((i // 3) * 3) + (j // 3)
        elif self.size == 6:
            return ((i // 2) * 2) + (j // 3)
        elif self.size == 8:
            return ((i // 2) * 2) + (j // 4)
        assert False

# 6x6
#s = '624005000462000536306000201050005000'

# easy 8x8
#s = '6820751335170280000200600460007000000000260100370000000000701400'

# hard 8x8
#s =  '0000001006008000003008011065743200004000400001803106024820040003'

# 52 calls [wikipedia]
#s = '530070000600195000098000060800060003400803001700020006060000280000419005000080079'

# 54 calls
#s = "080007095010020000309581000500000300400000006006000007000762409000050020820400060"

# 8.8K calls, naive: 300522 calls, 3.407 secs
s = "120400300300010050006000100700090000040603000003002000500080700007000005000000098"

# 11K calls [wikipedia "near worst case"], naive: 69175317 calls in 803.392 secs
#s = "..............3.85..1.2.......5.7.....4...1...9.......5......73..2.1........4...9"

# 21K calls [norvig]
#s = "4.....8.5.3..........7......2.....6.....8.4......1.......6.3.7.5..2.....1.4......"

# should yield 6 solutions
#s = "300000080001093000040780003093800012000040000520006790600021040000530900030000051"

# http://zonkedyak.blogspot.com/2006/11/worlds-hardest-sudoku-puzzle-al.html
#s = '100007090030020008009600500005300900010080002600004000300000010040000007007000300'

#S = Sudoku(s, '6x6_solveNaive.dot')
S = Sudoku(s, 'graph.dot')
#print
#S.show()

S.solve()
#S.solveNaive()
#S.solveRandom()
#S.solveMoreConstrained()
#S.solveWithLessRecursion()
#S.solveMoreConstrainedWithLessRecursion()

assert S.isSolved()
#print; print
S.show()

S.graph_file.write('}\n')
S.graph_file.close()

# for i, T in enumerate(S.solveAll(), 1):
# #    print 'solution %s:' % i
# #    print
#     T.show(pretty=False)
#     assert T.isSolved()

print
print '(solved in %s calls)' % S.n_calls
#print
# print '==============================='
# print
# S.show()

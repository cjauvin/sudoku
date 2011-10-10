from collections import defaultdict
from copy import deepcopy
import math, random

# helper functions to go with the CP code
def cross(A, B):
    return [(a,b) for a in A for b in B]

def c(i, j):
    return 'ABCDEFGHI'[i] + str(j+1)

class Sudoku:

    # thos static variables are needed for the CP solver, which creates many Sudoku instances
    graph_file = None
    n_calls = 0
    
    def __init__(self, conf, graph_file=None, propagate_constraints=False):        
        self.grid = defaultdict(lambda: defaultdict(int))
        self.rows = defaultdict(set)
        self.cols = defaultdict(set)
        self.boxes = defaultdict(set)
        self.box_coords = [cross(rs, cs) for rs in ([0,1,2], [3,4,5], [6,7,8]) for cs in ([0,1,2], [3,4,5], [6,7,8])]        
        self.size = int(math.sqrt(len(conf))) # note that the number of squares is size^2
        self.values = range(1, self.size + 1)
        self.recursion_depth = 0
        for i in range(self.size):
            for j in range(self.size):
                v = conf[(i * self.size) + j]
                if v.isdigit() and v != '0':
                    self.set(i, j, int(v), propagate_constraints)
        self.recursion_depth = 0 # was updated by init, needs to be reset
        self.n_calls = 0        
        # self.graph_file = open(graph_file, 'w') if graph_file else None
        # if self.graph_file:
        #     self.graph_file.write('digraph g {\n')
        #     self.graph_file.write('rankdir=LR\n')
    
    def set(self, i, j, v, propagate_constraints=False):

        self.grid[i][j] = v
        self.rows[i].add(v)
        self.cols[j].add(v)
        self.boxes[self.box(i, j)].add(v)
        self.recursion_depth += 1
    
        if propagate_constraints:

            for a in range(self.size):
                row_places = defaultdict(list) 
                row_available = set(self.values)
                col_places = defaultdict(list) 
                col_available = set(self.values)
                box_places = defaultdict(list) 
                box_available = set(self.values)
                for b in range(self.size):
                    options = []
                    row_available.discard(self.grid[a][b])
                    col_available.discard(self.grid[b][a])
                    bi, bj = self.box_coords[a][b]
                    box_available.discard(self.grid[bi][bj])
                    for vv in self.values:
                        if not self.grid[a][b] and self.isValid(a, b, vv):
                            options.append(vv)
                            row_places[vv].append(b)
                        if not self.grid[b][a] and self.isValid(b, a, vv):
                            col_places[vv].append(b)
                        if not self.grid[bi][bj] and self.isValid(bi, bj, vv):
                            box_places[vv].append((bi,bj))
                    if not self.grid[a][b]:
                        if len(options) == 0: 
                            return False
                        elif len(options) == 1:
                            # square with single choice found
                            return self.set(a, b, options[0], propagate_constraints)
                if row_available != set(row_places.keys()): return False
                if col_available != set(col_places.keys()): return False
                if box_available != set(box_places.keys()): return False
                for vv, cols in row_places.items():
                    if len(cols) == 1:                       
                        # row with with single place value found
                        return self.set(a, cols[0], vv, propagate_constraints)
                for vv, rows in col_places.items():
                    if len(rows) == 1:                        
                        # col with with single place value found
                        return self.set(rows[0], a, vv, propagate_constraints)
                for vv, boxes in box_places.items():
                    if len(boxes) == 1:
                        # box with with single place value found
                        return self.set(boxes[0][0], boxes[0][1], vv, propagate_constraints)
                                                
            return True

    def unset(self, i, j):
        v = self.grid[i][j]
        self.rows[i].remove(v)
        self.cols[j].remove(v)
        self.boxes[self.box(i, j)].remove(v)
        self.grid[i][j] = 0
        self.recursion_depth -= 1

    def box(self, i, j):
        if self.size == 9:
            return ((i // 3) * 3) + (j // 3)
        elif self.size == 6:
            return ((i // 2) * 2) + (j // 3)
        elif self.size == 8:
            return ((i // 2) * 2) + (j // 4)
        assert False

    def isValid(self, i, j, v):
        return not (v in self.rows[i] or 
                    v in self.cols[j] or 
                    v in self.boxes[self.box(i, j)])

    def isSolved(self):
        rows_ok = len(self.rows) == self.size and all([len(self.rows[i]) == self.size for i in self.rows])
        cols_ok = len(self.cols) == self.size and all([len(self.cols[j]) == self.size for j in self.cols])
        boxes_ok = len(self.boxes) == self.size and all([len(self.boxes[k]) == self.size for k in self.boxes])
        return rows_ok and cols_ok and boxes_ok

    # Graphviz dot file
    def writeToGraphFile(self, prev, curr):
        if self.recursion_depth > 5: return
        node1_id = 'node_%s_%s_%s_%s' % prev
        node1_str = '%s [label="%s,%s,%s"]\n' % tuple([node1_id] + list(prev)[1:])
        node2_id = 'node_%s_%s_%s_%s' % curr
        node2_str = '%s [label="%s,%s,%s"]\n' % tuple([node2_id] + list(curr)[1:])
        Sudoku.graph_file.write(node1_str)
        Sudoku.graph_file.write(node2_str)
        Sudoku.graph_file.write('%s -> %s\n' % (node1_id, node2_id))

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

    def solveSequential(self, i=0, j=0):
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
        for v in self.values:
            if self.isValid(i, j, v):
                if self.graph_file and prev:
                    self.writeToGraphFile(prev, (self.n_calls+1, i, j, v))
                self.set(i, j, v)
                if self.solveSequential(i, j):
                    return True
                self.unset(i, j)
        return False

    def solveRandomly(self):
        self.n_calls += 1
        available_ijs = []
        for i in range(self.size):
            for j in range(self.size):
                if self.grid[i][j]: continue
                available_ijs.append((i, j))
        if not available_ijs:
            return True    
        i, j = random.choice(available_ijs)
        opts_ij = []
        for v in self.values:
            if self.isValid(i, j, v):
                opts_ij.append(v)
        for v in opts_ij:
            self.set(i, j, v)
            if self.solveRandomly(): 
                return True
            self.unset(i, j)
        return False
        
    def solveGreedilyStopEarlier(self, i=None, j=None):
        self.n_calls += 1
        prev = (self.n_calls, i, j, self.grid[i][j]) if (i,j) != (None,None) else None
        nopts = {} # n options -> (opts, (i,j))
        single_found = False
        for i in range(self.size):
            for j in range(self.size):
                if self.grid[i][j]: continue
                opts_ij = []
                for v in self.values:
                    if self.isValid(i, j, v):
                        opts_ij.append(v)
                n = len(opts_ij) 
                if n == 0: return False
                nopts[n] = (opts_ij, (i,j))
                if n == 1:
                    single_found = True
                    break
            if single_found:
                break
        if nopts:
            opts_ij, (i,j) = min(nopts.items())[1]
            for v in opts_ij:
                if self.graph_file and prev:
                    self.writeToGraphFile(prev, (self.n_calls+1, i, j, v))
                self.set(i, j, v)
                if self.solveGreedilyStopEarlier(i, j): 
                    return True
                self.unset(i, j)
            return False
        return True

    def solveGreedilyStopEarlierWithLessRecursion(self):
        self.n_calls += 1
        single_value_ijs = []
        while True:
            nopts = {} # n options -> (opts, (i,j))
            single_found = False
            for i in range(self.size):
                for j in range(self.size):
                    if self.grid[i][j]: continue
                    opts_ij = []
                    for v in self.values:
                        if self.isValid(i, j, v):
                            opts_ij.append(v)
                    n = len(opts_ij) 
                    if n == 0: 
                        for i, j in single_value_ijs:
                            self.unset(i, j)
                        return False
                    nopts[n] = (opts_ij, (i,j))
                    if n == 1:
                        single_found = True
                        break
                if single_found:
                    break
            if nopts:
                opts_ij, (i,j) = min(nopts.items())[1]
                if single_found:
                    self.set(i, j, opts_ij[0])
                    single_value_ijs.append((i,j))
                    continue
                for v in opts_ij:
                    self.set(i, j, v)
                    if self.solveGreedilyStopEarlierWithLessRecursion(): 
                        return True
                    self.unset(i, j)
                for i, j in single_value_ijs:
                    self.unset(i, j)
                return False
            return True

    # For puzzles with many solutions: yields solved copies of self
    def solveAll(self):
        self.n_calls += 1
        nopts = {} # n options -> (opts, (i,j))
        for i in range(self.size):
            for j in range(self.size):
                if self.grid[i][j]: continue
                opts = []
                for v in self.values:
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

    def solveGreedilyWithConstraintPropagation(self, i=None, j=None):
        Sudoku.n_calls += 1
#        prev = (Sudoku.n_calls, i, j, self.grid[i][j]) if (i,j) != (None,None) else None
        #nopts = {} # n options -> (opts, (i,j))
        nopts_list = defaultdict(list) # n_opts -> [(opts, (i,j)), ..] # use this one to emulate norvig's algo
        for i in range(self.size):
            for j in range(self.size):
                if self.grid[i][j]: continue
                opts_ij = []
                for v in self.values:
                    if self.isValid(i, j, v):
                        opts_ij.append(v)
                n = len(opts_ij) 
                if n == 0: return None
                nopts_list[n].append((opts_ij, (i,j)))
                #nopts[n] = (opts_ij, (i,j))
        if nopts_list:
            opts_ij, (i,j) = min(nopts_list.items())[1][0]
            #opts_ij, (i,j) = min(nopts.items())[1]
            for v in opts_ij:
#                if Sudoku.graph_file and prev:
#                    self.writeToGraphFile(prev, (Sudoku.n_calls+1, i, j, v))
#                print Sudoku.n_calls, i, j, c(i,j), v
                S = deepcopy(self)
                if S.set(i, j, v, propagate_constraints=True):
                    T = S.solveGreedilyWithConstraintPropagation(i, j)
                    if T:
                        return T
                else:
                    Sudoku.n_calls += 1
            return None
        return self

n_calls = 0
# standalone, non-method version
def solveGreedilyWithConstraintPropagation(S):
    global n_calls
    n_calls += 1
    #prev = (self.n_calls, i, j, self.grid[i][j]) if (i,j) != (None,None) else None
    #nopts = {} # n options -> (opts, (i,j))
    nopts_list = defaultdict(list) # n_opts -> [(opts, (i,j)), ..] # use this one to emulate norvig's algo
    for i in range(S.size):
        for j in range(S.size):
            if S.grid[i][j]: continue
            opts_ij = []
            for v in S.values:
                if S.isValid(i, j, v):
                    opts_ij.append(v)
            n = len(opts_ij) 
            if n == 0: return None
            nopts_list[n].append((opts_ij, (i,j)))
            #nopts[n] = (opts_ij, (i,j))

    if not nopts_list:
        return S

    opts_ij, (i,j) = min(nopts_list.items())[1][0]
    #opts_ij, (i,j) = min(nopts.items())[1]
    for v in opts_ij:
        # if self.graph_file and prev:
        #     self.writeToGraphFile(prev, (self.n_calls+1, i, j, v))
        T = deepcopy(S)
        if T.set(i, j, v, propagate_constraints=True):
            U = solveGreedilyWithConstraintPropagation(T)
            if U:
               return U

        else:                            
            n_calls += 1
    return None
            
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

# 8.8K calls, naive: 300522 calls, 3.407 secs, CP=474
s = "120400300300010050006000100700090000040603000003002000500080700007000005000000098"

# 11K calls [wikipedia "near worst case"], naive: 69175317 calls in 803.392 secs
#s = "..............3.85..1.2.......5.7.....4...1...9.......5......73..2.1........4...9"

# 21K calls [norvig]
#s = "4.....8.5.3..........7......2.....6.....8.4......1.......6.3.7.5..2.....1.4......"

# should yield 6 solutions
#s = "300000080001093000040780003093800012000040000520006790600021040000530900030000051"

# http://zonkedyak.blogspot.com/2006/11/worlds-hardest-sudoku-puzzle-al.html
#s = '100007090030020008009600500005300900010080002600004000300000010040000007007000300'

# norvig (no search needed)
#s = '003020600900305001001806400008102900700000008006708200002609500800203009005010300'

# norvig hard1 VERY hard (600K+)
#s  = '.....6....59.....82....8....45........3........6..3.54...325..6..................'

S = Sudoku(s, propagate_constraints=True)

#Sudoku.graph_file = open('graph.dot', 'w') 
#Sudoku.graph_file.write('digraph g {\n')
#Sudoku.graph_file.write('rankdir=LR\n')

#print
S.show()

#S.solveSequential()
#S.solveRandomly()
#S.solveGreedilyStopEarlier()
#S.solveGreedilyStopEarlierWithLessRecursion()
S = S.solveGreedilyWithConstraintPropagation()
#S = solveGreedilyWithConstraintPropagation(S)

print; print
S.show()

assert S.isSolved()

#Sudoku.graph_file.write('}\n')
#Sudoku.graph_file.close()

# for i, T in enumerate(S.solveAll(), 1):
# #    print 'solution %s:' % i
# #    print
#     T.show(pretty=False)
#     assert T.isSolved()

print
#print '(solved in %s calls)' % S.n_calls
print '(solved in %s calls)' % (Sudoku.n_calls)

import sys
import math
import re
import gurobipy as gp
from gurobipy import GRB
import time

class KenKenBox:
    def __init__(self, lines):
        header = re.search(r"([0-9]*) ([+-/*//])", lines[0])
        self.value = int(header.group(1))
        self.operation = header.group(2)

        self.grids = []
        for line in lines[1:]:
            coords = re.search(r"\(([0-9]*), ([0-9]*)\)\n", line)
            self.grids.append(tuple(map(int, coords.groups())))
        print(self.grids)

    def _do_operation(self, values):
        if self.operation == "+":
            return sum(values)
        elif self.operation == "-":
            return max(values) - min(values)
        elif self.operation == "*":
            return math.prod(values)
        elif self.operation == "/":
            if max(values) % min(values) != 0:
                return None
            return int(max(values) / min(values))


    # TODO this is unnecessarily inefficient
    def get_grid_pairings(self, size):
        values = [1] * len(self.grids)

        while True:
            if self._do_operation(values) == self.value:
                yield tuple(values)

            if min(values) == size:
                break

            # Increment one at a time
            values[-1] += 1
            while max(values) > size:
                index = values.index(size + 1)
                values[index] = 1
                values[index - 1] += 1

    @staticmethod
    def from_file_lines(lines):
        box = []
        for line in lines:
            if line == "\n":
                yield KenKenBox(box)
                box = []
            else:
                box.append(line)

    @staticmethod
    def check_dimensions(boxes):
        filled = set()
        dim_x = 0
        dim_y = 0

        for box in boxes:
            for grid in box.grids:
                dim_x = max(dim_x, grid[0])
                dim_y = max(dim_y, grid[1])

                if tuple(grid) in filled:
                    print("ERROR - " + str(grid) + " already filled!")
                filled.add(tuple(grid))

        expected = set()
        for x in range(dim_x + 1):
            for y in range(dim_y + 1):
                expected.add((x, y))

        if filled != expected:
            print("Invalid file!")
            print(expected - filled)

        return (dim_x + 1, dim_y + 1)


if len(sys.argv) < 2:
    print('Usage: solver.py filename')
    sys.exit(0)

with open(sys.argv[1]) as fp:
    boxes = list(KenKenBox.from_file_lines(fp.readlines()))
n = KenKenBox.check_dimensions(boxes)[0]



model = gp.Model('kenken')
vars = model.addVars(n, n, n, vtype=GRB.BINARY, name='G')

model.addConstrs((vars.sum(i, j, '*') == 1
                 for i in range(n)
                 for j in range(n)), name='V')

model.addConstrs((vars.sum(i, '*', v) == 1
                 for i in range(n)
                 for v in range(n)), name='R')

model.addConstrs((vars.sum('*', j, v) == 1
                 for j in range(n)
                 for v in range(n)), name='C')

def combine_grid_with_options(grids, option):
    for grid, value in zip(grids, option):
        yield vars[grid[0], grid[1], value - 1]

for box in boxes:
    options = list(box.get_grid_pairings(n))
    temps = model.addVars(len(options), vtype=GRB.BINARY)
    for i in range(len(options)):
        model.addConstr(temps[i] == gp.and_(*combine_grid_with_options(box.grids, options[i])))

    model.addConstr(temps.sum() == 1)

print("Starting solving")
start_time = time.time() * 10**6
model.optimize()
end_time = time.time() * 10**6
print("Finished solving, took " + str(int(end_time - start_time)) + " us")
model.write('kenken.lp')

solution = model.getAttr('X', vars)
for y in range(n - 1, -1, -1):
    line = ''
    for x in range(n):
        for v in range(n):
            if solution[x, y, v] > 0.5:
                line += str(v + 1) + " "
    print(line)

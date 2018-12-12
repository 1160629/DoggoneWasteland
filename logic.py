
from pygame import Rect as pRect
from itertools import product


# decorator function to loop another function infinitely

def infinite_loop(func):
    def new_func():
        while True:
            func()
    return new_func


# class for box collisions

class Rect(pRect):
    pass


# copy a tree (list-of-lists-of-...) 

def copy(l):
    nl = []
    for i in l:
        if isinstance(i, list):
            nl.append(copy(i))
        else:
            nl.append(i)
    return nl


# range and distance functions

def get_distance(p1, p2):
    x1, y1 = p1
    x2, y2 = p2

    dsq = (x1-x2)**2 + (y1-y2)**2

    return dsq ** 0.5

def in_range(u1, u2, r):
    if get_distance(u1, u2) <= r:
        return True
    return False

one_tile_range = 1.42


# pathfinding

def reconstruct_path(cameFrom, current):
    total_path = [current]
    while current in cameFrom.keys():
        current = cameFrom[current]
        total_path.append(current)
    return total_path

def lowest_fscore_value(fScore, openSet):
    lowest = openSet[0]
    for n in openSet:
        if fScore[n] < fScore[lowest]:
            lowest = n
    #print(lowest.pos)
    return lowest

def heuristic_cost_estimate(n1, n2):
    cost = dist_between(n1, n2)
    return cost

def dist_between(n1, n2):
    x1, y1 = n1.pos
    x2, y2 = n2.pos

    dsq = (x1-x2)**2 + (y1-y2)**2
    return dsq

def A_Star(start, goal):
    #// The set of nodes already evaluated
    closedSet = {}

    discovered = {}

    #// The set of currently discovered nodes that are not evaluated yet.
    #// Initially, only the start node is known.
    openSet = [start]

    #// For each node, which node it can most efficiently be reached from.
    #// If a node can be reached from many nodes, cameFrom will eventually contain the
    #// most efficient previous step.
    cameFrom = {}

    #// For each node, the cost of getting from the start node to that node.
    gScore = {}

    #// The cost of going from start to start is zero.
    gScore[start] = 0

    #// For each node, the total cost of getting from the start node to the goal
    #// by passing by that node. That value is partly known, partly heuristic.
    fScore = {}

    #// For the first node, that value is completely heuristic.
    fScore[start] = heuristic_cost_estimate(start, goal)
    while len(openSet) != 0:
        current = lowest_fscore_value(fScore, openSet)
        if current == goal:
            return reconstruct_path(cameFrom, current)

        n = 0
        for i in openSet:
            if i == current:
                ind = n
                break
            n += 1

        openSet.pop(ind)
        closedSet[current] = True

        for neighbor in current.neighbours:
            in_closed = True
            try:
                closedSet[neighbor]
            except KeyError:
                in_closed = False
            if in_closed:
                continue
            #// The distance from start to a neighbor
            tentative_gScore = gScore[current] + dist_between(current, neighbor)

            in_discovered = True
            try:
                discovered[neighbor]
            except KeyError:
                in_discovered = False
            if not in_discovered:	#// Discover a new node
                discovered[neighbor] = True
                openSet.append(neighbor)
            elif tentative_gScore >= gScore[neighbor]:
                continue		#// This is not a better path.

            #// This path is the best until now. Record it!
            cameFrom[neighbor] = current
            gScore[neighbor] = tentative_gScore
            fScore[neighbor] = gScore[neighbor] + heuristic_cost_estimate(neighbor, goal)

def corrigated_path(unit):
    cpath = []
    ppos = unit.pos
    avail_points = unit.ap.turn_ap
    use_points = []
    for p in unit.path:
        VX, VY = p[0] - ppos[0], p[1] - ppos[1]
        if VX**2 + VY ** 2 == 2:
            move_distance = 1.41
        else:
            move_distance = 1
        ms = unit.get_move_speed()
        use_points.append(move_distance/ms)

        cpath.append(p)

        if avail_points - sum(use_points) <= 0:
            break

    return cpath, use_points

def create_walkable_matrix(cr, units, cu, g_obj, am = None):

    dung = g_obj.dungeon
    rs = dung.adjacent_rooms() + [((0, 0), cr)]

    rw, rh = g_obj.rw, g_obj.rh
    aw, ah = rw * 3, rh * 3
    walk_mat = [[False for y in range(ah)] for x in range(aw)]
    for po, r in rs:
        o = po[0] + 1, po[1] + 1
        ox, oy = rw * o[0], rh * o[1]
        for x, y in product(range(rw), range(rh)):
            rx, ry = ox + x, oy + y
            #print(rx, ry)
            #print(r.grid_pos, rx, ry)
            walk = r.walkable_map[x][y]
            walk_mat[rx][ry] = walk # here is the crash when trying to walk

    for u in units:
        if u == cu:
            continue
        x, y = u.pos
        xd, yd = x//rw, y//rh
        room = cr
        rw, rh = g_obj.rw, g_obj.rh
        gx, gy = room.grid_pos
        rx = x - gx * rw
        ry = y - gy * rh
        if (xd, yd) == (gx, gy):
            walk_mat[rx][ry] = False

    dung = g_obj.dungeon
    doors = dung.doors

    for d in doors:
        if not d.is_closed:
            continue

        g1x, g1y = cr.grid_pos
        g2x, g2y = d.belongs_to.grid_pos

        gx, gy = g2x - g1x, g2y - g1y
        ox = gx * rw
        oy = gy * rh
        for rx, ry in d.get_collidable():
            grx = rx + ox + rw
            gry = ry + oy + rh
            if 0 <= grx < len(walk_mat) and 0 <= gry < len(walk_mat[0]):
                walk_mat[grx][gry] = False

    return walk_mat

class Node:
    def __init__(self, x, y):
        self.pos = x, y
        self.neighbours = []

def get_node_map(walk_mat):
    node_map = [[Node(x, y) for y in range(len(walk_mat[x]))] for x in range(len(walk_mat))]
    nbors = [
        [0, 1],
        [1, 0],
        [0, -1],
        [-1, 0],
        [1, 1],
        [-1, -1],
        [1, -1],
        [-1, 1]
    ]

    for x, y in product(range(len(node_map)), range(len(node_map[0]))):
        if not walk_mat[x][y]:
            continue
        for nbor in nbors:
            nx, ny = x + nbor[0], y + nbor[1]
            if not (0 <= nx < len(node_map) and 0 <= ny < len(node_map[0])):
                continue
            if not walk_mat[nx][ny]:
                continue
            node_map[x][y].neighbours.append(node_map[nx][ny])

    return node_map
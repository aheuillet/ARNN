import numpy as np
import random
import time


def generate_shape(file_in, file_out, size, dim, min, max, seed):#time complexity is quadratic in size, it could be linear, but it would be very heavy for the memory
    if (seed == -1):
        np.random.seed(int(time.time())%1000)
    else:
        np.random.seed(seed)

    inp = []
    out = np.zeros(size, dtype=int)

    for i in range(size):
        inp.append(np.random.randint(min, max, size=dim))

    for i in range(1, size):
        if out[i] == 0:
            for j in range(i+1, size):
                if np.array_equal(inp[i], inp[j]):
                    out[j] = 1
                    break

    with open(file_in, mode='w') as inf:
        buf = ""
        for i in range(len(inp)):
            for j in range(dim-1):
                buf += str(inp[i][j])+","
            buf += str(inp[i][dim-1])+"\n"
        inf.write(buf)
        
    with open(file_out, mode='w') as ouf:
        buf = ""
        for i in range(len(out)):
            buf += str(out[i])+"\n"
        ouf.write(buf)


def generate_n(file_in, file_out, size, dim, min, max, n, seed):
    if (seed == -1):
        np.random.seed(int(time.time())%1000)
    else:
        np.random.seed(seed)

    inp = []

    for a in range(size+n):
        inp.append([])
        for i in range(dim):
            inp[a].append(random.randint(min, max))

    with open(file_in, mode='w') as inf:
        buf = ""
        for i in range(len(inp)-n):
            for j in range(dim-1):
                buf += str(inp[i][j])+","
            buf += str(inp[i][dim-1])+"\n"
        inf.write(buf)
        
    with open(file_out, mode='w') as ouf:
        buf = ""
        for i in range(n,len(inp)):
            for j in range(dim-1):
                buf += str(inp[i][j])+","
            buf += str(inp[i][dim-1])+"\n"
        ouf.write(buf)


generate_n("file_in_1_backing.csv", "file_out_1_backing.csv", 4000, 1, 0, 15, 1, -1)

# generate_shape("file_in.csv", "file_out.csv", 4000, 3, 0, 20, -1)



import numpy as np
import time


def write_csv(file, array, dim, start, stop):
    """This fonction writes an array in csv format.
        Inputs:
        -file: A string containning the name of the csv file.
        -array: A matrix-like array containing the data to be written.
        -dim: The number of colunm that must be written (must be less or equal to the width of the matrix array).
        -start: The index of the first line to be written.
        -stop: The index of the line before the last to be written.
    """
    with open(file, mode='w') as f:
        buf = ""
        for i in range(start, stop):
            for j in range(dim-1):
                buf += str(array[i][j])+","#place commas between the numbers
            buf += str(array[i][dim-1])+"\n"
        f.write(buf)


def set_seed(seed):
    """This fonction initiate the random of numpy with the seed.
       If the seed is set to a negative value, numpy's random is initiated with the time.   
       
        Inputs:
        -seed: An int representing the seed.
    """
    if (seed <= -1):
        np.random.seed(int(time.time())%1000)
    else:
        np.random.seed(seed)


def generate_shape_tracking_array(array, start, stop):#time complexity is in O((stop-start)², it could be linear, but it would be very heavy for the memory
    """This fonction create a numpy array, based on the array given. For every 
        element of the array, inside of the interval [start, stop], a 0 or a 1 
        is associated in the output array. If a vector is present before in 
        the considered interval, the a 1 is associated, otherwise, a 0.  
        
        Inputs:
        -array: A numpy array containing vectors of the same size.
        -start: The index of the first vector of the array to be considered.
        -stop: The index of the last vector of the array to be considered.

        Outputs:
        -out: A numpy array of size stop-start
    """
    out = np.zeros((stop-start, 1), dtype=int)
    for i in range(start+1, stop):
        for j in range(i-1, start-1, -1):#looking at previous values to see if they were identical
            print(i, j)
            if np.array_equal(array[i], array[j]):
                out[i][0] = 1
                break#if an identical value is founded, no need to continue
    
    return out


def generate_shape(file_in, file_out, size, dim, min, max, seed):
    """This fonction create 2 files in csv format. The first contains a serie of vectors that are randomly generated. The second 
        file contains a serie of 0 and 1 of the same size as the first file. A 0 in the second file means that the vector at the 
        same line in the first file as not being seen before in the file. A 1 means that the vector appears at least one time 
        in the first file. 
        
        Inputs:
        -file_in: A string containning the name of the first csv.
        -file_out: A string containning the name of the second csv.
        -size: The length of the files.
        -dim: The number of colunm in the files.
        -min: The minimum numerical value of the vectors to be generated.
        -max: The maximum numerical value of the vectors to be generated.
        -seed: The seed to initialize the random.
    """
    set_seed(seed)

    inp = []

    for i in range(size):
        inp.append(np.random.randint(min, max, size=dim))#generate the data randomly

    out = generate_shape_tracking_array(inp, 0, size)

    write_csv(file_in, inp, dim, 0, len(inp))
    write_csv(file_out, out, 1, 0, len(out))


def generate_n(file_in, file_out, size, dim, min, max, n, seed):
    """This fonction create 2 files in csv format. The first contains a serie of vectors that are randomly generated. The second 
        file contains the same serie but shifted. Meaning that, given a vector in the first file, it will appear at a fix distance 
        later in the second. 
        
        Inputs:
        -file_in: A string containning the name of the first csv.
        -file_out: A string containning the name of the second csv.
        -size: The length of the files.
        -dim: The number of colunm in the files.
        -min: The minimum numerical value of the vectors to be generated.
        -max: The maximum numerical value of the vectors to be generated.
        -n: The shift between two vectors.
        -seed: The seed to initialize the random.
    """
    set_seed(seed)

    inp = []

    for a in range(size+n):
        inp.append(np.random.randint(min, max, size=(dim)))

    write_csv(file_in, inp, dim, 0, len(inp)-n)
    write_csv(file_out, inp, dim, n, len(inp))

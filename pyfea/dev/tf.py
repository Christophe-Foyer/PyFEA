# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

import tensorflow as tf
import numpy as np

tf.compat.v1.enable_eager_execution()

def adjacentfinder(tets, nodes):
    """
    Finds adjacent tetrahedrons using tensorflow.
    """
    
    length = len(nodes)
    
    tetnums = np.arange(tets.shape[0])
    
    tets = tf.constant(tets, dtype=tf.int32)
    tetnums = tf.constant(tetnums, dtype=tf.int32)

    matrix = tf.stack([tets] * tets.shape[0])
    matrix_nums = tf.stack([tetnums] * tets.shape[0])
    
    concat = tf.concat([matrix,
                        tf.stack([tets]*tets.shape[0],axis=1)],
                       axis=2)
    
    vconcat = tf.reshape(concat,
                         [concat.shape[0]*concat.shape[1],concat.shape[2]])
    
    floats = tf.cast(bincount(vconcat, length) > 0, dtype=tf.float32)
    sums = tf.math.reduce_sum(floats, axis=1)
    n = tf.equal(sums, 5)
    
    mask = tf.reshape(n, [tets.shape[0]]*2)
    
    n = tf.ragged.boolean_mask(matrix_nums, mask)
    
    return n.to_list()

#from https://stackoverflow.com/questions/50882282/tensorflow-bincount-with-axis-option
def bincount(arr, length, axis=-1):
  """
  Counts the number of ocurrences of each value along an axis.
  """
  
  mask = tf.equal(arr[..., tf.newaxis], tf.range(length))
  return tf.count_nonzero(mask, axis=axis - 1 if axis < 0 else axis)

if __name__ == "__main__":
#    x = [[2.]]
#    m = tf.matmul(x, x)
#    print("hello, {}".format(m))
    from pyfea.fea.geometry import EntityMesh, SurfaceMesh
    
    sm = SurfaceMesh(filename='../../testfiles/cube.stl')

    em = EntityMesh(sm)
    em.gen_mesh_from_surf(element_size=(1000.0,10.0**22))
#    em.plot()
    
    em.get_adjacent()
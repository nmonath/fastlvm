import time
import pickle
import numpy as np
import scipy as sc
from fastlvm import CoverTree
from fastlvm.covertree import HyperParams
#from d3m.primitives.cmu.fastlvm import CoverTree, KMeans, GMM, LDA, GLDA
#from fastlvm import read_corpus
from sklearn.neighbors import NearestNeighbors
from sklearn.cluster import KMeans as sKMeans
from sklearn.mixture import GaussianMixture

import pdb

gt = time.time
np.random.seed(seed=3)

print('Generate random points')
N=100
K=10
D=1000
means = 20*np.random.rand(K,D) - 10
x = np.vstack([np.random.randn(N,D) + means[i] for i in range(K)])
np.random.shuffle(x)
x = np.require(x, requirements=['A', 'C', 'O', 'W'])
y = np.vstack([np.random.randn(N//10,D) + means[i] for i in range(K)])
y = np.require(y, requirements=['A', 'C', 'O', 'W'])

#pdb.set_trace()

print('======== Checks for Search ==========')
hp = HyperParams(trunc=-1)
ct = CoverTree(hyperparams=hp)
ct.set_training_data(inputs=x)
t = gt()
ct.fit()
b_t = gt() - t
print("Building time:", b_t, "seconds")
    
print('Test Nearest Neighbour: ')
t = gt()
a = ct.produce(inputs=y, k=1)
b_t = gt() - t
print("Query time:", b_t, "seconds")
nbrs = NearestNeighbors(n_neighbors=1, algorithm='brute').fit(x)
distances, indices = nbrs.kneighbors(y)
b = np.squeeze(x[indices])
if np.all(a==b):
    print("Test for Nearest Neighbour passed")
else:
    print("Test for Nearest Neighbour failed")
print()


print('Test k-Nearest Neighbours (k=3): ')
t = gt()
a = ct.produce(inputs=y, k=3)
b_t = gt() - t
print("Query time:", b_t, "seconds")
nbrs = NearestNeighbors(n_neighbors=3, algorithm='brute').fit(x)
distances, indices = nbrs.kneighbors(y)
if np.all(a==x[indices]):
    print("Test for k-Nearest Neighbours passed")
else:
    print("Test for k-Nearest Neighbours failed")
print()

print('Test get/set params: ')
p = ct.get_params()
ct = None
ct_new = CoverTree(hyperparams=hp)
ct_new.set_params(params=p)
a = ct_new.produce(inputs=y, k=3)
if np.all(a==x[indices]):
    print("Test for get/set params passed")
else:
    print("Test for get/set params failed")

#pdb.set_trace()
    
print('======== Checks for Clustering ==========')
print('Building clustering data structures')
skm = sKMeans(K, 'k-means++', 1, 10, verbose=0)
ctm = KMeans(k = K, iters = 10, initial_centres = 'covertree', data = x)
ctm.set_training_data(training_inputs = x, validation_inputs = y)

t = gt()
ctm.fit()
b_t = gt() - t
print("Training time:", b_t, "seconds")
skm.fit(x,y)

a = ctm.evaluate(inputs=y)
b = skm.score(y)
print('Canopy score: ', a)
print('Sklearn score: ', b)
print('Difference: ', a-b)
print()

print('Test get/set params: ')
p = ctm.get_params()
ctm = None
ct_new = KMeans(k = K, iters = 10, initial_centres = 'covertree', data = x)
ct_new.set_params(params=p)
a_new = ct_new.evaluate(inputs=y)
if np.abs(a_new - a) < 1e-9*np.abs(a):
    print("Test for get/set params passed")
else:
    print("Test for get/set params failed")

#pdb.set_trace()

print('======== Checks for GMM ==========')
print('Building clustering data structures')
skm = GaussianMixture(K, covariance_type='diag', max_iter=10, init_params='kmeans', verbose=0)
ctm = GMM(k = K, iters = 10, initial_centres = 'covertree', data = x)
ctm.set_training_data(training_inputs = x, validation_inputs = y)

t = gt()
ct = ctm.fit()
b_t = gt() - t
print("Training time:", b_t, "seconds")
skm.fit(x,y)

a = ctm.evaluate(inputs=y)
b = skm.score(y)
print('Canopy score: ', a)
print('Sklearn score: ', b)
print('Difference: ', a-b)
print()

print('Test get/set params: ')
p = ctm.get_params()
ctm = None
ct_new = GMM(k = K, iters = 10, initial_centres = 'covertree', data = x)
ct_new.set_params(params=p)
a_new = ct_new.evaluate(inputs=y)
if np.abs(a_new - a) < 1e-9*np.abs(a):
    print("Test for get/set params passed")
else:
    print("Test for get/set params failed")

#pdb.set_trace()

print('======== Checks for LDA ==========')
# Load NIPS data
trngdata, vocab = read_corpus('data/nips.train')
testdata, vocab = read_corpus('data/nips.test', vocab)

# Init LDA model
canlda = LDA(k=10, iters=100, vocab=vocab)
canlda.set_training_data(training_inputs=trngdata, validation_inputs=testdata)

# Train LDA model
canlda.fit()

# Test on held out data using learned model
a = canlda.evaluate(inputs=testdata)

# Get topic matrix
tm = canlda.get_topic_matrix()

# Read word|topic distribution from gensim
with open('data/lda_gensim.pkl', 'rb') as f:
    m = pickle.load(f)
np.copyto(tm, m)

# Test on held out data using gensim model
b = canlda.evaluate(inputs=testdata)

print('Canopy score: ', a)
print('Gensim score: ', b)
print('Difference: ', a-b)

print('Test get/set params: ')
p = canlda.get_params()
canlda = None
ct_new = LDA(k=10, iters=100, vocab=vocab)
ct_new.set_params(params=p)
b_new = ct_new.evaluate(inputs=testdata)
if np.abs(b_new - b) < 1e-2*np.abs(a):
    print("Test for get/set params passed")
else:
    print("Test for get/set params failed")
    

print('======== Checks for GLDA ==========')
# Load 20 News data
with open('data/20_news.pkl', 'rb') as f:
    d = pickle.load(f)
    # {'trngdata':trngdata, 'testdata':testdata, 'word_map':word_map, 'word_vec':word_vec}

# Init GLDA model
canglda = GLDA(k=10, iters=10, vocab=d['word_map'], vectors=d['word_vec'])
canglda.set_training_data(training_inputs=d['trngdata'], validation_inputs=d['testdata'])

# Train GLDA model
canglda.fit()

# Test on held out data using learned model
b = canglda.evaluate(inputs=d['testdata'])
print('Canopy score: ', b)

print('Test pickling: ')
p = canglda.get_params()
canglda = None
ct_new = GLDA(k=10, iters=10, vocab=d['word_map'], vectors=d['word_vec'])
ct_new.set_params(params=p)
b_new = ct_new.evaluate(inputs=d['testdata'])
if np.abs(b_new - b) < 1e-2*np.abs(b):
    print("Test for get/set params passed")
else:
    print("Test for get/set params failed")

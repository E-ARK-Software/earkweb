import sys
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import Perceptron
from sklearn.svm import LinearSVC
from sklearn.pipeline import Pipeline
from sklearn.datasets import load_files
from sklearn.cross_validation import train_test_split
from sklearn import metrics
from sklearn.externals import joblib
import os

# load the model - all .pkl files must be in the same folder
clf = joblib.load('newspapers.pkl')

# test data
testfiles = os.listdir('/home/janrn/Development/machinelearning/tests')

# categories
categories = ['AutoMobil', 'Bildung', 'Etat', 'Familie', 'Finanzen', 'Gesundheit', 'Greenlife', 'Immobilien',
              'Inland', 'International', 'Karriere', 'Kultur', 'Lifestyle', 'Meinung', 'Panorama', 'Politik',
              'Reise', 'Sport', 'Stil', 'Technik', 'Web', 'Wirtschaft', 'Wissenschaft']

# predict the class
# for file in testfiles:
#     prediction = clf.predict('/home/janrn/Development/machinelearning/tests/%s' % file)
#     print 'Prediction for %s is: ' % file, prediction

prediction = clf.predict(testfiles)

for file in testfiles:
    print 'The file %s was categorized as %s.' % (file, categories[prediction[testfiles.index(file)]])

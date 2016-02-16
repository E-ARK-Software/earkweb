import sys
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import Perceptron
from sklearn.svm import LinearSVC
from sklearn.pipeline import Pipeline
from sklearn.datasets import load_files
from sklearn.cross_validation import train_test_split
from sklearn import metrics
from sklearn.externals import joblib

# The training data folder must be passed as first argument.
# Subfolders are named according to the subcategories that are represented by the files found inside.
languages_data_folder = '/home/janrn/Development/machinelearning/articles'
dataset = load_files(languages_data_folder)

# Split the dataset in training and test set:
docs_train, docs_test, y_train, y_test = train_test_split(
    dataset.data, dataset.target, test_size=0.5)

# Build a an vectorizer
clf = Pipeline([('vect', TfidfVectorizer(max_df=0.9, min_df=2)),
                ('clf', LinearSVC())])

# fit the pipeline on training data
clf.fit(docs_train, y_train)

# fit pipeline on all the data (no test)
# clf.fit(dataset.data, dataset.target)

# get category names
# print dataset.target_names

# save the model to disk
# joblib.dump(clf, 'newspapers.pkl')

# predict outcome
y_predicted = clf.predict(docs_test)

# # Print the classification report
print(metrics.classification_report(y_test, y_predicted,
                                    target_names=dataset.target_names))

# Plot the confusion matrix
cm = metrics.confusion_matrix(y_test, y_predicted)
print(cm)

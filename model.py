import wave
import numpy as np
import pandas as pd
import pickle
import pywt

# NOW

# TODO: Hardcode all signal objects for all records, speed it all up
# TODO: Add noise classification?
# TODO: Keep adding features 
# TODO: Start using rpy2 to work with alex's code to do regression http://rpy.sourceforge.net/rpy2/doc-dev/html/introduction.html

# LATER

# TODO: Submit DRYRUN entry, entry.zip in folder is ready

# TODO: Deal with weird records....
    # A03509 RRvar1, RRvar2, RRvar3 NaNs
    # A03863 A03812 too
    # A00111, A00269, A00420, A00550, A00692, A01053, A01329 noisy sections
    # A00123, A00119 single inversion

"""
When submitting:
    -remove import plot from all files
    -run compress.sh, verify it included the right files, Include DRYRUN? Include saved Model?
    -make sure setup.sh includes all the right libs
    -make sure dependencies.txt has the right packages
    -make sure entry.zip is formatted correctly
    -(empty setup.sh & add validation folder+F1_score.py temporarily) make sure the whole thing runs without errors, delete pycache/vailidation/F1_score        
"""
"""
When adding features:
    -add a new features = append() line with new feature
    -add a 0 to test and trainmatrix in feature_extract()
"""

"""
When testing:
    -run feature_extract() (uncomment the line below it)
    -run runModel()  (uncomment the line below it)
    -go to score.py and just run the whole file
"""


class Signal(object):
    """
    An ECG/EKG signal

    Attributes:
        name: A string representing the record name.
        sampling rate/freq: the sampling rate Hz and frequency (float)
        data : 1-dimensional array with input signal data
        RPeaks : array of R Peak indices
        RRintervals : array of RR interval lengths
        RRbins : tuple of bin percents
    """

    def __init__(self, name, data, mid_bin_range=(234.85, 276.42)):
        """
        Return a Signal object whose record name is *name*,
        signal data is *data*,
        RRInterval bin range is *mid_bin_range*
        """
        self.name = name
        self.sampling_rate = 300. # 300 hz
        self.sampleFreq = 1/300

        # self.data = wave.discardNoise(data) # optimize this
        self.data = wave.filterSignal(data)
        # self.data = data

        self.RPeaks = wave.getRPeaks(self.data, sampling_rate=self.sampling_rate)

        self.RRintervals = wave.interval(self.RPeaks)
        self.RRbins = wave.interval_bin(self.RRintervals, mid_bin_range)




def saveSignalFeatures():
    """
    This function saves all the features for each signal into a giant dataframe
    This is so we don't have to re-derive the peaks, intervals, etc. for each signal

    Parameters
    ----------
    None

    Returns
    -------
    Saves dataframe as hardcoded_features.csv where each row is a filtered signal with the following features:
        RRbins 3
        RRintervals 1
        Residuals 1
        Wavelet coeff 42
    """
    
    records = wave.getRecords('All')[0]
    returnMatrix = np.array([np.zeros(48)])
    
    for i in records:
        sig = Signal(i, wave.load(i))
        
        features = np.asarray([i]) # record name and data +1 = 1
        
        features = np.append(features, np.asarray(sig.RRbins)) # RR bins +3 = 4
        features = np.append(features, np.var(sig.RRintervals)) # RR interval variance +1 = 5
        features = np.append(features, wave.calculate_residuals(sig.data)) # Residuals +1 = 6
        
        wtcoeff = pywt.wavedecn(sig.data, 'sym5', level=5, mode='constant')
        wtstats = wave.stats_feat(wtcoeff)
        features = np.append(features, wtstats) # Wavelet coefficient stats  +42 = 48
        
        returnMatrix = np.concatenate((returnMatrix, np.asarray([features])))
    
    returnMatrix = np.delete(returnMatrix, (0), axis=0) # get rid of initial np.zeros array
    
    df = pd.DataFrame(returnMatrix)
    df.to_csv('hardcoded_features.csv')

saveSignalFeatures()

def deriveBinEdges(training):
    """
    This function derives bin edges from the normal EKG signals

    Parameters
    ----------
    training : tuple
        tuple of lists of training data record names and labels, first element from wave.getPartitionedRecords()

    Returns
    -------
    edges : tuple
        tuple of bin edge values, i.e. (230,270) to use as mid_bin_range in wave.interval_bin()
    """
    
    lower = 0
    upper = 0
    normals = []
    
    for idx, val in enumerate(training[0]):
        
        if training[1][idx] == 'N':
            normals.append(val)

    for i in normals:
        
        sig = Signal(i, wave.load(i))
        # print("processing " + i)
        tempMean = np.mean(sig.RRintervals)
        tempStd = np.std(sig.RRintervals)
        
        lower += tempMean - tempStd
        upper += tempMean + tempStd
    
    lower = lower/len(normals)
    upper = upper/len(normals)
    
    return (lower,upper)

hardcoded_features = pd.read_csv("harcoded_features.csv")

def getFeaturesHarcoded(name):
    """
    this function extract the features from the attributes of a signal
    it uses the hardcoded csv data for each signal that we saved earlier using saveSignalFeatures()

    Parameters
    ----------
    name : String
        record name

    Returns
    -------
    features : array_like
        a feature array for the given signal

    """
    
    features = np.append(np.asarray(sig.RRbins), np.var(sig.RRintervals)) # RR bins and RR variance +4 = 4
    features = np.append(features, wave.calculate_residuals(sig.data)) # Residuals +1 = 5
    
    wtcoeff = pywt.wavedecn(sig.data, 'sym5', level=5, mode='constant')
    wtstats = wave.stats_feat(wtcoeff)
    #features = np.append(features, wtstats) # Wavelet coefficient stats  +42 = 47
    
    return features

def getFeatures(sig):
    """
    this function extract the features from the attributes of a signal

    Parameters
    ----------
    sig : Signal object
        instantiated signal object of class Signal

    Returns
    -------
    features : array_like
        a feature array for the given signal

    """
    
    features = np.append(np.asarray(sig.RRbins), np.var(sig.RRintervals)) # RR bins and RR variance +4 = 4
    features = np.append(features, wave.calculate_residuals(sig.data)) # Residuals +1 = 5
    
    wtcoeff = pywt.wavedecn(sig.data, 'sym5', level=5, mode='constant')
    wtstats = wave.stats_feat(wtcoeff)
    #features = np.append(features, wtstats) # Wavelet coefficient stats  +42 = 47
    
    return features


def feature_extract():
    """
    this function creates a feature matrix from patitioned data

    Parameters
    ----------
        None

    Returns
    -------
        A pickle dump of the following:
            tuple of tuples:
            test (1/10th of data) tuple:
                testing subset feature matrix, 2D array
                list of record labels N O A ~
                list of record names
            training (9/10th of data) tuple:
                training subset feature matrix, 2D array
                list of record labels N O A ~ 

    """

    records_labels = wave.getRecords('All')
    partitioned = wave.getPartitionedRecords(3) # partition nth 10th
    testing = partitioned[0]
    training = partitioned[1]

    binEdges = deriveBinEdges(training)
    testMatrix = np.array([np.zeros(5)])
    trainMatrix = np.array([np.zeros(5)])

    for i in records_labels[0]:
        data = wave.load(i)
        sig = Signal(i, data, mid_bin_range=binEdges)
        if i in testing[0]:
            testMatrix = np.concatenate((testMatrix, [getFeatures(sig)]))
        elif i in training[0]:
            trainMatrix = np.concatenate((trainMatrix, [getFeatures(sig)]))
            
    testMatrix = np.delete(testMatrix, (0), axis=0) # get rid of zeros array we started with
    trainMatrix = np.delete(trainMatrix, (0), axis=0)
    
    featureMatrix = ((testMatrix, testing[1], testing[0]), (trainMatrix, training[1]))
    
    pickle.dump(featureMatrix, open("feature_matrices", 'wb'))
    
#feature_extract()

def runModel():
    """
    runs an machine learning model on our training_data with features bin1, bin2, bin3, and variance

    Parameters
    ----------
    None    
    
    Returns
    -------
        A pickle dump of the trained machine learning model (svm) and pca model

    """
    
    featureMatrix = pickle.load(open("feature_matrices", 'rb'))
        
    # Split data in train and test data
    data_test  = featureMatrix[0][0]
    answer_test  = np.asarray(featureMatrix[0][1])
    
    data_train = featureMatrix[1][0]
    answer_train = np.asarray(featureMatrix[1][1])
    
    # Creating a PCA model
    from sklearn.decomposition import PCA
    pca = PCA(n_components=1)
    pca.fit(data_train)
    data_train = pca.transform(data_train)
    print(pca.explained_variance_ratio_)
    # TODO: find the components in the explained variance ratio that add up to 0.9 first (see binder notes)
    #       do pca once, get the explained variance ratios, find how many it takes to add up to 0.9, redo PCA
    
    # Create and fit a svm classifier
    from sklearn import svm
    clf = svm.SVC()
    clf.fit(data_train, answer_train)
    data_test = pca.transform(data_test)
    print(np.sum(clf.predict(data_test) == answer_test))
    
    # Create and fit a nearest-neighbor classifier
    from sklearn.neighbors import KNeighborsClassifier
    knn = KNeighborsClassifier()
    knn.fit(data_train, answer_train) 
    KNeighborsClassifier(algorithm='auto',n_neighbors=5,weights='uniform') # try different n_neighbors
    print(np.sum(knn.predict(data_test) == answer_test))
    
    # Save the model you want to use
    pickle.dump(clf, open("model", 'wb'))
    pickle.dump(pca, open("pca", 'wb'))

#runModel()

def get_answer(record, data):
    
    sig = Signal(record, data)
    
    loaded_model = pickle.load(open("model", 'rb'))
    loaded_pca = pickle.load(open("pca", 'rb'))
    features = loaded_pca.transform([getFeatures(sig)])
    result = loaded_model.predict(features)    
    
    return result[0]

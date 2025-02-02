import os
import numpy as np
import tensorflow as tf
from pyswarm import pso
from RBFA import Autoencoder
from sklearn.ensemble import RandomForestClassifier
import pandas as pd
from sklearn.metrics import precision_score,recall_score,f1_score,accuracy_score,roc_auc_score

# Define the input parameters
flags = tf.app.flags
flags.DEFINE_string("dataset_name","AllAML", "the name of the dataset")
flags.DEFINE_string("train_dataset_file", "AllAML_train_data_run_0.csv","dataset file name")
flags.DEFINE_string("train_class_file", "AllAML_train_class_run_0.csv", "classes are in a separate folder")
flags.DEFINE_string("test_dataset_file", "AllAML_test_data_run_0.csv", "dataset file name")
flags.DEFINE_string("test_class_file", "AllAML_test_class_run_0.csv", "classes are in a separate folder")
flags.DEFINE_integer("rep_length", "250", "The length of the  generated representation")
flags.DEFINE_integer("iterations", "2", "max number odf iterations for the pso")
flags.DEFINE_integer("swarm_size", "3", "pso number of particles")


FLAGS = flags.FLAGS


def main(_):
    r = 0
    file_dir = "data/"

    train_data = pd.read_csv(os.path.join(file_dir, FLAGS.train_dataset_file),
                             header=None,
                             dtype={'my_column': np.float64}, na_values=['n/a'])

    train_class = pd.read_csv(os.path.join(file_dir,FLAGS.train_class_file),
                              header=None,
                              dtype={'my_column': np.unicode_}, na_values=['n/a'])
    test_data = pd.read_csv(os.path.join(file_dir,FLAGS.test_dataset_file),
                            header=None,
                            dtype={'my_column': np.float64}, na_values=['n/a'])

    test_class = pd.read_csv(os.path.join(file_dir,FLAGS.test_class_file),
                             header=None,
                             dtype={'my_column': np.unicode_}, na_values=['n/a'])

    iterations = FLAGS.iterations
    swarm_size = FLAGS.swarm_size
    #lb = {learning_rate, num_epochs, patch_size,n_layers}
    lb = np.array([0.00001, 1, 1,1]) # lower_baound limit for the parameters
    ub = np.array([2,10,10,5]) #upper bound limit for the parameters


    best_parameters, best_score = find_parameters(train_data,train_class, test_data, test_class,lb,ub,iterations, swarm_size)
    print(best_parameters, best_score)
#@vectorize(['float32(float32, float32)'], target='cuda') for GPU implementation
def find_parameters(train_data, train_class, test_data, test_class, lb, ub, iterations, swarm_size):
    lb = lb * np.ones([1, lb.shape[0]], np.float32)
    ub = ub * np.ones([1, lb.shape[0]], np.float32)

    args = (train_data,train_class, test_data, test_class)
    # initial population is hard-coded here
    pop = [[np.random.random() * 0.001, np.int(np.random.random() * 1000), np.int(np.random.random() * 10 + 1), np.int(np.random.random() * 10 + 1)],
           [np.random.random() * 0.001, np.int(np.random.random() * 1000), np.int(np.random.random() * 10 + 1), np.int(np.random.random() * 10 + 1)],
           [np.random.random() * 0.001, np.int(np.random.random() * 1000), np.int(np.random.random() * 10 + 1), np.int(np.random.random() * 10 + 1)],
           ]
    initial_population = np.array(pop)

    # print the initial population
    print("[*] initial population: ")
    print(initial_population)
    xopt, fopt = pso(fitness, initial_population,lb,ub, swarmsize=swarm_size, maxiter=iterations, args=args)
    # best_ind.append(xopt)

    return xopt, fopt
def fitness(x, *args):
    ''' returns the fitness of the particles '''
    train_data, train_class,test_data, test_class = args
    training(train_data, test_data, train_class, test_class, x)
    score = classify(train_class, test_class)
    print("score", score)
    return (1/score)


def training( train_data, test_data, train_class, test_class, x):
    r =0
    sess = tf.Session()
    autoencoder_dict_testing = Autoencoder(sess,
                                                   run=r,
                                                   dataset_dir = FLAGS.dataset_name,
                                                   dataset_name= FLAGS.dataset_name+"_RBF_optimized_parameters",
                                                   epochs= np.int(x[1]),#FLAGS.epochs,
                                                   learning_rate= x[0], #FLAGS.learning_rate,
                                                   batch_size= np.int(x[2]), #FLAGS.batch_size,
                                                   n_layers=np.int(x[3]),
                                                   training_data=np.array(train_data.values),
                                                   testing_data=np.array(test_data.values),
                                                   checkpoint_dir="checkpoin/"+FLAGS.dataset_name,
                                                   train=True,
                                                   test=False,
                                                   )


def classify(train_class, test_class):
    i = 0
    # for i in range(n_runs) 
    train_data = pd.read_csv(
        "../../../Documents/newProject/AutoencoderOptimizer/Representations/"+FLAGS.dataset_name+"/"+
        FLAGS.dataset_name+"_RBF_optimized_regu_cluster/run_" + str(
            i) + "/Autoencoder/data_train_reps.csv",
        header=None)
    test_data = pd.read_csv(
        "../../../Documents/newProject/AutoencoderOptimizer/Representations/"+FLAGS.dataset_name"+/"+ 
        FLAGS.dataset_name+"_RBF_optimized_regu_cluster/run_" + str(i) +
        "/Autoencoder/data_test_reps.csv", dtype=float,
        header=None)
    x_train = np.array(train_data.values, np.float32)  #
    class_list = np.array(train_class.values)

    x_test = np.array(test_data.values, np.float32)
    y_test = np.array(test_class.values)

    RF_classifier = RandomForestClassifier(n_estimators=100, criterion='entropy', random_state=24)
    RF_classifier.fit(x_train, class_list[:, 0])
    y_score = RF_classifier.predict(x_test)
    score = accuracy_score(y_test[:, 0], y_score, normalize=True,
                           sample_weight=None)
    return score

if __name__ == "__main__":
    tf.app.run()

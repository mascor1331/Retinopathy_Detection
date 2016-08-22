
import os
import numpy as np
import pandas as pd
from keras.utils import np_utils
from keras.models import Sequential, load_model
from keras.layers import Convolution2D, MaxPooling2D
from keras.layers import Dense, Activation, Flatten, BatchNormalization, Dropout
from keras.callbacks import ModelCheckpoint, EarlyStopping
from models.vgg_nets import conv1, conv0
from models.resnets import resnet_v1
from config import training_config, preprocessing_config
from keras.preprocessing.image import ImageDataGenerator
import matplotlib.pyplot as plt

size = preprocessing_config['size']
config = training_config
nb_train_samples = 22481
nb_validation_samples = 5620


#load model
if config['continue_training'] == True:
    model = load_model(os.path.join('models', 'saved_models', config['model_name']+'.hdf5'))

else:
    model = resnet_v1()


earlystop = EarlyStopping(monitor='val_loss', patience=10, verbose=1, mode='auto')
checkpointer = ModelCheckpoint(filepath=os.path.join('models', 'saved_models', config['model_name']+'.hdf5'), verbose=1, save_best_only=False, monitor='val_loss')

if config['prototype_model'] == True:
    # checks if model overfits one sample
    X_sample = np.load(os.path.join('data', 'X_sample.npy'))
    y_sample = np.load(os.path.join('data', 'y_sample.npy'))
    y_sample = np_utils.to_categorical(y_sample, 5)
    history = model.fit(
            X_sample,
            y_sample,
            batch_size=config['batch_size'],
            nb_epoch=config['nb_epoch'],
            verbose=1,
            callbacks=[checkpointer, earlystop],
            class_weight=config['class_weight'])
else:
    # this is the augmentation configuration we will use for training
    train_datagen = ImageDataGenerator(samplewise_center=True,
                                        rotation_range=20,
                                        width_shift_range=0.2,
                                        height_shift_range=0.2,
                                        zoom_range=0.2,
                                        horizontal_flip=True))

    test_datagen = ImageDataGenerator(samplewise_center=True)

    train_generator = train_datagen.flow_from_directory(
            config['train_data_dir'],
            target_size=preprocessing_config['size'],
            batch_size=config['batch_size'],
            class_mode='categorical')

    validation_generator = test_datagen.flow_from_directory(
            config['validation_data_dir'],
            target_size=preprocessing_config['size'],
            batch_size=config['batch_size'],
            class_mode='categorical')

    history = model.fit_generator(
            train_generator,
            samples_per_epoch=nb_train_samples,
            nb_epoch=config['nb_epoch'],
            validation_data=validation_generator,
            nb_val_samples=nb_validation_samples,
            callbacks=[checkpointer, earlystop],
            class_weight=config['class_weight'],
            nb_worker=4)

# list all data in history
print(history.history.keys())

if config['continue_training'] == True:
    with open(os.path.join('training_history', config['model_name']+'.csv'), 'a') as f:
        pd.DataFrame(history.history).to_csv(f, header=False)

else:
    pd.DataFrame(history.history).to_csv(os.path.join('training_history', config['model_name']+'.csv'))

# summarize history for accuracy
plt.plot(history.history['acc'])
plt.plot(history.history['val_acc'])
plt.title('model accuracy')
plt.ylabel('accuracy')
plt.xlabel('epoch')
plt.legend(['train', 'test'], loc='upper left')
plt.show()

plt.plot(history.history['loss'])
plt.plot(history.history['val_loss'])
plt.title('model loss')
plt.ylabel('loss')
plt.xlabel('epoch')
plt.legend(['train', 'test'], loc='upper left')
plt.show()

import keras    
import glob
from tqdm import tqdm
import os
import cv2
import numpy as np
from keras.preprocessing.image import load_img, img_to_array
from sklearn.model_selection import train_test_split
from keras.utils import to_categorical
from keras.preprocessing.image import ImageDataGenerator
from keras.layers import Conv2D, MaxPool2D, Flatten, Dense
from keras.models import Model
from keras.layers import Input
from keras.optimizers import Adam
from keras.callbacks import ModelCheckpoint
from matplotlib import pyplot as plt


def build_model(inputs):
    x = inputs

    x = Conv2D(filters=20, kernel_size=(5, 5), padding="same", activation="relu", kernel_initializer='he_normal')(x)
    x = MaxPool2D(pool_size=(2, 2), strides=(2, 2))(x)

    x = Conv2D(filters=50, kernel_size=(5, 5), padding="same", activation="relu", kernel_initializer='he_normal')(x)
    x = MaxPool2D(pool_size=(2, 2), strides=(2, 2))(x) 

    x = Flatten()(x)
    x = Dense(500, activation="relu")(x)
    outputs = Dense(num_classes, activation="softmax")(x)

    model = Model(inputs, outputs, name="LeNet")
    model.summary()
  
    return model

num_classes = 32
EPOCHS = 5
BS = 32

train_dirs = glob.glob("./dataset/letters/*")
train_dirs.sort(key = lambda x: int(x.rsplit('/',1)[1]))


data = []
labels = []
for train_dir in tqdm(train_dirs):
    imgPaths = glob.glob(train_dir + "/*.jpg")
    imgPaths.sort()
    for imgPath in tqdm(imgPaths):
        image = load_img(imgPath, target_size=(28, 28), grayscale=True)
        image = img_to_array(image) 
        data.append(image)

        label = imgPath.split(os.path.sep)[-2]
        label = int(label)
        labels.append(label)
        


data = np.array(data, dtype=np.float) / 255.
labels = np.array(labels)

train_input, valid_input, train_target, valid_target = train_test_split(data,
                                                                        labels,
                                                                        test_size=0.25,
                                                                        random_state=123)

train_target = to_categorical(train_target, num_classes)
valid_target = to_categorical(valid_target, num_classes)

aug = ImageDataGenerator(width_shift_range=0.1, height_shift_range=0.1)

input = Input((28, 28, 1))
model = build_model(input)

opt = Adam()
model.compile(loss="categorical_crossentropy", optimizer=opt, metrics=["acc"])

checkpoint = ModelCheckpoint(filepath="model.h5",
                             monitor="val_acc",
                             verbose=1,
                             save_best_only=True)

training_log = model.fit_generator(aug.flow(train_input, train_target, batch_size=BS),
                        steps_per_epoch=len(train_input) // BS,
                        validation_data=[valid_input, valid_target],
                        epochs=EPOCHS,
                        callbacks=[checkpoint])

plt.style.use("ggplot")
plt.figure()
plt.plot(np.arange(EPOCHS), training_log.history["loss"], label="train_loss")
plt.plot(np.arange(EPOCHS), training_log.history["acc"], label="train_acc")
plt.plot(np.arange(EPOCHS), training_log.history["val_loss"], label="val_loss")
plt.plot(np.arange(EPOCHS), training_log.history["val_acc"], label="val_acc")
plt.xlabel("Epochs")
plt.ylabel("loss/accuracy")
plt.title("training plot")
plt.legend(loc="center right")
plt.savefig("training_plot.png")


model.load_weights("model.h5")
testPaths = glob.glob("./dataset/letter_sample_test/*.jpg")
testPaths.sort()
model.save('my_model')

for i, testPath in enumerate(testPaths):
    image = load_img(testPath, target_size=(28, 28), grayscale=True)
    image = img_to_array(image) / 255.
    orig_img = image.copy()
    image = np.expand_dims(image, 0)
    predictions = model.predict(image)[0]
    label = np.argmax(predictions)
    proba = np.max(predictions)
    output = cv2.resize(orig_img, (400, 400))
    # plt.subplot(3, 3, i + 1)
    # plt.imshow(output, cmap="gray")
    # plt.axis("off")
    # plt.title("{}: {:.2f}%".format(label, proba * 100))
    cv2.imshow(label, output)
    cv2.waitkey()

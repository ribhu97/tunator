import tensorflow as tf
from keras import Sequential
from keras.models import Model
from keras.optimizers import Adam
from keras.layers import CuDNNLSTM, Dropout, Dense, Activation, Bidirectional, Reshape, LSTM, Lambda, Input, RepeatVector
from midi_processing import gen_batch_tensor
import os
import numpy as np
from math import floor
import music21

import ipdb


def main():
    dir_ = '../music/mini_classical_violin'
    filepath_list = [os.path.join(dir_, fname) for fname in os.listdir(dir_)]
    batch_size = 5
    sample_range = (64, 1000)
    sample_len = sample_range[1] - sample_range[0]
    n_features = 28
    X_batch, Y_batch = next(gen_batch_tensor(filepath_list, batch_size=5, sample_range=sample_range))

    def build_model(timesteps, hidden_size, n_features):
        reshape = Reshape((1, n_features))
        lstm = CuDNNLSTM(512, return_state=True)
        dense = Dense(n_features)

        X = Input(shape=(timesteps, n_features))
        a0 = Input(shape=(hidden_size,), name='a0')    # initialize hidden state
        c0 = Input(shape=(hidden_size,), name='c0')    # initialize cell state
        a = a0
        c = c0

        outputs = []
        for t in range(timesteps):
            x = Lambda(lambda x: X[:, t, :])(X)
            x = reshape(x)
            a, _, c = lstm(x, initial_state=[a, c])
            out = dense(a)
            outputs.append(out)

        model = Model(inputs=[X, a0, c0], outputs=outputs)
        return model

    hidden_size = 512
    model = build_model(timesteps=sample_len, hidden_size=hidden_size, n_features=n_features)
    opt = Adam(lr=0.01, beta_1=0.9, beta_2=0.999, decay=0.01)
    print(model.summary())
    model.compile(optimizer=opt, loss='categorical_crossentropy', metrics=['accuracy'])

    m = 60
    a0 = np.zeros((batch_size, hidden_size))    # TODO: why batch size?
    c0 = np.zeros((batch_size, hidden_size))    # TODO: why batch size?

    model.fit([X_batch, a0, c0], list(Y_batch), epochs=3)

    # model = Sequential()
    #
    # model.add(LSTM(512, input_shape=(sample_len, n_features), return_sequences=True))    # input_shape=(batch_size, sample_len, n_features)
    # model.add(Dropout(0.2))
    #
    # model.add(LSTM(512))
    # model.add(Dropout(0.2))
    #
    # model.add(Dense(56))
    # model.add(Dropout(0.2))
    #
    # model.add(Dense(28))
    # model.add(Dropout(0.2))

    # model.add(Flatten())

    # model.add(Activation('tanh'))   # TODO: activation expects 2 dims, but rest liked 3

    # opt = tf.keras.optimizers.Adam(lr=1e-3, decay=1e-5)

    # for layer in model.layers:
    #     print(layer.get_output_at(0).get_shape().as_list())

    # model.compile(
    #     optimizer='rmsprop',
    #     loss='categorical_crossentropy',
    #     metrics=['accuracy'],
    # )
    #
    # batches_per_epoch = floor(len(filepath_list) / batch_size)
    # model.fit_generator(tensor_gen, steps_per_epoch=batches_per_epoch, epochs=3)


if __name__ == '__main__':
    main()


    # out_stream = __generate_grammar(model)
    #
    # mf = midi.translate.streamToMidiFile(out_stream)
    # mf.open(out_fn, 'wb')
    # mf.write()
    # mf.close()
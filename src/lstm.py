import tensorflow as tf
from tensorflow.keras.layers import GRU, Input, Embedding, LSTM, Dense, Concatenate, TimeDistributed, Dropout, BatchNormalization, LayerNormalization
from tensorflow.keras.models import Model
import config

def get_model():
    seq_len = config.LstmParameters.seq_len
    num_features = config.LstmParameters.num_features
    inputs = Input(shape=(seq_len, num_features))

    x = LSTM(512, return_sequences=True)(inputs)
    # x = Dropout(0.2)(x)

    x = LSTM(512, return_sequences=True)(x)
    # x = Dropout(0.2)(x)

    x = LSTM(512, return_sequences=False)(x)
    # x = Dropout(0.2)(x)

    x = LayerNormalization()(x)

    x = Dense(256, activation='relu')(x)
    # x = Dropout(0.2)(x)

    out_delta = Dense(1, activation='relu', name='out_delta')(x)
    out_duration = Dense(1, activation='relu', name='out_duration')(x)
    out_zero_delta = Dense(1, activation='sigmoid', name='out_zero_delta')(x)
    out_note = Dense(12, activation='softmax', name='out_note')(x)
    out_octave = Dense(10, activation='softmax', name='out_octave')(x)

    model = Model(inputs=inputs, outputs=[out_delta, out_duration,  out_zero_delta, out_note, out_octave])

    model.compile(
        optimizer='adam',
        loss={
            'out_delta': 'mse',
            'out_duration': 'mse',
            'out_zero_delta': 'binary_crossentropy',
            'out_note': 'categorical_crossentropy',
            'out_octave': 'categorical_crossentropy',
        },
        loss_weights={
            'out_delta': 1.0,
            'out_duration': 1.0,
            'out_zero_delta': 1.0,
            'out_note': 1.0,
            'out_octave': 1.0,
        }
    )

    return model
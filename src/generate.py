from src.lstm import get_model
import config, os, random, pandas as pd, numpy as np, tqdm, pathlib
import tensorflow as tf

def load_model():
    model = get_model()

    model.summary()

    model_weights_path = config.LstmParameters.final_model_path
    try:
        model.load_weights(model_weights_path)
        print("Weights Loaded!")
    except Exception as e:
        raise e

    return model


def preprocess_file(df):
    df['delta_time'] = np.log1p(df['delta_time'])
    df['duration'] = np.log1p(df['duration'])

    df['note'] = df['pitch'] % 12
    df['octave'] = df['pitch'] // 12

    df['zero_delta_time'] = df['delta_time'] == 0
    df["delta_time"] = df["delta_time"].replace(0, pd.NA).ffill()
    df["delta_time"] = df["delta_time"].fillna(0)

    df = df.drop(columns=["pitch"])

    return df


def load_seeds(files=[], k=10):
    """
        Loads k random seeds from csv files, or trys to load given files as seeds
    """
    seeds = []
    file_names = []
    csv_files_path = config.MidiFiles.preprocessed_csv_files

    if len(files) != 0:
        pass
    else:
        file_names = os.listdir(csv_files_path)
        file_names = random.sample(file_names, k)
        
    for p in file_names:
        try:
            pd.set_option("future.no_silent_downcasting", True)
            df = pd.read_csv(csv_files_path / p)
            df = preprocess_file(df)
            seeds.append(df)
        except Exception as e:
            print("Skipping", p, e)

    for name, df in zip(file_names, seeds):
        copied_df = df.copy()
            
        # one-hot encoding the notes
        notes = copied_df["note"].astype(int).values
        notes_onehot = np.eye(12, dtype=np.float32)[notes]  # shape (len, 12)

        # one-hot encoding the octave
        octaves = copied_df["octave"].astype(int).values
        octaves_onehot = np.eye(10, dtype=np.float32)[octaves]  # shape (len, 10)

        # drop old note column and replace with one-hot
        copied_df = copied_df.drop(columns=["note", "octave"])
        data = np.hstack([copied_df.values.astype(np.float32), notes_onehot, octaves_onehot])

        # split features
        X_seq = data[:, :]  # all features
        seq_len = config.LstmParameters.seq_len

        yield (name, X_seq[0:seq_len])


def generate(model, seed_sequence, steps=150):
    seed_sequence = tf.expand_dims(seed_sequence, 0)
    generated_sequence = tf.identity(seed_sequence)
    sequence_length = seed_sequence.shape[1]

    for _ in tqdm.tqdm(range(steps)):
        input_seq = generated_sequence[:, -sequence_length:, :]

        pred_delta, pred_duration, pred_zero_delta, pred_note, pred_octave = model(input_seq)

        # Optionally sample instead of taking raw predictions
        # For categorical note output: sample from softmax distribution
        note_probs = tf.squeeze(pred_note)  # shape (12,)
        note_index = tf.random.categorical(tf.math.log([note_probs]), 1)
        note_onehot = tf.one_hot(tf.squeeze(note_index), depth=12)

        octave_probs = tf.squeeze(pred_octave)  # shape (10,)
        octave_index = tf.random.categorical(tf.math.log([octave_probs]), 1)
        octave_onehot = tf.one_hot(tf.squeeze(octave_index), depth=10)

        # Concatenate all outputs into one step vector
        next_step = tf.concat([
            tf.cast(pred_delta, tf.float32),       # (batch, 1)
            tf.cast(pred_duration, tf.float32),    # (batch, 1)
            tf.cast(pred_zero_delta, tf.float32),   # (batch, 1)
            tf.cast(tf.expand_dims(note_onehot, axis=0), tf.float32), # Add batch dimension
            tf.cast(tf.expand_dims(octave_onehot, axis=0), tf.float32) # Add batch dimension
        ], axis=-1)  # shape (batch, 25) - 1 (pitch) + 12 (note onehot) + 10 (octave onehot) = 25

        generated_sequence = tf.concat(
            [generated_sequence, next_step[:, tf.newaxis, :]], axis=1
        )

    return generated_sequence


def reverse_preprocess_file(df):
    df = df.copy()

    df['delta_time'] = np.expm1(df['delta_time']).round().astype(int)
    df['duration'] = np.expm1(df['duration']).round().astype(int)

    df["velocity"] = 127

    df.loc[df["zero_delta_time"] > 0.5, "delta_time"] = 0

    df['pitch'] = df['octave'] * 12 + df["note"]

    df.drop(["zero_delta_time", 'note', 'octave'], inplace=True, axis=1)

    df = df[['delta_time', 'pitch', 'velocity', 'duration']]

    return df


def trun_back_to_df(generated_sequence, start=0):
    seq = generated_sequence[0].numpy()

    delta_time = seq[start:, 0]
    duration = seq[start:, 1]
    zero_delta_time = seq[start:, 2]
    note_onehot = seq[start:, 3:15] 
    octave = seq[start:, 15:25]

    note = np.argmax(note_onehot, axis=1)
    octave = np.argmax(octave, axis=1)

    df = pd.DataFrame({
        "delta_time": delta_time,
        "duration": duration,
        "zero_delta_time": zero_delta_time,
        "note": note,
        "octave": octave,
    })

    reversed_df = reverse_preprocess_file(df)

    return reversed_df


def save_csvs(df_list, file_names, remove_pervious_generated_csvs=False):
    save_path = config.MidiFiles.generated_csv_path
    pathlib.Path(save_path).mkdir(parents=True, exist_ok=True)

    if remove_pervious_generated_csvs:
        for item in os.listdir(save_path):
            item_path = save_path / item
            os.remove(item_path)

    for name, df in zip(file_names, df_list):
        df.to_csv(save_path / name, index=False)


def main():
    model = load_model()
    seeds = load_seeds(k=1)

    generated_csvs = []
    names = []
    for name, seed in seeds:
        print(f"Generating seed: {name}")
        seq = generate(model, seed, 10)

        csv = trun_back_to_df(seq)
        generated_csvs.append(csv)
        names.append(name)

    save_csvs(generated_csvs, names)
    print("Done!")


if __name__ == "__main__":
    main()
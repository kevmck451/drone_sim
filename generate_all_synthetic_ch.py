


import numpy as np
import pandas as pd
from scipy.io import wavfile
import soundfile as sf
from scipy.interpolate import interp1d
from pymavlink import mavutil




def extract_pwm(log_file):
    # Open the log file
    logfile = mavutil.mavlink_connection(log_file, robust_parsing=True)

    pwm_data = {f"channel_{i}": {"timestamps": [], "pwm_values": []} for i in range(1, 7)}
    first_time = None  # To store the first timestamp for normalization

    while True:
        # Read RCOU messages
        msg = logfile.recv_match(type="RCOU", blocking=False)
        if msg is None:
            break

        # Extract timestamp and PWM values for C1 to C6
        msg_dict = msg.to_dict()
        timestamp = msg_dict["TimeUS"]  # Get raw timestamp in microseconds

        # Initialize first_time on the first message
        if first_time is None:
            first_time = timestamp

        # Normalize timestamp to start at 0 and convert to seconds
        normalized_time = (timestamp - first_time) / 1_000_000.0

        # Append data for each channel
        for i in range(1, 7):
            pwm_data[f"channel_{i}"]["timestamps"].append(normalized_time)
            pwm_data[f"channel_{i}"]["pwm_values"].append(msg_dict.get(f"C{i}", 0))

    print("PWM signals (C1-C6) and timestamps extracted successfully.")
    return pwm_data

def interpolate_sweep_data(pwm_data, sample_rate):
    pwm_values = pwm_data['PWM'].values
    times = pwm_data['Time'].values

    # Convert times to sample indices
    sample_indices = (times * sample_rate).astype(int)

    # Create an interpolator for audio data
    interpolated_audio = interp1d(pwm_values, sample_indices, kind='linear', fill_value='extrapolate')

    return interpolated_audio

def dynamic_hover_variation(pwm_value, min_pwm, max_pwm, current_index, total_indices):
    # Calculate a scaling factor based on the flight progress
    flight_progress = current_index / total_indices  # Progress from 0 to 1

    # Gradually increase hover variation based on progress
    # 0 variation when PWM is minimum, scales to max at mid-flight
    hover_scale = flight_progress * (pwm_value - min_pwm) / (max_pwm - min_pwm)

    return hover_scale * 5  # Scale to maximum variation (5)

def generate_synthetic_audio(pwm_inputs, pwm_audio_file, pwm_timestamps, pwm_times):
    sample_rate, sweep_audio = wavfile.read(pwm_audio_file)
    pwm_data = pd.read_csv(pwm_timestamps)
    pwm_data.columns = ['PWM', 'Time']

    # Interpolate audio indices for PWM values
    interpolated_audio = interpolate_sweep_data(pwm_data, sample_rate)

    window_duration = 0.5  # Window size in seconds
    window_samples = int(window_duration * sample_rate)

    # synthetic_audio = np.zeros(int(pwm_times[-1] * sample_rate))  # Pre-allocate final audio array
    # Determine flight end time based on active PWM values
    # Assume the idle state is the minimum PWM; adjust tolerance as needed.
    idle_pwm = min(pwm_inputs)
    tolerance = 50  # you can adjust this margin based on your data
    active_indices = [i for i, pwm in enumerate(pwm_inputs) if pwm > idle_pwm + tolerance]
    if active_indices:
        last_active_index = active_indices[-1]
        flight_end_time = pwm_times[last_active_index] + window_duration
    else:
        flight_end_time = pwm_times[-1] + window_duration

    # Preallocate synthetic audio using the determined flight end time
    synthetic_audio = np.zeros(int(flight_end_time * sample_rate))

    for i, pwm_value in enumerate(pwm_inputs):
        try:
            # Calculate dynamic hover variation
            hover_variation = dynamic_hover_variation(
                pwm_value, min(pwm_inputs), max(pwm_inputs), i, len(pwm_inputs) - 1
            )

            # Add small random variations during hover
            if i > 0 and pwm_inputs[i] == pwm_inputs[i - 1]:  # Hover detected
                pwm_value += np.random.uniform(-hover_variation, hover_variation)

            # Get interpolated sample index for current PWM
            start_sample = int(interpolated_audio(pwm_value))
            segment_samples = window_samples
            segment = sweep_audio[start_sample:start_sample + segment_samples].astype(np.float32)

            if len(segment) < segment_samples:
                # Zero-pad segment if it's too short
                segment = np.pad(segment, (0, segment_samples - len(segment)))

            # Apply a window function (e.g., Hanning) for overlap blending
            window = np.hanning(segment_samples)
            segment *= window

            # Calculate start position in the synthetic audio
            audio_start = int(pwm_times[i] * sample_rate)
            audio_end = audio_start + segment_samples

            # Add segment to synthetic audio with overlap
            synthetic_audio[audio_start:audio_end] += segment
        except Exception as e:
            # print(f"Error processing PWM {pwm_value:.2f}: {e}")
            pass

    # Normalize and save the final audio
    synthetic_audio = synthetic_audio.astype(np.float32)
    synthetic_audio /= np.max(np.abs(synthetic_audio))
    synthetic_audio = (synthetic_audio * 32767).astype(np.int16)

    return  synthetic_audio




if __name__ == '__main__':

    # filename = 'LightRect'
    # filename = 'LightRectCrazy'
    # filename = 'DenseRectCenterStart'

    filenames = ['DenseRectCornerStart', 'FanPath', 'PolygonBottomStart', 'PolygonCenterStart', 'PolygonTopStart']

    for filename in filenames:

        log_file = f"../Data/Drone_Paths/{filename}.BIN"
        pwm_data = extract_pwm(log_file)

        audio_list = []

        # Generate Synthetic Audio
        for channel in range(1, 7):
            synthetic_pwm = pwm_data[f"channel_{channel}"]["pwm_values"]
            pwm_times = pwm_data[f"channel_{channel}"]["timestamps"]

            pwm_audio_file = "../Data/Sweep Ref 2/motor_sweep.wav"
            pwm_timestamps = "../Data/Sweep Ref 2/sweep pwm times.csv"
            output_file = f"../Data/synthesized/gen 3/synthetic_{filename}_{channel}.wav"

            audio_list.append(generate_synthetic_audio(synthetic_pwm, pwm_audio_file, pwm_timestamps, pwm_times))

        # Mix Channels into One
        max_length = max(audio.shape[0] for audio in audio_list)
        combined_audio = np.zeros(max_length, dtype=np.float32)

        for audio in audio_list:
            # Pad each audio array to the maximum length and add to combined audio
            padded_audio = np.pad(audio, (0, max_length - len(audio)))
            combined_audio += padded_audio

        # Renormalize the combined audio
        combined_audio /= np.max(np.abs(combined_audio))  # Normalize to [-1, 1]
        combined_audio = (combined_audio * 32767).astype(np.int16)  # Convert to 16-bit PCM

        # Save the final combined audio
        output_file = f"../Data/synthesized/gen 4/{filename}_synthetic_FULL.wav"
        sf.write(output_file, combined_audio, 44100)  # Replace with your sample rate if different
        print(f"Saved combined audio to {output_file}")










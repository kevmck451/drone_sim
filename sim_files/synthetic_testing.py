import numpy as np
import pandas as pd
from scipy.io import wavfile
from scipy.signal import resample
import soundfile as sf
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d

def generate_synthetic_pwm():
    idle_pwm = 1020
    hover_pwm = 1400
    max_pwm = 1840
    pwm_sampling_rate = 50  # PWM values per second

    # Define flight phases
    takeoff_duration = 10  # seconds
    hover_duration = 10    # seconds
    forward_duration = 60 # seconds
    landing_duration = 10  # seconds

    flight_duration = takeoff_duration + hover_duration + forward_duration + landing_duration

    # Time array with high sampling rate
    time = np.linspace(0, flight_duration, int(flight_duration * pwm_sampling_rate))

    takeoff_time = time[time <= takeoff_duration]
    takeoff_pwm = np.linspace(idle_pwm, hover_pwm, len(takeoff_time))

    hover_time = time[(time > takeoff_duration) & (time <= takeoff_duration + hover_duration)]
    hover_pwm = np.full(len(hover_time), hover_pwm)

    forward_time = time[(time > takeoff_duration + hover_duration) &
                        (time <= takeoff_duration + hover_duration + forward_duration)]
    forward_pwm = hover_pwm[0] + 50 * np.sin(0.2 * np.pi * (forward_time - forward_time[0]))

    landing_time = time[time > takeoff_duration + hover_duration + forward_duration]
    landing_pwm = np.linspace(hover_pwm[0], idle_pwm, len(landing_time))

    # Combine all PWM values
    pwm = np.concatenate([takeoff_pwm, hover_pwm, forward_pwm, landing_pwm])

    # Plot the PWM sequence
    plt.figure(figsize=(12, 6))
    plt.plot(time, pwm)
    plt.title("Synthetic PWM Input for Drone Flight")
    plt.xlabel("Time (s)")
    plt.ylabel("PWM Value")
    plt.grid(True)
    plt.show()

    return pwm, time


def interpolate_sweep_data(pwm_data, sample_rate):
    pwm_values = pwm_data['PWM'].values
    times = pwm_data['Time'].values

    # Convert times to sample indices
    sample_indices = (times * sample_rate).astype(int)

    # Create an interpolator for audio data
    interpolated_audio = interp1d(pwm_values, sample_indices, kind='linear', fill_value='extrapolate')

    return interpolated_audio


# Function to generate synthetic audio
def generate_synthetic_audio(pwm_inputs, pwm_audio_file, pwm_timestamps, output_file, pwm_times):
    sample_rate, sweep_audio = wavfile.read(pwm_audio_file)
    pwm_data = pd.read_csv(pwm_timestamps)
    pwm_data.columns = ['PWM', 'Time']

    # Interpolate audio indices for PWM values
    interpolated_audio = interpolate_sweep_data(pwm_data, sweep_audio, sample_rate)

    synthetic_audio = np.zeros(int(pwm_times[-1] * sample_rate))  # Pre-allocate final audio array
    window_duration = 0.5  # Window size in seconds
    overlap_duration = 0.1  # Overlap size in seconds
    hover_variation = 5  # Amount of PWM variation during hover

    window_samples = int(window_duration * sample_rate)
    overlap_samples = int(overlap_duration * sample_rate)

    for i, pwm_value in enumerate(pwm_inputs):
        try:
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
            print(f"Error processing PWM {pwm_value:.2f}: {e}")

    # Normalize and save the final audio
    synthetic_audio = synthetic_audio.astype(np.float32)
    synthetic_audio /= np.max(np.abs(synthetic_audio))
    synthetic_audio = (synthetic_audio * 32767).astype(np.int16)
    sf.write(output_file, synthetic_audio, sample_rate)




if __name__ == '__main__':
    # Generate synthetic PWM sequence
    synthetic_pwm, pwm_times = generate_synthetic_pwm()

    # Parameters
    file_index = 1
    pwm_audio_file = "../Data/Sweep Ref 2/motor_sweep.wav"
    pwm_timestamps = "../Data/Sweep Ref 2/sweep pwm times.csv"
    output_file = f"../Data/synthesized/gen 2/synthetic_{file_index}.wav"

    # Generate synthetic audio
    generate_synthetic_audio(synthetic_pwm, pwm_audio_file, pwm_timestamps, output_file, pwm_times)

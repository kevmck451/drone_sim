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
    flight_duration = 300  # Desired flight duration in seconds
    pwm_sampling_rate = 50  # PWM values per second

    # Time array with high sampling rate
    time = np.linspace(0, flight_duration, int(flight_duration * pwm_sampling_rate))

    # Define flight phases
    takeoff_duration = 10  # seconds
    hover_duration = 10    # seconds
    climb_duration = 10    # seconds
    forward_duration = 120 # seconds
    landing_duration = 10  # seconds

    takeoff_time = time[time <= takeoff_duration]
    takeoff_pwm = np.linspace(idle_pwm, hover_pwm, len(takeoff_time))

    hover_time = time[(time > takeoff_duration) & (time <= takeoff_duration + hover_duration)]
    hover_pwm = np.full(len(hover_time), hover_pwm)

    climb_time = time[(time > takeoff_duration + hover_duration) &
                      (time <= takeoff_duration + hover_duration + climb_duration)]
    climb_pwm = np.linspace(hover_pwm[0], max_pwm, len(climb_time))

    forward_time = time[(time > takeoff_duration + hover_duration + climb_duration) &
                        (time <= takeoff_duration + hover_duration + climb_duration + forward_duration)]
    forward_pwm = hover_pwm[0] + 100 * np.sin(0.2 * np.pi * (forward_time - forward_time[0]))

    landing_time = time[time > takeoff_duration + hover_duration + climb_duration + forward_duration]
    landing_pwm = np.linspace(max_pwm, idle_pwm, len(landing_time))

    # Combine all PWM values
    pwm = np.concatenate([takeoff_pwm, hover_pwm, climb_pwm, forward_pwm, landing_pwm])

    # Plot the PWM sequence
    # plt.figure(figsize=(12, 6))
    # plt.plot(time, pwm)
    # plt.title("Synthetic PWM Input for Drone Flight")
    # plt.xlabel("Time (s)")
    # plt.ylabel("PWM Value")
    # plt.grid(True)
    # plt.show()

    return pwm, time


def interpolate_sweep_data(pwm_data, sweep_audio, sample_rate):
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

    window_samples = int(window_duration * sample_rate)
    overlap_samples = int(overlap_duration * sample_rate)

    for i, pwm_value in enumerate(pwm_inputs):
        try:
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




# Generate synthetic PWM sequence
synthetic_pwm, pwm_times = generate_synthetic_pwm()

# Parameters
pwm_audio_file = "../Data/motor_sweep.wav"
pwm_timestamps = "../Data/sweep pwm times.csv"
output_file = "../Data/synthesized/synthetic_7.wav"

# Generate synthetic audio
generate_synthetic_audio(synthetic_pwm, pwm_audio_file, pwm_timestamps, output_file, pwm_times)

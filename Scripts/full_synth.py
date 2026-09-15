import numpy as np
import pandas as pd
from scipy.io import wavfile
from scipy.signal import resample
import soundfile as sf
import matplotlib.pyplot as plt

# Function to generate synthetic PWM
def generate_synthetic_pwm():
    idle_pwm = 1100
    hover_pwm = 1400
    max_pwm = 1860
    flight_duration = 300  # seconds
    sampling_rate = 10  # PWM samples per second

    time = np.linspace(0, flight_duration, flight_duration * sampling_rate)

    # Takeoff (0-30 seconds)
    takeoff_time = time[time <= 30]
    takeoff_pwm = np.linspace(idle_pwm, hover_pwm, len(takeoff_time))

    # Hover (30-60 seconds)
    hover_time = time[(time > 30) & (time <= 60)]
    hover_pwm = np.full(len(hover_time), hover_pwm)

    # Climbing (60-90 seconds)
    climb_time = time[(time > 60) & (time <= 90)]
    climb_pwm = np.linspace(hover_pwm[0], max_pwm, len(climb_time))

    # Forward Motion (90-210 seconds): sinusoidal PWM changes
    forward_time = time[(time > 90) & (time <= 210)]
    forward_pwm = hover_pwm[0] + 100 * np.sin(0.2 * np.pi * forward_time)

    # Landing (210-300 seconds)
    landing_time = time[time > 210]
    landing_pwm = np.linspace(max_pwm, idle_pwm, len(landing_time))

    # Combine all segments
    pwm = np.concatenate([takeoff_pwm, hover_pwm, climb_pwm, forward_pwm, landing_pwm])

    # Plot the PWM sequence
    # plt.figure(figsize=(12, 6))
    # plt.plot(time, pwm)
    # plt.title("Synthetic PWM Input for Drone Flight")
    # plt.xlabel("Time (s)")
    # plt.ylabel("PWM Value")
    # plt.grid(True)
    # plt.show()

    return pwm

# Function to generate synthetic audio
def generate_synthetic_audio(pwm_inputs, pwm_audio_file, pwm_timestamps, output_file):
    sample_rate, sweep_audio = wavfile.read(pwm_audio_file)
    pwm_data = pd.read_csv(pwm_timestamps)
    pwm_data.columns = ['PWM', 'Time']

    pwm_data['End_Time'] = pwm_data['Time'].shift(-1, fill_value=pwm_data['Time'].iloc[-1] + 1)

    synthetic_audio = []

    for i, pwm_value in enumerate(pwm_inputs):
        # Find the closest matching PWM value
        closest_idx = (pwm_data['PWM'] - pwm_value).abs().idxmin()
        match = pwm_data.iloc[closest_idx]

        start_time = match['Time']
        end_time = match['End_Time']

        start_sample = int(start_time * sample_rate)
        end_sample = int(end_time * sample_rate)
        segment = sweep_audio[start_sample:end_sample].astype(np.float32)  # Convert to float32 for processing

        if i > 0 and pwm_inputs[i] != pwm_inputs[i - 1]:
            transition_samples = min(len(segment), int(sample_rate * 0.1))  # Ensure we don't exceed segment length
            if transition_samples > 0 and len(synthetic_audio) >= transition_samples:
                fade_out = np.linspace(1, 0, transition_samples, dtype=np.float32)
                fade_in = np.linspace(0, 1, transition_samples, dtype=np.float32)

                # Apply fade-out to previous audio and fade-in to current segment
                synthetic_audio[-transition_samples:] *= fade_out
                segment[:transition_samples] *= fade_in

        synthetic_audio.extend(segment)

    synthetic_audio = np.array(synthetic_audio, dtype=np.float32)
    synthetic_audio /= np.max(np.abs(synthetic_audio))
    synthetic_audio = (synthetic_audio * 32767).astype(np.int16)  # Convert back to int16
    sf.write(output_file, synthetic_audio, sample_rate)




# Generate synthetic PWM sequence
synthetic_pwm = generate_synthetic_pwm()

# Parameters
pwm_audio_file = "../Data/motor_sweep.wav"
pwm_timestamps = "../Data/sweep pwm times.csv"
output_file = "../Data/synthesized/synthetic_1.wav"

# Generate synthetic audio
generate_synthetic_audio(synthetic_pwm, pwm_audio_file, pwm_timestamps, output_file)

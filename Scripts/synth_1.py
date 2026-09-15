import numpy as np
import pandas as pd
from scipy.io import wavfile
from scipy.signal import resample
import soundfile as sf

def generate_synthetic_audio(pwm_inputs, pwm_audio_file, pwm_timestamps, output_file):
    # Load the sweep audio file
    sample_rate, sweep_audio = wavfile.read(pwm_audio_file)

    # Load the PWM timestamps and corresponding values
    pwm_data = pd.read_csv(pwm_timestamps)

    # Ensure columns are correctly named
    pwm_data.columns = ['PWM', 'Start_Time', 'End_Time']

    # Prepare the output audio signal
    synthetic_audio = []

    # Iterate over the PWM inputs
    for i, pwm_value in enumerate(pwm_inputs):
        # Find the matching PWM value in the sweep data
        match = pwm_data[pwm_data['PWM'] == pwm_value]

        if not match.empty:
            start_time = match.iloc[0]['Start_Time']
            end_time = match.iloc[0]['End_Time']

            # Extract the corresponding audio segment
            start_sample = int(start_time * sample_rate)
            end_sample = int(end_time * sample_rate)
            segment = sweep_audio[start_sample:end_sample]

            # Handle increasing/decreasing transitions
            if i > 0 and pwm_inputs[i] != pwm_inputs[i - 1]:
                # Smoothly transition between segments
                transition_samples = int(sample_rate * 0.1)  # 0.1 second fade
                fade_out = np.linspace(1, 0, transition_samples)
                fade_in = np.linspace(0, 1, transition_samples)

                # Apply fade to segments
                if len(synthetic_audio) > transition_samples:
                    synthetic_audio[-transition_samples:] *= fade_out
                segment[:transition_samples] *= fade_in

            # Add segment to synthetic audio
            synthetic_audio.extend(segment)

        else:
            print(f"PWM value {pwm_value} not found in sweep data.")

    # Convert to numpy array and normalize
    synthetic_audio = np.array(synthetic_audio, dtype=np.float32)
    synthetic_audio /= np.max(np.abs(synthetic_audio))

    # Save the synthetic audio to a file
    sf.write(output_file, synthetic_audio, sample_rate)

# Example usage
pwm_inputs = [1010, 1200, 1400, 1500, 1600, 1860]  # Example PWM sequence
pwm_audio_file = "motor_sweep.wav"
pwm_timestamps = "sweep pwm times.csv"
output_file = "synthetic_flight_audio.wav"

generate_synthetic_audio(pwm_inputs, pwm_audio_file, pwm_timestamps, output_file)
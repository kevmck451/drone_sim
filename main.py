from generate_all_synthetic_ch import *

from pathlib import Path


if __name__ == '__main__':

    # path to folder where the bin files are
    input_folder = './Data/_Experiment/Logs4'

    # path where you want to save the synthesized wav files
    output_folder = './Data/_Experiment/Audios/5-13-25'

    for log_file in Path(input_folder).glob("*.bin"):

        pwm_data = extract_pwm(str(log_file))

        audio_list = []

        # Generate Synthetic Audio
        for channel in range(1, 7):
            synthetic_pwm = pwm_data[f"channel_{channel}"]["pwm_values"]
            pwm_times = pwm_data[f"channel_{channel}"]["timestamps"]

            pwm_audio_file = "./sweep_reference/motor_sweep.wav"
            pwm_timestamps = "./sweep_reference/sweep pwm times.csv"

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
        output_file = f"{output_folder}/{log_file.stem}_synthetic.wav"
        sf.write(output_file, combined_audio, 48000)
        print(f"Saved combined audio to {output_file}")


import csv


if __name__ == '__main__':

    # Define the CSV file name
    output_file = "../Data/Sweep Ref 2/sweep pwm times.csv"

    # Define the range for PWM and time intervals
    pwm_start = 1100
    pwm_end = 1700
    pwm_step = 1
    time_interval = 0.5

    # Create data for the CSV
    rows = []
    time = 0
    for pwm in range(pwm_start, pwm_end + 1, pwm_step):
        rows.append([pwm, round(time, 1)])
        time += time_interval

    # Write data to the CSV file
    with open(output_file, mode="w", newline="") as file:
        writer = csv.writer(file)
        # Write the header
        writer.writerow(["pwm", "time"])
        # Write the rows
        writer.writerows(rows)

    print(f"CSV file '{output_file}' generated successfully.")
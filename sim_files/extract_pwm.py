import csv
from pymavlink import mavutil


def extract_pwm(logfile):

    # Open the log file
    logfile = mavutil.mavlink_connection(log_file, robust_parsing=True)

    # Open a CSV file to save PWM signals and timestamps
    with open(output_file, mode="w", newline="") as csvfile:
        csvwriter = csv.writer(csvfile)
        # Write the header
        csvwriter.writerow(["Time", "1", "2", "3", "4", "5", "6"])

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
            c1_to_c6 = [msg_dict.get(f"C{i}", 0) for i in range(1, 7)]  # Get values for C1 to C6

            # Write to CSV file
            csvwriter.writerow([normalized_time] + c1_to_c6)

    print(f"Normalized PWM signals (C1-C6) and timestamps saved to {output_file}.")


if __name__ == '__main__':

    # Input log file and output CSV file
    # filename = 'LightRect'
    filename = 'LightRectCrazy'
    log_file = f"../Data/Drone_Paths/{filename}.BIN"
    output_file = f"../Data/Drone_Paths/{filename}.csv"


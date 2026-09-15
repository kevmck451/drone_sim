from pymavlink import mavutil

filename = 'LightRect'
log_file = f"../Data/Drone_Paths/{filename}.BIN"
logfile = mavutil.mavlink_connection(log_file, robust_parsing=True)

found_rcou = False
while True:
    msg = logfile.recv_match(type='RCOU', blocking=False)
    if msg is None:
        break
    print(msg)  # Print each `RCOU` message for verification
    found_rcou = True

if not found_rcou:
    print("No RCOU messages found in the log file.")
else:
    print("RCOU messages found.")
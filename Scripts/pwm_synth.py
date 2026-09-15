import numpy as np
import matplotlib.pyplot as plt

def generate_synthetic_pwm():
    # Parameters
    idle_pwm = 1010
    hover_pwm = 1400
    max_pwm = 1860
    flight_duration = 300  # seconds
    sampling_rate = 10  # PWM samples per second

    # Time array
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
    plt.figure(figsize=(12, 6))
    plt.plot(time, pwm)
    plt.title("Synthetic PWM Input for Drone Flight")
    plt.xlabel("Time (s)")
    plt.ylabel("PWM Value")
    plt.grid(True)
    plt.show()

    return pwm

# Generate synthetic PWM array
synthetic_pwm = generate_synthetic_pwm()

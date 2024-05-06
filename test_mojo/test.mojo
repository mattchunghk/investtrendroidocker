from python import Python
from time import now


# Start the timer


# Calculate the elapsed time


fn main():
    let start_time = now()
    print("start_time: ", start_time)
    for i in range(1000):
        pass
    # Print the elapsed time
    let elapsed_time = (now() - start_time) / 1000000000.0
    print("The code took " + str(elapsed_time) + " seconds to run.")


# def main():
#     for i in range(1000000):
#         pass

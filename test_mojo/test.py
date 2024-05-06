import time

def test_code():
    # Add your code to test here
    # For example, you can use a loop to perform some computations
    for i in range(10000):
        pass

# Start the timer
start_time = time.time()

# Call the function to test the code
test_code()

# Calculate the elapsed time
elapsed_time = time.time() - start_time

# Print the elapsed time
print(f"The code took {elapsed_time} seconds to run.")
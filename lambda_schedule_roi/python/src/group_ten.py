def group(n, group = 10):

    remaining = n % group
    full_groups = n // group
    index = 0
    
    # Loop through numbers from 0 to n-1 (since we're considering 0 as a possible output)
    for i in range(full_groups):
        print(index, index + 9)
        index += 10
    print(index, index + remaining - 1)

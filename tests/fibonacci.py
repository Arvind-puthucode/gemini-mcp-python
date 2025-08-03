```python
# A cache to store computed Fibonacci numbers
memo = {0: 0, 1: 1}

def fibonacci(n: int) -> int:
    """
    Calculates the nth Fibonacci number using memoization.

    This function stores previously computed results in a dictionary (memo)
    to avoid redundant calculations in the recursive calls.

    Args:
        n: A non-negative integer.

    Returns:
        The nth Fibonacci number.

    Raises:
        ValueError: If n is a negative integer.
    """
    if n < 0:
        raise ValueError("Input must be a non-negative integer.")
    
    if n in memo:
        return memo[n]
    
    # Recursively compute the Fibonacci number and store it in the cache
    result = fibonacci(n - 1) + fibonacci(n - 2)
    memo[n] = result
    
    return result

if __name__ == '__main__':
    # Demonstrate the function and its efficiency
    print(f"fibonacci(10) = {fibonacci(10)}")
    print(f"fibonacci(20) = {fibonacci(20)}")
    print(f"fibonacci(35) = {fibonacci(35)}")
    print(f"fibonacci(50) = {fibonacci(50)}")

    # Example of handling invalid input
    try:
        fibonacci(-5)
    except ValueError as e:
        print(f"\nCaught expected error for fibonacci(-5): {e}")

    # You can inspect the cache to see the stored values
    # print(f"\nCache contains {len(memo)} values after computations.")
```
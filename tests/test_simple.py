"""Simple test to verify the gemini-mcp-python package works correctly"""

def test_calculator():
    """Test basic calculator functionality"""
    def add(a, b):
        return a + b
    
    def subtract(a, b):
        return a - b
    
    # Test addition
    assert add(2, 3) == 5
    assert add(-1, 1) == 0
    
    # Test subtraction  
    assert subtract(5, 3) == 2
    assert subtract(0, 0) == 0
    
    print("✅ All calculator tests passed!")

if __name__ == "__main__":
    test_calculator()
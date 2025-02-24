# data_parser.py

class SensorData:
    """
    A flexible data container to store raw sensor values as attributes.
    Example usage:
        line = "F1:0,P1:1,AccX:0.4,GyrZ:-0.2"
        data = parse_line_to_object(line)
        print(data.F1, data.P1, data.AccX, data.GyrZ)
    """
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            # Convert spaces or punctuation if needed, but typically F1, P1, etc. are fine
            setattr(self, key, value)

def parse_line_to_dict(line: str) -> dict:
    """
    Parses a line like:
        "F1:0,P1:1,AccX:0.4,GyrZ:-0.2"
    into a dictionary:
        {"F1": 0, "P1": 1, "AccX": 0.4, "GyrZ": -0.2}
    """
    data_dict = {}
    # Split by commas
    parts = line.split(',')
    for part in parts:
        kv = part.split(':')
        if len(kv) == 2:
            key = kv[0].strip()
            val_str = kv[1].strip()
            # Attempt type conversion
            data_dict[key] = try_convert(val_str)
    return data_dict

def try_convert(value_str: str):
    """
    Converts a string to int or float if possible, otherwise returns the original string.
    """
    # Try int
    try:
        return int(value_str)
    except ValueError:
        pass
    # Try float
    try:
        return float(value_str)
    except ValueError:
        pass
    # Fallback as string
    return value_str

def parse_line_to_object(line: str) -> SensorData:
    """
    Returns a SensorData instance for easier attribute-style access.
    """
    data_dict = parse_line_to_dict(line)
    return SensorData(**data_dict)

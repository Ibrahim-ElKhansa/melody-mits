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
    print(line)
    
    with open('percussion.txt', 'a') as file:
        file.write(line + '\n')
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

def parse_line_to_dict(line):
    """
    Example: 
       "F1:OFF, F2:OFF, F3:OFF, F4:OFF | AccX:0.36, AccY:0.11, AccZ:0.86, GyroX:-0.07, ..."
    Returns a dict like:
       {
         "F1": 0,   # OFF -> 0
         "F2": 0,
         ...
         "AccX": 0.36,
         ...
       }
    """
    data_dict = {}
    
    # Split around the "|" first, so we get "F1:OFF, F2:..." part and "AccX:0.36..." part
    parts = line.split("|")
    if len(parts) == 2:
        flex_part, motion_part = parts
    else:
        # If the line isn't exactly in that format, handle gracefully
        flex_part = line
        motion_part = ""

    # Split each part by commas, e.g. "F1:OFF" -> sensor "F1", val "OFF"
    flex_splits = flex_part.strip().split(",")
    motion_splits = motion_part.strip().split(",")

    # Parse each "F1:OFF", "F2:OFF" etc.
    for chunk in flex_splits:
        chunk = chunk.strip()
        if not chunk:
            continue
        # e.g. "F1:OFF"
        sensor, val = chunk.split(":")
        sensor = sensor.strip()
        val = val.strip()
        if val.upper() == "ON":
            data_dict[sensor] = 1
        elif val.upper() == "OFF":
            data_dict[sensor] = 0
        else:
            # If not ON/OFF, try to parse numeric
            try:
                data_dict[sensor] = float(val)
            except ValueError:
                data_dict[sensor] = 0

    # Same for motion_splits
    for chunk in motion_splits:
        chunk = chunk.strip()
        if not chunk:
            continue
        sensor, val = chunk.split(":")
        sensor = sensor.strip()
        val = val.strip()
        try:
            data_dict[sensor] = float(val)
        except ValueError:
            data_dict[sensor] = 0

    return data_dict

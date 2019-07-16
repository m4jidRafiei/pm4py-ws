import chardet

def predict_encoding(file_path, n_lines=20):
    """
    Predict the encoding of a file using chardet

    Parameters
    ------------
    file_path
        Path to the file
    n_lines
        (Optional) number of lines to read to make the encoding recognition

    Returns
    ------------
    encoding
        Encoding
    """
    # Open the file as binary data
    with open(file_path, 'rb') as f:
        # Join binary lines for specified number of lines
        rawdata = b''.join([f.readline() for _ in range(n_lines)])

    return chardet.detect(rawdata)['encoding']
import pandas as pd

class PreProcessing:

    def __init__(self, design) :

        self.design = design
        a = 1
    

    def load_data(self, path):
        self.raw_data = pd.read_csv(path)
        self.raw_data.dropna(inplace=True)
        print("Data loaded successfully!")
        print(f"Data Shape: {self.raw_data.shape}")
        print(f"Columns: {self.raw_data.columns.tolist()}")

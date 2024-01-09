import requests
import seaborn as sns
from matplotlib import pyplot as plt

def get_user_level_image(user_id: str):
    # Add domain and scheme so that this request makes sense, for now it is just a dummy request
    req = requests.get(f'/statistics/user/{user_id}')
    data = req.json()



if __name__ == "__main__":

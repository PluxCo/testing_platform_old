import io

import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt


# resp = requests.get('DOMAIN/statistics/user/<user_ID>')
# data = resp.json()

def get_points_by_level_kde_plot(data, dpi=200) -> bytes:
    """
    Generate a kernel density estimate (kdeplot) of points vs level.

    Parameters:
    - data (dict): A dictionary containing data, including 'ls' with information about levels and points.
    - dpi (int, optional): Dots per inch of the generated image. Default is 200.

    Returns:
    - bytes: Image data in PNG format.
    """
    ls_df = pd.DataFrame(data['ls'])

    plt.figure(dpi=dpi)

    sns.kdeplot(x='points', y='level', data=ls_df, fill=True, cmap='Blues', thresh=0, levels=30)
    plt.title('Kernel Density Estimate: Points vs Level')
    plt.xlabel('Points')
    plt.ylabel('Level')

    # Saving the plot to a BytesIO buffer
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png')
    plt.close()

    img_buffer.seek(0)

    return img_buffer.getvalue()


def get_points_by_level_and_subject_barplot(data, dpi=200) -> bytes:
    """
    Generate a bar plot of points by level and subject.

    Parameters:
    - data (dict): A dictionary containing data, including 'ls' with information about levels, subjects, and points.
    - dpi (int, optional): Dots per inch of the generated image. Default is 200.

    Returns:
    - bytes: Image data in PNG format.
    """
    ls_df = pd.DataFrame(data['ls'])

    plt.figure(dpi=dpi)

    sns.barplot(x='subject', y='points', hue='level', data=ls_df,
                palette=sns.cubehelix_palette(start=.5, rot=-.7, dark=.4, light=.75, as_cmap=True))
    plt.title('Bar Plot: Points by Level and Subject')
    plt.xlabel('Subject')
    plt.ylabel('Points')

    # Saving the plot to a BytesIO buffer
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png')
    plt.close()

    img_buffer.seek(0)

    return img_buffer.getvalue()

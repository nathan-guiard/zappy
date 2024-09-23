import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN
from scipy.spatial import ConvexHull

def parse_tuple_key(key_str):
    """
    Convert a string representing a tuple into a Python tuple.
    """
    try:
        parts = key_str.strip("()").split(",")
        return tuple(map(int, parts))
    except Exception as e:
        print(f"Error parsing key {key_str}: {e}")
        return None

def perform_clustering(df, eps=5, min_samples=1):
    """
    Applique l'algorithme DBSCAN pour identifier des clusters dans les données.
    
    Args:
        df (DataFrame): DataFrame contenant les colonnes 'x', 'y', 'value'.
        eps (float): Rayon maximum pour rechercher les voisins.
        min_samples (int): Nombre minimum de points pour former un cluster.
        
    Returns:
        DataFrame: DataFrame avec une colonne supplémentaire 'cluster' indiquant l'appartenance au cluster.
    """
    if df.empty:
        print("Aucune donnée positive à clusteriser.")
        return df
    
    # Extraire les coordonnées pour le clustering
    coords = df[['x', 'y']].values
    
    # Appliquer DBSCAN
    db = DBSCAN(eps=eps, min_samples=min_samples).fit(coords)
    df['cluster'] = db.labels_

    # Filtrer les clusters en ne gardant que ceux avec au moins 10 points
    cluster_counts = df['cluster'].value_counts()
    valid_clusters = cluster_counts[cluster_counts >= 6].index
    
    # Marquer les clusters invalides comme bruit
    df['cluster'] = df['cluster'].where(df['cluster'].isin(valid_clusters), -1)

    return df

def get_cluster_centroid(df, cluster_label):
    """
    Calculate the centroid of a cluster.
    
    Args:
        df (DataFrame): DataFrame containing the points of the cluster.
        cluster_label (int): Label of the cluster.
    
    Returns:
        tuple: Coordinates of the cluster's centroid.
    """
    cluster_points = df[df['cluster'] == cluster_label]
    centroid_x = cluster_points['x'].mean()
    centroid_y = cluster_points['y'].mean()
    return int(centroid_x), int(centroid_y)

def cluster_analysis(coordinates_values_dict, eps=5, min_samples=10, score_threshold=1500):
    """
    Perform clustering on the given data and return the centroid of the largest cluster.
    
    Args:
        coordinates_values_dict (dict): Dictionary with (x, y) as keys and values as resource count.
        eps (float): Max radius for DBSCAN.
        min_samples (int): Minimum points to form a cluster.
        score_threshold (int): Minimum score threshold to consider a cluster.
    
    Returns:
        tuple or None: The center of the largest cluster or None if no valid clusters found.
    """
    # Convert dictionary to DataFrame
    data = [{"x": coord[0], "y": -coord[1], "value": val} for coord, val in coordinates_values_dict.items()]
    df = pd.DataFrame(data)
    
    if df.empty:
        print("No data to analyze.")
        return None
    
    # Apply clustering
    df = perform_clustering(df, eps=eps, min_samples=min_samples)
    
    # Identify the largest cluster
    cluster_totals = df.groupby('cluster')['value'].sum()
    if cluster_totals.empty:
        print("No clusters found.")
        return None
    
    # Get the label of the largest cluster
    top_cluster_label = cluster_totals.idxmax()
    
    centroid = get_cluster_centroid(df, top_cluster_label)
    return centroid
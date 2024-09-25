import os
import json
import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN
from scipy.spatial import ConvexHull

def parse_tuple_key(key_str):
    try:
        parts = key_str.strip("()").split(",")
        return tuple(map(int, parts))
    except Exception as e:
        print(f"Erreur lors de la conversion de la clé {key_str}: {e}")
        return None

def load_json_file(file_path):
    try:
        with open(file_path, 'r') as file:
            if os.path.getsize(file_path) == 0:
                # print(f"Le fichier {file_path} est vide.")
                return {}
            data = json.load(file)
            converted_data = {}
            for key_str, value in data.items():
                key_tuple = parse_tuple_key(key_str)
                if key_tuple:
                    converted_data[key_tuple] = value
            return converted_data
    except json.JSONDecodeError as e:
        print(f"Erreur JSON dans le fichier {file_path}: {e}")
        return {}
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier {file_path}: {e}")
        return {}

def perform_clustering(df, eps, min_samples):
    """
    Applique l'algorithme DBSCAN pour identifier des clusters dans les données,
    mais uniquement sur les points avec une valeur positive.
    
    Args:
        df (DataFrame): DataFrame contenant les colonnes 'x', 'y', 'value'.
        eps (float): Rayon maximum pour rechercher les voisins.
        min_samples (int): Nombre minimum de points pour former un cluster.
        
    Returns:
        DataFrame: DataFrame avec une colonne supplémentaire 'cluster' indiquant l'appartenance au cluster.
    """
    # Filtrer pour ne garder que les points avec des valeurs positives
    # df = df[df['value'] > 0].copy()  # Faire une copie explicite

    if df.empty:
        # print("Aucune donnée positive à clusteriser.")
        return None
    
    # Extraire les coordonnées pour le clustering
    coords = df[['x', 'y']].values
    
    # Appliquer DBSCAN
    db = DBSCAN(eps=eps, min_samples=min_samples).fit(coords)
    df.loc[:, 'cluster'] = db.labels_  # Utiliser .loc pour éviter le warning

    # Filtrer les clusters en ne gardant que ceux avec au moins 6 points
    cluster_counts = df['cluster'].value_counts()
    valid_clusters = cluster_counts[cluster_counts >= 6].index
    
    # Marquer les clusters invalides comme bruit
    df.loc[:, 'cluster'] = df['cluster'].where(df['cluster'].isin(valid_clusters), -1)
    
    # Calculer la densité pour chaque cluster
    densities = {}
    for cluster in valid_clusters:
        cluster_points = df[df['cluster'] == cluster]
        # Calcul de la densité en fonction de l'étendue des coordonnées
        density = len(cluster_points) / (cluster_points['x'].max() - cluster_points['x'].min()) * (cluster_points['y'].max() - cluster_points['y'].min())
        densities[cluster] = density
        # print(f"Densité du cluster {cluster}: {density}")

    # Sélectionner le cluster avec la plus grande densité
    if densities:
        best_cluster = max(densities, key=densities.get)
        return df[df['cluster'] == best_cluster]
    else:
        return None



def get_cluster_centroid(df, cluster_label):
    """
    Calculer le centroïde d'un cluster.
    
    Args:
        df (DataFrame): DataFrame contenant les points du cluster.
        cluster_label (int): Label du cluster.
    
    Returns:
        tuple: Coordonnées du centroïde du cluster.
    """
    cluster_points = df[df['cluster'] == cluster_label]
    centroid_x = cluster_points['x'].mean()
    centroid_y = cluster_points['y'].mean()
    return int(centroid_x), int(centroid_y)

def find_cluster_center(data_dict):
    df = pd.DataFrame([
        {"x": coord[0], "y": coord[1], "value": val}
        for coord, val in data_dict.items() if val > 0  # Only include positive values
    ])

    cluster_df = perform_clustering(df, eps=5, min_samples=1)

    if cluster_df is not None:
        centroid_x, centroid_y = get_cluster_centroid(cluster_df, cluster_df['cluster'].unique()[0])
        return (centroid_x, centroid_y)
    return None




def main():
    data_directory = "datas"
    if not os.path.isdir(data_directory):
        print(f"Le dossier '{data_directory}' n'existe pas.")
        return

    for filename in os.listdir(data_directory):
        if filename.endswith(".json"):
            file_path = os.path.join(data_directory, filename)
            # print(f"\nTraitement du fichier: {file_path}")

            data = load_json_file(file_path)
            if not data:
                # print(f"Aucune donnée valide trouvée dans {filename}.")
                continue
            
            file_path = os.path.splitext(filename)[0]
            
            df = pd.DataFrame([
                {"x": coord[0], "y": -coord[1], "value": val}
                for coord, val in data.items() if val > 0  # Only include positive values
            ])

            cluster_df = perform_clustering(df, eps=5, min_samples=1)
            
            if cluster_df is not None:
                # Calculer le centre du cluster avec la plus grande densité
                centroid_x = int(cluster_df['x'].mean())
                centroid_y = int(cluster_df['y'].mean())
                print(f"{file_path}: Centre du cluster avec la plus grande densité: ({centroid_x}, {centroid_y})")
            # else:
            #     print("Aucun cluster trouvé.")


if __name__ == "__main__":
    main()

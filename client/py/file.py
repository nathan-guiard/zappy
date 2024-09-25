import os
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from sklearn.cluster import DBSCAN
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection
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
                print(f"Le fichier {file_path} est vide.")
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

    # Filtrer les clusters en ne gardant que ceux avec au moins 6 points
    cluster_counts = df['cluster'].value_counts()
    valid_clusters = cluster_counts[cluster_counts >= 6].index
    
    # Marquer les clusters invalides comme bruit
    df['cluster'] = df['cluster'].where(df['cluster'].isin(valid_clusters), -1)

    return df


def get_cluster_polygons(df, cluster_label):
    try:
        points = df[df['cluster'] == cluster_label][['x', 'y']].values
        if len(points) < 3:
            return None
        hull = ConvexHull(points)
        polygon = Polygon(points[hull.vertices], closed=True, fill=True, edgecolor='black', alpha=0.2)
        return polygon
    except Exception as e:
        print(f"Erreur lors du calcul du Convex Hull pour le cluster {cluster_label}: {e}")
        return None

def visualize_data_with_clusters(df, output_path, filename, eps=5, min_samples=1):
    df_positive = df[df['value'] > 0].copy()
    df_zero = df[df['value'] == 0].copy()

    df_positive = perform_clustering(df_positive, eps=eps, min_samples=min_samples)

    plt.figure(figsize=(14, 12))
    
    # Tracer les points avec des valeurs > 0
    if not df_positive.empty:
        scatter_positive = plt.scatter(
            df_positive['x'], 
            df_positive['y'], 
            c=df_positive['cluster'], 
            cmap='tab10',  # Utiliser une palette de couleurs distinctes
            edgecolors='w', 
            s=150
        )

    plt.scatter(
        df_zero['x'], 
        df_zero['y'], 
        c='grey', 
        edgecolors='w', 
        s=100, 
        label='Aucune Ressource'
    )

    # Tracer les polygones des clusters
    if not df_positive.empty:
        unique_clusters = df_positive['cluster'].unique()
        patches = []

        for cluster in unique_clusters:
            if cluster == -1:
                continue
            polygon = get_cluster_polygons(df_positive, cluster)
            if polygon:
                patches.append(polygon)

                # Calculer la densité de points dans le cluster
                cluster_points = df_positive[df_positive['cluster'] == cluster]
                density = len(cluster_points) / (cluster_points['x'].max() - cluster_points['x'].min()) * (cluster_points['y'].max() - cluster_points['y'].min())
                
                # Afficher la densité sur le graphique
                centroid_x = cluster_points['x'].mean()
                centroid_y = cluster_points['y'].mean()
                plt.annotate(
                    f'Densité: {density:.2f}',
                    (centroid_x, centroid_y),
                    textcoords="offset points",
                    xytext=(0, -20),
                    ha='center',
                    fontsize=10,
                    color='black',
                    weight='bold',
                    bbox=dict(boxstyle="round,pad=0.3", fc="yellow", alpha=0.5)
                )

        if patches:
            p = PatchCollection(patches, facecolor='none', edgecolor='black', linewidth=2, linestyle='--')
            plt.gca().add_collection(p)

    plt.title(f"Carte des Endroits avec les Ressources Trouvées - {filename}", fontsize=20, fontweight='bold')
    plt.xlabel("Coordonnée X", fontsize=16)
    plt.ylabel("Coordonnée Y (Négatif)", fontsize=16)
    plt.legend(loc='upper right', fontsize=14, markerscale=1.5, framealpha=0.7)
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.xlim(df['x'].min() - 5, df['x'].max() + 5)
    plt.ylim(df['y'].min() - 5, df['y'].max() + 5)

    save_path = os.path.join(output_path, f"{os.path.splitext(filename)[0]}.png")
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()
    print(f"Graphique sauvegardé: {save_path}")

def main():
    data_directory = "datas"
    if not os.path.isdir(data_directory):
        print(f"Le dossier '{data_directory}' n'existe pas.")
        return

    output_directory = "output_graphs"
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    for filename in os.listdir(data_directory):
        if filename.endswith(".json"):
            file_path = os.path.join(data_directory, filename)
            print(f"\nTraitement du fichier: {file_path}")

            data = load_json_file(file_path)
            if not data:
                print(f"Aucune donnée valide trouvée dans {filename}.")
                continue
            
            df = pd.DataFrame([
                {"x": coord[0], "y": -coord[1], "value": val}
                for coord, val in data.items()
            ])

            if df.empty:
                print(f"Aucune donnée à visualiser dans {filename}.")
                continue
            
            visualize_data_with_clusters(
                df, 
                output_directory, 
                filename, 
                eps=5, 
                min_samples=1
            )

    print("\nTous les graphiques ont été générés et sauvegardés.")

if __name__ == "__main__":
    main()

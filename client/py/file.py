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
    """
    Convertit une chaîne de caractères représentant un tuple en un tuple Python.
    Exemple : "(55, 44)" -> (55, 44)
    """
    try:
        # Enlève les parenthèses et sépare par la virgule
        parts = key_str.strip("()").split(",")
        # Convertit chaque partie en entier
        return tuple(map(int, parts))
    except Exception as e:
        print(f"Erreur lors de la conversion de la clé {key_str}: {e}")
        return None

def load_json_file(file_path):
    """
    Charge un fichier JSON et convertit les clés en tuples.
    
    Args:
        file_path (str): Chemin vers le fichier JSON.
        
    Returns:
        dict: Dictionnaire avec des tuples comme clés et des valeurs numériques.
    """
    try:
        with open(file_path, 'r') as file:
            # Vérifier si le fichier est vide
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
    
    # Ajouter les labels de cluster au DataFrame
    df['cluster'] = db.labels_
    
    return df

def get_cluster_polygons(df, cluster_label):
    """
    Calcule le polygone convexe enveloppant les points d'un cluster.
    
    Args:
        df (DataFrame): DataFrame contenant les points du cluster.
        cluster_label (int): Label du cluster.
        
    Returns:
        Polygon or None: Objet Polygon représentant le convex hull du cluster, ou None si impossible.
    """
    try:
        points = df[df['cluster'] == cluster_label][['x', 'y']].values
        if len(points) < 3:
            return None  # Convex hull n'est pas défini pour moins de 3 points
        hull = ConvexHull(points)
        polygon = Polygon(points[hull.vertices], closed=True, fill=True, edgecolor='black', alpha=0.2)
        return polygon
    except Exception as e:
        print(f"Erreur lors du calcul du Convex Hull pour le cluster {cluster_label}: {e}")
        return None

def visualize_data_with_clusters(df, output_path, filename, eps=5, min_samples=1):
    """
    Visualise les données dans un graphique avec clustering et sauvegarde l'image.
    
    Args:
        df (DataFrame): DataFrame contenant les colonnes 'x', 'y', 'value'.
        output_path (str): Chemin du dossier où sauvegarder les graphiques.
        filename (str): Nom du fichier JSON original pour nommer le graphique.
        eps (float): Rayon maximum pour DBSCAN.
        min_samples (int): Nombre minimum de points pour DBSCAN.
    """
    # Séparer les points avec des valeurs > 0 et = 0
    df_positive = df[df['value'] > 0].copy()
    df_zero = df[df['value'] == 0].copy()
    
    # Appliquer le clustering sur les points avec des valeurs > 0
    df_positive = perform_clustering(df_positive, eps=eps, min_samples=min_samples)
    
    # Définir le colormap pour les valeurs
    cmap = plt.cm.viridis
    norm = Normalize(vmin=df_positive['value'].min() if not df_positive.empty else 0,
                    vmax=df_positive['value'].max() if not df_positive.empty else 1)
    
    # Créer le graphique
    plt.figure(figsize=(14, 12))
    
    # Tracer les points avec des valeurs > 0 en utilisant le colormap
    if not df_positive.empty:
        scatter_positive = plt.scatter(
            df_positive['x'], 
            df_positive['y'], 
            c=df_positive['value'], 
            cmap=cmap, 
            norm=norm,
            edgecolors='w', 
            s=150, 
            label='Points d\'Intérêt'
        )
    else:
        scatter_positive = None
    
    # Tracer les points avec des valeurs = 0 en gris
    plt.scatter(
        df_zero['x'], 
        df_zero['y'], 
        c='grey', 
        edgecolors='w', 
        s=100, 
        label='Aucune Ressource'
    )
    
    # Ajouter une barre de couleur (colorbar) pour la légende
    if scatter_positive:
        cbar = plt.colorbar(scatter_positive)
        cbar.set_label('Nombre de Ressources Trouvées', fontsize=14)
    
    # Tracer les polygones des clusters
    if not df_positive.empty:
        unique_clusters = df_positive['cluster'].unique()
        patches = []
        cluster_labels = []
        cluster_values = []
        
        for cluster in unique_clusters:
            if cluster == -1:
                continue  # Ignorer le bruit
            polygon = get_cluster_polygons(df_positive, cluster)
            if polygon:
                patches.append(polygon)
                total_resources = df_positive[df_positive['cluster'] == cluster]['value'].sum()
                cluster_labels.append(f'Cluster {cluster} (Total: {total_resources})')
                cluster_values.append(total_resources)
            else:
                # Si le Convex Hull n'est pas défini, tracer une ligne ou un point
                cluster_points = df_positive[df_positive['cluster'] == cluster][['x', 'y']].values
                if len(cluster_points) == 1:
                    # Tracer un point unique avec un marqueur spécial
                    plt.scatter(
                        cluster_points[0][0], 
                        cluster_points[0][1], 
                        color='black', 
                        edgecolors='w', 
                        s=200, 
                        marker='X', 
                        label=f'Cluster {cluster} (Single Point)'
                    )
                elif len(cluster_points) == 2:
                    # Tracer une ligne entre les deux points
                    plt.plot(
                        cluster_points[:,0], 
                        cluster_points[:,1], 
                        'k--', 
                        linewidth=2, 
                        label=f'Cluster {cluster} (Line)'
                    )
                # Vous pouvez ajouter plus de conditions pour gérer d'autres cas si nécessaire
        
        if patches:
            p = PatchCollection(patches, facecolor='none', edgecolor='black', linewidth=2, linestyle='--')
            plt.gca().add_collection(p)
        
        # Ajouter des annotations pour les points d'intérêt
        for _, row in df_positive.iterrows():
            plt.annotate(
                f'{row["value"]}', 
                (row['x'], row['y']),
                textcoords="offset points", 
                xytext=(0,10), 
                ha='center',
                fontsize=12,
                color='black',
                weight='bold'
            )
        
        # Ajouter des annotations pour les clusters
        for cluster in unique_clusters:
            if cluster == -1:
                continue  # Ignorer le bruit
            cluster_points = df_positive[df_positive['cluster'] == cluster]
            centroid_x = cluster_points['x'].mean()
            centroid_y = cluster_points['y'].mean()
            total_resources = cluster_points['value'].sum()
            
            # Vérifier si Convex Hull a été tracé
            polygon = get_cluster_polygons(df_positive, cluster)
            if polygon:
                plt.annotate(
                    f'Cluster {cluster}\nTotal: {total_resources}',
                    (centroid_x, centroid_y),
                    textcoords="offset points",
                    xytext=(0, -20),
                    ha='center',
                    fontsize=12,
                    color='black',
                    weight='bold',
                    bbox=dict(boxstyle="round,pad=0.3", fc="yellow", alpha=0.5)
                )
            else:
                # Si Convex Hull n'est pas défini, placer l'annotation près du point ou de la ligne
                if len(cluster_points) == 1:
                    plt.annotate(
                        f'Cluster {cluster}\nTotal: {total_resources}',
                        (centroid_x, centroid_y),
                        textcoords="offset points",
                        xytext=(0, -30),
                        ha='center',
                        fontsize=12,
                        color='black',
                        weight='bold',
                        bbox=dict(boxstyle="round,pad=0.3", fc="yellow", alpha=0.5)
                    )
                elif len(cluster_points) == 2:
                    plt.annotate(
                        f'Cluster {cluster}\nTotal: {total_resources}',
                        (centroid_x, centroid_y),
                        textcoords="offset points",
                        xytext=(0, -30),
                        ha='center',
                        fontsize=12,
                        color='black',
                        weight='bold',
                        bbox=dict(boxstyle="round,pad=0.3", fc="yellow", alpha=0.5)
                    )
    
    # Personnaliser le graphique
        plt.title(f"Carte des Endroits avec les Ressources Trouvées - {filename}", fontsize=20, fontweight='bold')
    else:
        plt.title(f"Carte des Endroits avec les Ressources Trouvées - {filename} (Aucune donnée positive)", fontsize=20, fontweight='bold')
    
    plt.xlabel("Coordonnée X", fontsize=16)
    plt.ylabel("Coordonnée Y (Négatif)", fontsize=16)
    plt.legend(loc='upper right', fontsize=14, markerscale=1.5, framealpha=0.7)
    plt.grid(True, linestyle='--', alpha=0.5)
    
    # Ajuster les limites des axes pour mieux encadrer les points
    plt.xlim(df['x'].min() - 5, df['x'].max() + 5)
    plt.ylim(df['y'].min() - 5, df['y'].max() + 5)
    
    # Sauvegarder le graphique
    save_path = os.path.join(output_path, f"{os.path.splitext(filename)[0]}.png")
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()
    print(f"Graphique sauvegardé: {save_path}")

def main():
    # Définir le répertoire contenant les fichiers JSON
    data_directory = "datas"
    
    # Vérifier si le répertoire existe
    if not os.path.isdir(data_directory):
        print(f"Le dossier '{data_directory}' n'existe pas.")
        return
    
    # Créer un répertoire de sortie pour les graphiques
    output_directory = "output_graphs"
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    
    # Parcourir tous les fichiers JSON dans le répertoire
    for filename in os.listdir(data_directory):
        if filename.endswith(".json"):
            file_path = os.path.join(data_directory, filename)
            print(f"Traitement du fichier: {file_path}")
            
            # Charger et convertir les données
            data = load_json_file(file_path)
            if not data:
                print(f"Aucune donnée valide trouvée dans {filename}.")
                continue
            
            # Convertir le dictionnaire en DataFrame avec les ordonnées négatives
            df = pd.DataFrame([
                {"x": coord[0], "y": -coord[1], "value": val}
                for coord, val in data.items()
            ])
            
            # Vérifier si le DataFrame est vide
            if df.empty:
                print(f"Aucune donnée à visualiser dans {filename}.")
                continue
            
            # Visualiser et sauvegarder le graphique avec clustering
            visualize_data_with_clusters(df, output_directory, filename, eps=5, min_samples=1)
    
    print("Tous les graphiques ont été générés et sauvegardés.")

if __name__ == "__main__":
    main()

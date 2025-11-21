import collections

class Grille:
    def __init__(self):
        self.cellules = set()
        self.generation = 0

    def ajouter_ou_supprimer(self, x, y):
        if (x, y) in self.cellules:
            self.cellules.remove((x, y))
        else:
            self.cellules.add((x, y))

    def evoluer(self):
        compteur_voisins = collections.defaultdict(int)
        self.generation +=1
        offsets = [(-1, -1), (0, -1), (1, -1),
                   (-1,  0),          (1,  0),
                   (-1,  1), (0,  1), (1,  1)]

        # --- PHASE A : RECENSEMENT ---
        for (x, y) in self.cellules:
            for dx, dy in offsets:
                # On remplit le dictionnaire
                compteur_voisins[(x + dx, y + dy)] += 1

        # --- PHASE B : SÉLECTION ---
        nouvelles_cellules = set()

        # On parcourt toutes les cases qui ont au moins 1 voisin
        for coord, nb_voisins in compteur_voisins.items():
            
            # Règle 1 : Naissance (Une case vide ou pleine avec 3 voisins vit)
            if nb_voisins == 3:
                nouvelles_cellules.add(coord)
            
            # Règle 2 : Survie (Une case DEJA vivante avec 2 voisins reste en vie)
            elif nb_voisins == 2 and coord in self.cellules:
                nouvelles_cellules.add(coord)
            
            # Toutes les autres (nb < 2 ou nb > 3) ne sont pas ajoutées
            # donc elles seront mortes dans la nouvelle grille.

        # On vérifie si le nouvel état est différent de l'ancien
        a_change = (nouvelles_cellules != self.cellules)
        
        self.cellules = nouvelles_cellules
        
        return a_change